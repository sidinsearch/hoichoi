"""Output generation — scenes.json, debug.json, vmap.xml, playback.json.

The VMAP generator is isolated so the XML shape can be swapped without touching
the rest of the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring

from ..models.schemas import (
    AcceptedBreak,
    Candidate,
    DebugDoc,
    PlaybackBreak,
    PlaybackDoc,
    Scene,
    ScenesDoc,
)


def write_scenes(job_dir: Path, scenes: List[Scene], video_meta: Dict) -> Path:
    doc = ScenesDoc(video=video_meta, scenes=scenes)
    out = job_dir / "scenes.json"
    out.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    return out


def write_debug(
    job_dir: Path,
    candidates: List[Candidate],
    accepted: List[AcceptedBreak],
    video_meta: Dict,
) -> Path:
    scene_count = len({c.scene_id for c in candidates if c.scene_id})
    doc = DebugDoc(
        video=video_meta,
        candidates=candidates,
        accepted_breaks=accepted,
        summary={
            "scene_count": scene_count,
            "candidate_count": len(candidates),
            "accepted_count": len(accepted),
            "rejected_count": sum(1 for c in candidates if c.decision == "rejected"),
        },
    )
    out = job_dir / "debug.json"
    out.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    return out


def write_playback(job_dir: Path, video_url: str, accepted: List[AcceptedBreak]) -> Path:
    breaks = [
        PlaybackBreak(
            id=b.break_id,
            timestamp_sec=b.timestamp_sec,
            duration_sec=b.duration_sec,
            brand_id=b.brand.brand_id,
            display_name=b.brand.display_name,
            category=b.brand.category,
            context_summary=b.reason,
        )
        for b in accepted
    ]
    doc = PlaybackDoc(video_url=video_url, breaks=breaks)
    out = job_dir / "playback.json"
    out.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    return out


def write_vmap(job_dir: Path, accepted: List[AcceptedBreak], duration_sec: float) -> Path:
    """VMAP 1.0 — well-formed, advertises accepted breaks as `vmap:AdBreak` elements.

    We intentionally keep this isolated: a real VAST/VMAP library would replace it,
    but the demo doesn't need one.
    """
    vmap = Element("vmap:VMAP")
    vmap.set("xmlns:vmap", "http://www.iab.net/videosuite/vmap")
    vmap.set("xmlns:cv", "http://www.iab.net/videosuite/vmap-1.0")
    vmap.set("version", "1.0")

    ads = SubElement(vmap, "vmap:AdSources")
    ad_source = SubElement(ads, "vmap:AdSource")
    ad_source.set("id", "synthetic-source")
    ad_tag_uri = SubElement(ad_source, "vmap:AdTagURI")
    ad_tag_uri.text = "uri=synthetic://hoichoi/black-card"

    extensions = SubElement(ad_source, "vmap:Extensions")
    ext = SubElement(extensions, "cv:Extension", {"type": "synthetic_brands"})

    for b in accepted:
        adbreak = SubElement(
            vmap,
            "vmap:AdBreak",
            {
                "id": b.break_id,
                "timeOffset": f"{b.timestamp_sec:.3f}",
                "breakType": "linear",
                "breakFormat": "synthetic",
            },
        )
        # Synthetic creative metadata inside the AdBreak — kept portable.
        meta = SubElement(adbreak, "vmap:Extensions")
        ex = SubElement(meta, "cv:Extension", {"type": "synthetic_creative"})
        brand_el = SubElement(ex, "Brand")
        brand_el.text = b.brand.display_name
        cat_el = SubElement(ex, "Category")
        cat_el.text = b.brand.category
        dur_el = SubElement(ex, "DurationSec")
        dur_el.text = str(b.duration_sec)
        reason_el = SubElement(ex, "Reason")
        reason_el.text = b.reason

    xml_bytes = tostring(vmap, encoding="utf-8", xml_declaration=True)
    out = job_dir / "vmap.xml"
    out.write_bytes(xml_bytes)
    return out
