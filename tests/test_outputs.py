"""VMAP output is well-formed XML."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from app.backend.models.schemas import AcceptedBreak, BrandDecision, CreativeSelection
from app.backend.pipeline import outputs as out_mod


def test_vmap_well_formed(tmp_path: Path):
    b = AcceptedBreak(
        break_id="break_001",
        timestamp_sec=842.4,
        duration_sec=20,
        brand=BrandDecision(
            brand_id="brand_a", display_name="Brand A",
            category="food", semantic_score=0.9, eligible=True, blocked_by=[]
        ),
        creative=CreativeSelection(creative_id="a_20s_bn", language="bn", duration_sec=20),
        score=0.9,
        scene_id="scene_007",
        reason="Family cooking",
    )
    p = out_mod.write_vmap(tmp_path, [b], duration_sec=1684.2)
    text = p.read_bytes()
    assert b"<vmap:VMAP" in text
    tree = ET.fromstring(text)
    assert tree.tag.endswith("VMAP")
    found = [el for el in tree.iter() if el.attrib.get("id") == "break_001"]
    assert found, "AdBreak element with id=break_001 must be present"
