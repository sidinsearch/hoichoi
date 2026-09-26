"""Semantic scene construction.

Inputs: shots, ASR segments, audio signals, keyframes with optional VLM observations.

Approach (LLM-free by default):
  1. Group consecutive shots that share a transcript window OR share visual tags.
  2. For each group, take the dominant activity + objects from VLM observations.
  3. If `USE_LLM=1`, ask a tiny flan-t5-small to summarize; otherwise we do lexical fusion.

This deliberately keeps the pipeline usable without a chat LLM — the docs forbid it.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

from ..models.schemas import (
    AudioSignals,
    ASRSegment,
    KeyFrame,
    Scene,
    SceneContext,
    Shot,
)
from ..services.vlm import describe_scene_window


def _transcript_for_range(
    segments: List[ASRSegment], start: float, end: float
) -> str:
    bits = [
        s.text for s in segments if (s.end > start and s.start < end) and s.text.strip()
    ]
    return " ".join(bits)


def _tag_overlap(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def build_scenes(
    job_dir: Path,
    shots: List[Shot],
    asr_segments: List[ASRSegment],
    audio: AudioSignals,
    keyframes: List[KeyFrame],
) -> List[Scene]:
    """Build a list of semantic scenes, then attach per-scene visual observations."""
    if not shots:
        # Fallback: one giant scene
        return [
            Scene(
                scene_id="scene_001",
                start_sec=0.0,
                end_sec=float(audio.timeline[-1]["timestamp"] + 1) if audio.timeline else 0.0,
                shot_ids=[],
                transcript=_transcript_for_range(asr_segments, 0.0, 1e9),
                context=SceneContext(),
                confidence=0.3,
            )
        ]

    # 0. Ask the active provider once per bounded window. The returned
    # observation is reused for every shot in that window.
    scene_windows: List[List[Path]] = _build_scene_windows(shots, keyframes)
    window_observations: Dict[str, dict] = {}
    transcript_blob = " ".join(s.text for s in asr_segments)[:1000]
    for window in scene_windows[:8]:
        observation = describe_scene_window(window, transcript_window=transcript_blob)
        for frame_path in window:
            window_observations[str(frame_path)] = observation
    (job_dir / "vision_windows.json").write_text(
        json.dumps({
            "window_count": min(len(scene_windows), 8),
            "windows": [
                {"frames": [str(p) for p in w], "observation": window_observations.get(str(w[0]), {})}
                for w in scene_windows[:8] if w
            ],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 1. Annotate shots using the cached bounded-window observation.
    obs_per_shot: Dict[int, SceneContext] = {}
    for i, sh in enumerate(shots):
        # Find nearest keyframe within +/-2s of shot midpoint
        mid = (sh.start + sh.end) / 2.0
        nearest = None
        nearest_dt = float("inf")
        for kf in keyframes:
            dt = abs(kf.timestamp - mid)
            if dt < nearest_dt:
                nearest_dt = dt
                nearest = kf
        if nearest and nearest_dt <= 5.0:
            d = window_observations.get(str(Path(nearest.path)), {
                "setting": "unknown",
                "activities": [],
                "objects": [],
                "emotion": "neutral",
                "context_tags": [],
            })
            ctx = SceneContext(
                setting=d.get("setting", "unknown"),
                activities=d.get("activities", []),
                objects=d.get("objects", []),
                emotion=d.get("emotion", "neutral"),
                narrative_state="routine",
                context_tags=d.get("context_tags", []),
            )
            # Also weave in transcript keywords as context tags (cheap lexical fusion)
            transcript = _transcript_for_range(asr_segments, sh.start, sh.end).lower()
            for tag in _cheap_tags_from_text(transcript):
                if tag not in ctx.context_tags:
                    ctx.context_tags.append(tag)
            obs_per_shot[sh.id] = ctx
        else:
            obs_per_shot[sh.id] = SceneContext()

    # 2. Greedily group shots with similar context (tag-overlap >= 0.15) into scenes
    grouped: List[List[int]] = []
    cur: List[int] = []
    prev_ctx: SceneContext | None = None
    for sh in shots:
        cur_ctx = obs_per_shot.get(sh.id, SceneContext())
        if not cur:
            cur = [sh.id]
            prev_ctx = cur_ctx
            continue
        sim = max(
            _tag_overlap(cur_ctx.context_tags, prev_ctx.context_tags or []),
            1.0 if cur_ctx.setting == prev_ctx.setting and cur_ctx.setting not in ("unknown", "") else 0.0,
        )
        if sim >= 0.15:
            cur.append(sh.id)
        else:
            grouped.append(cur)
            cur = [sh.id]
            prev_ctx = cur_ctx
    if cur:
        grouped.append(cur)

    # 3. Materialize Scene objects
    scenes: List[Scene] = []
    for idx, ids in enumerate(grouped, start=1):
        id_shots = [s for s in shots if s.id in ids]
        start = min(s.start for s in id_shots)
        end = max(s.end for s in id_shots)
        transcript = _transcript_for_range(asr_segments, start, end)
        tags_pool = []
        acts_pool = []
        objects_pool = []
        for sid in ids:
            ctx = obs_per_shot.get(sid)
            if not ctx:
                continue
            tags_pool.extend(ctx.context_tags)
            acts_pool.extend(ctx.activities)
            objects_pool.extend(ctx.objects)
        dominant_activities = [w for w, _ in Counter(acts_pool).most_common(3)]
        dominant_objects = [w for w, _ in Counter(objects_pool).most_common(5)]
        dominant_tags = [w for w, _ in Counter(tags_pool).most_common(8)]
        setting = obs_per_shot[ids[0]].setting if ids else "unknown"
        confidence = min(1.0, 0.4 + 0.1 * len(ids))
        scenes.append(
            Scene(
                scene_id=f"scene_{idx:03d}",
                start_sec=start,
                end_sec=end,
                shot_ids=ids,
                transcript=transcript,
                context=SceneContext(
                    setting=setting,
                    activities=dominant_activities,
                    objects=dominant_objects,
                    emotion=obs_per_shot[ids[0]].emotion if ids else "neutral",
                    narrative_state="routine",
                    context_tags=dominant_tags,
                ),
                confidence=confidence,
            )
        )
    return scenes


# --- light lexical helpers ----------------------------------------------------

_NEGATIVE_HINTS = {
    "funeral", "death", "died", "mar", "shmashan", "hospital", "accident",
    "violence", "fight", "weeping", "cry", "crying", "blood", "injury",
}

_POSITIVE_HINTS = {
    "kitchen", "cooking", "khichuri", "rice", "fish", "spices", "food",
    "phone", "call", "shopping", "shopping", "delivery", "package",
    "wedding", "celebration", "party", "salon", "makeup", "mirror",
    "car", "driving", "road", "travel", "hotel", "beach", "train",
}


def _cheap_tags_from_text(text: str) -> List[str]:
    """Return normalized BN↔EN tag hits for fast lexical fusion."""
    if not text:
        return []
    tags: List[str] = []
    for w in text.split():
        w = w.strip(".,!?\"'()").lower()
        if w in _POSITIVE_HINTS or w in _NEGATIVE_HINTS:
            tags.append(w)
    # de-dup but preserve order
    seen, out = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _build_scene_windows(
    shots: List[Shot],
    keyframes: List[KeyFrame],
    scenes_fallback=None,
) -> List[List[Path]]:
    """Pre-allocate up to 4 keyframe paths per scene window.

    The orchestrator passes these to `describe_scene_window(...)` so the cloud
    provider gets a *bounded* packet (≤4 frames + transcript slice), not the
    full video. Hard rules stay in Python; the cloud only summarizes context.
    """
    if not shots:
        return []
    windows: List[List[Path]] = []
    cur_frames: List[Path] = []
    cur_window_start = shots[0].start
    for sh in shots:
        mid_kf = None
        mid_dt = float("inf")
        for kf in keyframes:
            dt = abs(kf.timestamp - (sh.start + sh.end) / 2)
            if dt < mid_dt:
                mid_dt = dt
                mid_kf = kf
        if mid_kf is None:
            continue
        if (sh.start - cur_window_start) > 60 or len(cur_frames) >= 4:
            if cur_frames:
                windows.append(cur_frames)
            cur_frames = [Path(mid_kf.path)]
            cur_window_start = sh.start
        else:
            cur_frames.append(Path(mid_kf.path))
    if cur_frames:
        windows.append(cur_frames)
    return windows
