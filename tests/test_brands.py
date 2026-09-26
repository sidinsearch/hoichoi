"""Brand engine tests — positive, hard-block, unknown, and pause-scene assignment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.backend.pipeline import brands as brand_mod
from app.backend.pipeline.breaks import select_final_breaks
from app.backend.models.schemas import Candidate, Scene, SceneContext


@pytest.fixture()
def brands_path(tmp_path: Path) -> Path:
    payload = [
        {
            "brand_id": "brand_a", "display_name": "Brand A", "category": "food",
            "target_contexts": ["cooking", "kitchen", "food"],
            "negative_contexts": ["funeral", "hospital", "violence"],
            "creatives": [{"id": "a_20s_bn", "duration_sec": 20, "language": "bn", "url": "ads/a.mp4"}],
        },
        {
            "brand_id": "brand_b", "display_name": "Brand B", "category": "telecom",
            "target_contexts": ["phone", "calling", "internet", "wifi"],
            "negative_contexts": ["hospital", "funeral", "violence"],
            "creatives": [{"id": "b_20s_bn", "duration_sec": 20, "language": "bn", "url": "ads/b.mp4"}],
        },
    ]
    p = tmp_path / "brands.json"
    p.write_text(json.dumps(payload))
    return p


def _scene(setting="family kitchen", activities=None, transcript="", tags=None, start=0.0, end=10.0):
    return Scene(
        scene_id="scene_x", start_sec=start, end_sec=end, shot_ids=[1, 2], transcript=transcript,
        context=SceneContext(setting=setting, activities=activities or ["cooking"], objects=["pan", "spices"],
                             emotion="neutral", narrative_state="routine", context_tags=tags or ["cooking", "kitchen"]),
        confidence=0.9,
    )


def test_positive_brand_selected_for_cooking(brands_path):
    brands = brand_mod.load_brands(brands_path)
    decisions = brand_mod.rank_brands_for_scene(_scene(), brands)
    assert decisions[0].brand_id == "brand_a"
    assert decisions[0].eligible is True
    b = next(d for d in decisions if d.brand_id == "brand_b")
    assert b.eligible is True
    assert b.semantic_score < decisions[0].semantic_score


def test_hard_negative_blocks(brands_path):
    brands = brand_mod.load_brands(brands_path)
    decisions = brand_mod.rank_brands_for_scene(_scene(transcript="the funeral was today at the crematorium শ্মশান", tags=["funeral"]), brands)
    blocked = [d for d in decisions if not d.eligible]
    assert len(blocked) == len(brands)
    for d in blocked:
        assert "funeral" in d.blocked_by


def test_hospital_blocks_telecom_but_might_keep_food(brands_path):
    brands = brand_mod.load_brands(brands_path)
    decisions = brand_mod.rank_brands_for_scene(_scene(transcript="went to the hospital for treatment", tags=["hospital"]), brands)
    by_id = {d.brand_id: d for d in decisions}
    assert by_id["brand_b"].eligible is False
    assert "hospital" in by_id["brand_b"].blocked_by


def test_unknown_brand_ingestion_zero_code_change(tmp_path):
    p = tmp_path / "brands.json"
    p.write_text(json.dumps([{"brand_id": "brand_i", "display_name": "Brand I", "category": "pet care", "target_contexts": ["dog", "cat", "pet"], "negative_contexts": ["funeral", "hospital", "violence"], "creatives": [{"id": "i_15s_bn", "duration_sec": 15, "language": "bn", "url": "ads/i.mp4"}]}]))
    brands = brand_mod.load_brands(p)
    assert len(brands) == 1 and brands[0].brand_id == "brand_i"
    assert brand_mod.rank_brands_for_scene(_scene(transcript="the dog is playing", tags=["pet", "dog"]), brands)[0].brand_id == "brand_i"


def test_pause_candidate_is_attached_to_containing_scene(brands_path):
    """A safe mid-scene pause must remain brand-matchable instead of disappearing."""
    scenes = {"scene_x": _scene(start=0.0, end=30.0)}
    candidate = Candidate(candidate_id="c1", timestamp_sec=12.0, scene_id=None, score=0.9,
                          decision="accepted_pre_brand")
    assignments, _ = brand_mod.assign_brands([candidate], scenes, brand_mod.load_brands(brands_path))
    assert candidate.scene_id == "scene_x"
    assert "c1" in assignments
    assert len(select_final_breaks([candidate], assignments)) == 1
