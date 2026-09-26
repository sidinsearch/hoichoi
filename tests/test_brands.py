"""Brand engine tests — the holy trinity: positive, hard-block, unknown brand."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.backend.pipeline import brands as brand_mod
from app.backend.models.schemas import Scene, SceneContext


@pytest.fixture()
def brands_path(tmp_path: Path) -> Path:
    payload = [
        {
            "brand_id": "brand_a",
            "display_name": "Brand A",
            "category": "food",
            "target_contexts": ["cooking", "kitchen", "food"],
            "negative_contexts": ["funeral", "hospital", "violence"],
            "creatives": [
                {"id": "a_20s_bn", "duration_sec": 20, "language": "bn", "url": "ads/a.mp4"}
            ],
        },
        {
            "brand_id": "brand_b",
            "display_name": "Brand B",
            "category": "telecom",
            "target_contexts": ["phone", "calling", "internet", "wifi"],
            "negative_contexts": ["hospital", "funeral", "violence"],
            "creatives": [
                {"id": "b_20s_bn", "duration_sec": 20, "language": "bn", "url": "ads/b.mp4"}
            ],
        },
    ]
    p = tmp_path / "brands.json"
    p.write_text(json.dumps(payload))
    return p


def _scene(setting="family kitchen", activities=None, transcript="", tags=None):
    return Scene(
        scene_id="scene_x",
        start_sec=0.0,
        end_sec=10.0,
        shot_ids=[1, 2],
        transcript=transcript,
        context=SceneContext(
            setting=setting,
            activities=activities or ["cooking"],
            objects=["pan", "spices"],
            emotion="neutral",
            narrative_state="routine",
            context_tags=tags or ["cooking", "kitchen"],
        ),
        confidence=0.9,
    )


def test_positive_brand_selected_for_cooking(brands_path):
    brands = brand_mod.load_brands(brands_path)
    scene = _scene()
    decisions = brand_mod.rank_brands_for_scene(scene, brands)
    # Brand A (food) should be eligible and rank #1
    assert decisions[0].brand_id == "brand_a"
    assert decisions[0].eligible is True
    # Brand B (telecom) is also eligible (no negative match), but lower.
    b = next(d for d in decisions if d.brand_id == "brand_b")
    assert b.eligible is True
    assert b.semantic_score < decisions[0].semantic_score


def test_hard_negative_blocks(brands_path):
    brands = brand_mod.load_brands(brands_path)
    # Funeral transcript → both brands blocked (food: "funeral" negative, telecom: "funeral" negative)
    scene = _scene(transcript="the funeral was today at the crematorium শ্মশান", tags=["funeral"])
    decisions = brand_mod.rank_brands_for_scene(scene, brands)
    blocked = [d for d in decisions if not d.eligible]
    assert len(blocked) == len(brands), "All brands must be blocked by funeral context"
    for d in blocked:
        assert "funeral" in d.blocked_by


def test_hospital_blocks_telecom_but_might_keep_food(brands_path):
    brands = brand_mod.load_brands(brands_path)
    scene = _scene(transcript="went to the hospital for treatment", tags=["hospital"])
    decisions = brand_mod.rank_brands_for_scene(scene, brands)
    by_id = {d.brand_id: d for d in decisions}
    # Telecom brand also blocks hospital
    assert by_id["brand_b"].eligible is False
    assert "hospital" in by_id["brand_b"].blocked_by


def test_unknown_brand_ingestion_zero_code_change(tmp_path):
    payload = [
        {
            "brand_id": "brand_i",
            "display_name": "Brand I",
            "category": "pet care",
            "target_contexts": ["dog", "cat", "pet"],
            "negative_contexts": ["funeral", "hospital", "violence"],
            "creatives": [
                {"id": "i_15s_bn", "duration_sec": 15, "language": "bn", "url": "ads/i.mp4"}
            ],
        }
    ]
    p = tmp_path / "brands.json"
    p.write_text(json.dumps(payload))
    brands = brand_mod.load_brands(p)
    assert len(brands) == 1
    assert brands[0].brand_id == "brand_i"
    scene = _scene(transcript="the dog is playing", tags=["pet", "dog"])
    decisions = brand_mod.rank_brands_for_scene(scene, brands)
    assert decisions[0].brand_id == "brand_i"
    assert decisions[0].eligible is True
