"""Semantic scene construction.

Inputs: shots, ASR segments, audio signals, keyframes with optional VLM observations.

Approach (LLM-free by default):
  1. Group consecutive shots that share a transcript window OR share visual tags.
  2. For each group, take the dominant activity + objects from VLM observations.
  3. If `USE_LLM=1`, ask a tiny flan-t5-small to summarize; otherwise we do lexical fusion.

This deliberately keeps the pipeline usable without a chat LLM — the docs forbid it.
"""

from __future__ import annotations

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
from ..services.vlm import describe_image


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

    # 1. Annotate shots with VLM-based observations (lazy — only keyframes near shot midpoint)
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
            try:
                d = describe_image(Path(nearest.path))
            except Exception:
                d = {
                    "setting": "unknown",
                    "activities": [],
                    "objects": [],
                    "emotion": "neutral",
                    "context_tags": [],
                }
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
