"""Break engine tests: hard rules + scoring + threshold."""

from __future__ import annotations

from app.backend.models.schemas import (
    BreakSignals,
    Candidate,
    HardConstraints,
)
from app.backend.pipeline import breaks as break_mod


def _c(idx, ts, scene_boundary=False, sentence=True, dialogue=False,
       silence=0.0, visual=False, intensity=0.3):
    return Candidate(
        candidate_id=f"candidate_{idx:03d}",
        timestamp_sec=ts,
        scene_id="scene_x" if scene_boundary else None,
        signals=BreakSignals(
            scene_boundary=scene_boundary,
            sentence_complete=sentence,
            dialogue_active=dialogue,
            audio_silence_sec=silence,
            visual_transition=visual,
            emotional_intensity=intensity,
        ),
        hard_constraints=HardConstraints(),
    )


def test_rejects_mid_sentence_and_dialogue():
    c = _c(1, 10.0, sentence=False, dialogue=True)
    cands = break_mod.apply_hard_filters([c], video_duration_sec=600.0)
    assert cands[0].decision == "rejected"
    assert "sentence_incomplete" in cands[0].rejected_reasons
    assert "dialogue_active" in cands[0].rejected_reasons


def test_first_break_is_not_at_opening_frame():
    c = _c(1, 10.0, scene_boundary=True, sentence=True, silence=1.5)
    cands = break_mod.apply_hard_filters([c], video_duration_sec=600.0)
    assert "too_early_first_break" in cands[0].rejected_reasons


def test_minimum_gap_rejected():
    c1 = _c(1, 100.0, scene_boundary=True, sentence=True, silence=1.5)
    c2 = _c(2, 130.0, scene_boundary=True, sentence=True, silence=1.5)  # 30s after
    cands = break_mod.apply_hard_filters([c1, c2], video_duration_sec=600.0)
    accepted = [c for c in cands if c.decision == "accepted_pre_brand"]
    rejected = [c for c in cands if c.decision == "rejected"]
    assert len(accepted) == 1
    assert accepted[0].timestamp_sec == 100.0
    # The second one rejected for minimum_gap (default 120s)
    gap_reasons = [r for c in rejected for r in c.rejected_reasons]
    assert "minimum_gap" in gap_reasons


def test_max_breaks_per_hour_caps():
    cands_list = []
    # 5 breaks inside an hour, all hard-safe
    for i, ts in enumerate([100, 220, 340, 460, 580], start=1):
        cands_list.append(_c(i, ts, scene_boundary=True, sentence=True, silence=1.5))
    cands = break_mod.apply_hard_filters(cands_list, video_duration_sec=600.0)
    accepted = [c for c in cands if c.decision == "accepted_pre_brand"]
    assert len(accepted) <= break_mod.CONFIG.pacing.max_breaks_per_hour


def test_emotional_climax_rejects():
    c = _c(1, 10.0, scene_boundary=True, sentence=True, silence=1.5, intensity=0.95)
    cands = break_mod.apply_hard_filters([c], video_duration_sec=600.0)
    assert cands[0].decision == "rejected"
    assert "emotional_climax" in cands[0].rejected_reasons


def test_scoring_is_bounded_0_to_1():
    c = _c(1, 100.0, scene_boundary=True, sentence=True, silence=2.0, visual=True, intensity=0.2)
    c.decision = "accepted_pre_brand"
    [scored] = break_mod.score_candidates([c])
    assert 0.0 <= scored.score <= 1.0
