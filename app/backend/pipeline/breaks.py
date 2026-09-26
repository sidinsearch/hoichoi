"""Break candidate engine.

Generates candidates around natural boundaries, applies deterministic hard rules,
scores survivors, and emits explainable records.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..config import CONFIG
from ..models.schemas import (
    AcceptedBreak,
    BreakSignals,
    BrandDecision,
    Candidate,
    HardConstraints,
    Scene,
)


# -------- Candidate generation --------

def generate_candidates(
    scenes: List[Scene],
    audio,
    asr_segments: List,
    shots: List,
) -> List[Candidate]:
    """Generate candidate timestamps. Never random."""

    candidates: List[Candidate] = []
    cidx = 0

    # (a) End-of-scene candidates — strongest natural break signal
    for sc in scenes:
        cidx += 1
        ts = sc.end_sec
        s_before = _silence_at(audio, ts)
        sentence_complete = _sentence_complete(asr_segments, ts)
        dialogue_active = _dialogue_active(asr_segments, ts)
        visuals = _visual_transition_at(shots, ts)
        candidates.append(
            _make_candidate(
                cidx, ts, sc,
                scene_boundary=True,
                sentence_complete=sentence_complete,
                dialogue_active=dialogue_active,
                silence=s_before,
                visual=visuals,
            )
        )

    # (b) Mid-shot long-silence candidates (>= 1.2s) inside non-dialogue windows
    for s in (audio.pause_segments or []):
        cidx += 1
        ts = s["start"] + 0.1
        candidates.append(
            _make_candidate(
                cidx, ts, None,
                scene_boundary=False,
                sentence_complete=True,
                dialogue_active=False,
                silence=s["duration"],
                visual=False,
            )
        )

    return candidates


def _make_candidate(
    idx, ts, scene,
    scene_boundary, sentence_complete, dialogue_active, silence, visual,
):
    sig = BreakSignals(
        scene_boundary=bool(scene_boundary),
        sentence_complete=bool(sentence_complete),
        dialogue_active=bool(dialogue_active),
        audio_silence_sec=float(silence or 0.0),
        visual_transition=bool(visual),
        emotional_intensity=0.4 if not scene else min(1.0, max(0.0, _scene_intensity(scene))),
        narrative_independence=0.6 if scene else 0.4,
    )
    return Candidate(
        candidate_id=f"candidate_{idx:03d}",
        timestamp_sec=float(ts),
        scene_id=scene.scene_id if scene else None,
        signals=sig,
        hard_constraints=HardConstraints(),
        score=0.0,
        decision="candidate",
    )


def _scene_intensity(scene: Scene) -> float:
    """Heuristic: emotionally loaded words -> high intensity."""
    pos = {"wedding", "celebration", "happy", "fun", "music"}
    neg = {"funeral", "death", "cry", "violence", "fight", "accident"}
    text = (scene.transcript or "").lower()
    p = sum(1 for w in pos if w in text)
    n = sum(1 for w in neg if w in text)
    base = (n - p) * 0.2
    return max(0.0, min(1.0, 0.4 + base))


def _silence_at(audio, ts: float) -> float:
    if not audio or not audio.pause_segments:
        return 0.0
    for p in audio.pause_segments:
        if p["start"] <= ts <= p["end"]:
            return float(p["duration"])
    return 0.0


def _sentence_complete(segments: List, ts: float) -> bool:
    """A timestamp is 'sentence_complete' if the last ASR segment that contains it is fully done."""
    for seg in segments:
        # ts is inside [start, end]
        if seg.start <= ts <= seg.end:
            return ts >= seg.end - 0.05
    # No active speech at ts -> vacuously complete
    return True


def _dialogue_active(segments: List, ts: float) -> bool:
    """Dialogue is active if a segment is currently being spoken at ts."""
    for seg in segments:
        # buffer around segment end (speaker may continue)
        if seg.start - 0.2 <= ts <= seg.end + 0.05:
            return True
    return False


def _visual_transition_at(shots: List, ts: float) -> bool:
    """Returns true if ts lies within 1s of a shot boundary."""
    for sh in shots or []:
        if abs(ts - sh.start) < 1.0 or abs(ts - sh.end) < 1.0:
            return True
    return False


# -------- Hard filters --------

def apply_hard_filters(
    candidates: List[Candidate], video_duration_sec: float
) -> List[Candidate]:
    """Apply mandatory constraints. The LLM never overrides these.

    Returns the same list with updated `hard_constraints`, `decision`, `rejected_reasons`.
    """
    cfg = CONFIG.pacing
    accepted: List[Candidate] = []
    last_accepted_ts: float | None = None
    last_hour = -1
    breaks_in_hour = 0
    cumulative_ad_sec = 0.0

    # Sort by timestamp so pacing is deterministic
    candidates = sorted(candidates, key=lambda c: c.timestamp_sec)

    for c in candidates:
        reasons: List[str] = []

        # Do not place an ad immediately at the opening frame. The first
        # meaningful break must have enough content before it.
        if last_accepted_ts is None and c.timestamp_sec < cfg.min_first_break_seconds:
            reasons.append("too_early_first_break")

        # Sentence safety
        if not c.signals.sentence_complete:
            reasons.append("sentence_incomplete")
        # Dialogue safety
        if c.signals.dialogue_active:
            reasons.append("dialogue_active")
        # Emotional safety: grief/funeral/violence → reject
        if c.signals.emotional_intensity >= 0.85:
            reasons.append("emotional_climax")

        c.hard_constraints.sentence_complete_ok = c.signals.sentence_complete
        c.hard_constraints.dialogue_ok = not c.signals.dialogue_active

        # Minimum gap
        gap_ok = True
        if last_accepted_ts is not None and (c.timestamp_sec - last_accepted_ts) < cfg.min_gap_seconds:
            gap_ok = False
            reasons.append("minimum_gap")
        c.hard_constraints.minimum_gap_ok = gap_ok

        # Max breaks / hour (sliding window of calendar hour)
        hour = int(c.timestamp_sec // 3600)
        if hour != last_hour:
            breaks_in_hour = 0
            last_hour = hour
        # If we've already accepted up to the limit in this hour, reject.
        hourly_ok = breaks_in_hour < cfg.max_breaks_per_hour
        if not hourly_ok:
            reasons.append("max_breaks_per_hour")
        c.hard_constraints.hourly_limit_ok = hourly_ok

        # Ad load ratio (uses the actually-selected creative duration from brands;
        # falls back to a 20s default so the very early candidate passes still hold).
        projected_sec = float(getattr(c, "_projected_ad_sec", 20.0))
        projected_ad_load_pct = (cumulative_ad_sec + projected_sec) / max(1.0, video_duration_sec) * 100.0
        # Below 5 min, ad-load ratio is noisy — skip the cap.
        ad_load_ok = (video_duration_sec < 300) or (projected_ad_load_pct <= cfg.max_ad_load_percent)
        if not ad_load_ok:
            reasons.append("max_ad_load")
        c.hard_constraints.ad_load_ok = ad_load_ok

        if reasons:
            c.decision = "rejected"
            c.rejected_reasons = reasons
        else:
            c.decision = "accepted_pre_brand"
            accepted.append(c)
            last_accepted_ts = c.timestamp_sec
            breaks_in_hour += 1
            cumulative_ad_sec += 20.0
    return candidates


# -------- Scoring --------

def score_candidates(candidates: List[Candidate]) -> List[Candidate]:
    """Assign a 0..1 score. Weights are tunable in one place."""
    for c in candidates:
        if c.decision == "rejected":
            c.score = 0.0
            continue
        s = c.signals
        # All signals normalized to ~[0,1]
        scene_completion = 1.0 if s.scene_boundary else 0.3
        sentence_completion = 1.0 if s.sentence_complete else 0.0
        dialogue_pause = min(1.0, s.audio_silence_sec / 1.5)
        audio_silence = min(1.0, s.audio_silence_sec / 2.0)
        visual_transition = 1.0 if s.visual_transition else 0.2
        visual_stability = 0.7  # stable by default (we don't drift frames in MVP)
        emotional_safety = 1.0 - s.emotional_intensity  # higher = safer
        narrative_independence = s.narrative_independence

        score = (
            0.20 * scene_completion
            + 0.20 * sentence_completion
            + 0.10 * dialogue_pause
            + 0.10 * audio_silence
            + 0.10 * visual_transition
            + 0.05 * visual_stability
            + 0.15 * emotional_safety
            + 0.10 * narrative_independence
        )
        c.score = round(max(0.0, min(1.0, score)), 4)
    return candidates


def select_final_breaks(
    candidates: List[Candidate],
    selected_brands: Dict[str, Tuple],  # candidate_id -> (Brand, creative, scene_context_summary)
) -> List[AcceptedBreak]:
    """Promote `accepted_pre_brand` candidates with brand decisions to FinalBreak objects."""
    out: List[AcceptedBreak] = []
    counter = 0
    for c in candidates:
        if c.decision != "accepted_pre_brand":
            continue
        if c.score < CONFIG.pacing.break_score_threshold:
            c.decision = "rejected"
            c.rejected_reasons.append("below_score_threshold")
            continue
        if c.candidate_id not in selected_brands:
            # No brand survived semantics (all blocked) — keep as safe-but-brand-less
            continue
        counter += 1
        brand, creative, context_summary = selected_brands[c.candidate_id]
        # brand here is the JSON-loaded `Brand` model; AcceptedBreak expects
        # the slimmer `BrandDecision` shape. Map explicitly so the contract
        # stays strict.
        decision = BrandDecision(
            brand_id=brand.brand_id,
            display_name=brand.display_name,
            category=brand.category,
            semantic_score=c.score,
            eligible=True,
            blocked_by=[],
        )
        out.append(
            AcceptedBreak(
                break_id=f"break_{counter:03d}",
                timestamp_sec=c.timestamp_sec,
                duration_sec=creative.duration_sec,
                brand=decision,
                creative=creative,
                score=c.score,
                scene_id=c.scene_id,
                reason=context_summary,
            )
        )
    return out
