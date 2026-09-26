"""Analysis orchestrator — runs the pipeline stages in order, persists all artifacts.

Single-process; no Celery/Redis. Status is tracked in-memory and flushed to JSON.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..config import CONFIG
from ..models.schemas import AcceptedBreak, Candidate, Scene
from ..pipeline import audio as audio_mod
from ..pipeline import brands as brand_mod
from ..pipeline import breaks as break_mod
from ..pipeline import outputs as out_mod
from ..pipeline import scenes as scene_mod
from ..pipeline import shots as shot_mod
from ..pipeline import vision as vision_mod
from ..services.ffmpeg import extract_audio, probe_metadata

log = logging.getLogger(__name__)

STAGE_ORDER = [
    "uploading",
    "extracting_audio",
    "transcribing_bengali",
    "detecting_shots",
    "analyzing_visual_context",
    "building_scenes",
    "finding_break_candidates",
    "applying_safety_rules",
    "matching_brands",
    "generating_outputs",
    "ready",
]


@dataclass
class JobStatus:
    job_id: str
    status: str = "queued"
    stage: str = "queued"
    progress: float = 0.0
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    error: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=dict)


def new_job_id() -> str:
    return f"job_{int(time.time()*1000)}"


def create_job(video_path: Path, brand_path: Path, job_dir: Path) -> JobStatus:
    job_dir.mkdir(parents=True, exist_ok=True)
    # Move uploaded artifacts into the job dir to keep self-contained
    stored_video = job_dir / video_path.name
    stored_brand = job_dir / "brands.json"
    if video_path.resolve() != stored_video.resolve():
        stored_video.write_bytes(video_path.read_bytes())
    stored_brand.write_bytes(brand_path.read_bytes())

    status = JobStatus(
        job_id=job_dir.name,
        status="processing",
        stage=STAGE_ORDER[0],
    )
    (job_dir / "status.json").write_text(json.dumps(status.__dict__, default=str), encoding="utf-8")
    return status, stored_video, stored_brand


def run_job(job_id: str, video_path: Path, brand_path: Path, job_dir: Path,
            status: JobStatus) -> None:
    """Run the full pipeline. Updates status.json as it goes."""
    def update(progress: float, stage: str, **extras) -> None:
        status.progress = progress
        status.stage = stage
        for k, v in extras.items():
            setattr(status, k, v)
        (job_dir / "status.json").write_text(
            json.dumps(status.__dict__, default=str), encoding="utf-8"
        )

    try:
        update(5.0, "uploading")
        log.info("Probing %s", video_path)
        meta = probe_metadata(video_path)
        duration = float(meta.get("duration_sec") or 0.0)
        video_meta = {"filename": video_path.name, "duration_sec": duration}

        # Stage: extracting audio
        audio_path = job_dir / "audio.wav"
        update(15.0, "extracting_audio")
        extract_audio(video_path, audio_path)

        # Stage: transcribing Bengali
        update(30.0, "transcribing_bengali")
        audio_signals, asr_segments = audio_mod.compute_audio_signals(audio_path)
        (job_dir / "transcript.json").write_text(
            json.dumps([s.model_dump() for s in asr_segments], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Stage: detecting shots
        update(45.0, "detecting_shots")
        shots = shot_mod.detect_shots(video_path)

        # Stage: analyzing visual context (extracts keyframes + runs VLM)
        update(55.0, "analyzing_visual_context")
        frames_dir = job_dir / "frames"
        keyframes = vision_mod.extract_keyframes_for(video_path, shots, frames_dir)

        # Stage: building scenes (multimodal fusion happens inside)
        update(70.0, "building_scenes")
        scenes: List[Scene] = scene_mod.build_scenes(
            job_dir,
            shots,
            asr_segments,
            audio_signals,
            keyframes,
        )
        out_mod.write_scenes(job_dir, scenes, video_meta)

        # Stage: finding break candidates
        update(80.0, "finding_break_candidates")
        candidates: List[Candidate] = break_mod.generate_candidates(
            scenes, audio_signals, asr_segments, shots
        )

        # Stage: applying safety rules
        update(85.0, "applying_safety_rules")
        candidates = break_mod.apply_hard_filters(candidates, duration)
        candidates = break_mod.score_candidates(candidates)

        # Stage: matching brands
        update(92.0, "matching_brands")
        brands = brand_mod.load_brands(brand_path)
        scenes_by_id: Dict[str, Scene] = {s.scene_id: s for s in scenes}
        # attach blocked brands list to candidates for the debug file
        scene_blocked_lookup = {}
        for sc in scenes:
            scene_blocked_lookup[sc.scene_id] = sorted(
                brand_mod.detect_negative_tags(sc)
            )
        assignments, blocked_log = brand_mod.assign_brands(
            [c for c in candidates if c.decision == "accepted_pre_brand"],
            scenes_by_id,
            brands,
        )
        for c in candidates:
            if c.candidate_id in blocked_log:
                c.blocked_brands = blocked_log[c.candidate_id]
        accepted_breaks: List[AcceptedBreak] = break_mod.select_final_breaks(
            candidates, assignments
        )

        # Stage: generating outputs
        update(96.0, "generating_outputs")
        out_mod.write_debug(job_dir, candidates, accepted_breaks, video_meta)
        video_url = f"/api/jobs/{job_id}/video"
        out_mod.write_playback(job_dir, video_url, accepted_breaks)
        out_mod.write_vmap(job_dir, accepted_breaks, duration)

        # Artifact paths
        status.artifacts = {
            "scenes": f"/api/jobs/{job_id}/scenes",
            "debug": f"/api/jobs/{job_id}/debug",
            "vmap": f"/api/jobs/{job_id}/vmap",
            "playback": f"/api/jobs/{job_id}/playback",
            "transcript": f"/api/jobs/{job_id}/transcript",
        }
        status.summary = {
            "scenes": len(scenes),
            "candidates": len(candidates),
            "accepted": len(accepted_breaks),
            "rejected": sum(1 for c in candidates if c.decision == "rejected"),
        }
        status.status = "completed"
        status.finished_at = time.time()
        status.progress = 100.0
        status.stage = "ready"
        (job_dir / "status.json").write_text(
            json.dumps(status.__dict__, default=str), encoding="utf-8"
        )
    except Exception as e:
        log.exception("Job %s failed", job_id)
        status.status = "failed"
        status.error = f"{type(e).__name__}: {e}"
        status.finished_at = time.time()
        status.stage = "failed"
        (job_dir / "status.json").write_text(
            json.dumps(status.__dict__, default=str), encoding="utf-8"
        )


def launch_in_background(job_id: str, video: Path, brand: Path, job_dir: Path,
                         status: JobStatus) -> threading.Thread:
    """Spawn the orchestrator in a daemon thread."""
    t = threading.Thread(
        target=run_job,
        args=(job_id, video, brand, job_dir, status),
        daemon=True,
        name=f"orchestrator-{job_id}",
    )
    t.start()
    return t
