"""Brand engine: dynamic loading, hard negative blocks, semantic ranking.

**Zero brand-specific Python.** Everything is data — adding Brand I works without code.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from ..models.schemas import (
    AcceptedBreak,
    Brand,
    BrandDecision,
    Candidate,
    CreativeSelection,
    Scene,
)
from ..services.embeddings import embed, similarity


_WORD_RE = re.compile(r"[\w\u0980-\u09FF]+", re.UNICODE)


def _normalize(text: str) -> str:
    return " ".join(w.lower() for w in _WORD_RE.findall(text or ""))


# Hard vocabulary used to detect negative context from transcript + scene tags.
# Each list maps a phrase to canonical negative tokens (which the PRD brands use).
_NEGATIVE_PHRASES = {
    # grief / death
    "শ্মশান": "funeral",
    "শাশান": "funeral",
    "death": "funeral",
    "died": "funeral",
    "মৃত": "funeral",
    "কবর": "funeral",
    # hospital
    "hospital": "hospital",
    "ডাক্তার": "hospital",
    "ডাক্তারখানা": "hospital",
    "চিকিৎসা": "hospital",
    "hospital-এ": "hospital",
    "icu": "hospital",
    "অসুস্থ": "illness",
    "hospital": "hospital",
    # accident / injury
    "accident": "accident",
    "দুর্ঘটনা": "accident",
    "আহত": "injury",
    "blood": "violence",
    "রক্ত": "violence",
    # violence
    "fight": "violence",
    "মারামারি": "violence",
    "ঝগড়া": "violence",
    "hitting": "violence",
    "gun": "violence",
    # financial distress
    "loan default": "financial distress",
    "bankrupt": "financial distress",
    "debt": "financial distress",
    # bathroom
    "bathroom": "bathroom",
    "toilet": "bathroom",
    "latrine": "bathroom",
    "শৌচালয়": "bathroom",
}


def detect_negative_tags(scene: Scene) -> List[str]:
    """Hard-block detector: returns all negative-context tokens present in this scene."""
    blob = _normalize((scene.transcript or "") + " " + " ".join(scene.context.context_tags))
    found = set()
    for phrase, canonical in _NEGATIVE_PHRASES.items():
        if _normalize(phrase) in blob:
            found.add(canonical)
    return sorted(found)


def _scene_text(scene: Scene) -> str:
    return " ".join(
        [
            scene.context.setting or "",
            " ".join(scene.context.activities),
            " ".join(scene.context.objects),
            " ".join(scene.context.context_tags),
            scene.transcript or "",
        ]
    )


def _brand_text(brand: Brand) -> str:
    return " ".join(brand.target_contexts)


def load_brands(path: Path) -> List[Brand]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    brands: List[Brand] = []
    for item in raw:
        brands.append(Brand(**item))
    return brands


def _choose_creative(brand: Brand, preferred: int = 20) -> CreativeSelection:
    """Choose an ad duration by preference, falling back to nearest available."""
    if not brand.creatives:
        return CreativeSelection(creative_id=f"{brand.brand_id}_default", language="bn", duration_sec=preferred)
    # Prefer 20s, else nearest
    pool = sorted(brand.creatives, key=lambda c: abs(c.duration_sec - preferred))
    chosen = pool[0]
    return CreativeSelection(
        creative_id=chosen.id,
        language=chosen.language,
        duration_sec=chosen.duration_sec,
    )


def rank_brands_for_scene(scene: Scene, brands: List[Brand]) -> List[BrandDecision]:
    """Return brand decisions, sorted by semantic score desc; ineligible brands have eligible=False."""
    scene_neg = set(detect_negative_tags(scene))
    if not brands:
        return []

    # Embed each brand's target context once
    brand_texts = [_brand_text(b) for b in brands]
    scene_vec = embed([_scene_text(scene)])  # (1, D)
    brand_vecs = embed(brand_texts)            # (N, D)
    sims = similarity(scene_vec, brand_vecs)[0]  # (N,)

    decisions: List[BrandDecision] = []
    for b, s in zip(brands, sims):
        blocked_by = sorted(set(b.negative_contexts or []) & scene_neg)
        eligible = len(blocked_by) == 0
        decisions.append(
            BrandDecision(
                brand_id=b.brand_id,
                display_name=b.display_name,
                category=b.category,
                semantic_score=float(s),
                eligible=eligible,
                blocked_by=blocked_by,
            )
        )
    # Only return eligible first — but we still surface ineligible for explainability
    decisions.sort(key=lambda d: (not d.eligible, -d.semantic_score))
    return decisions


def assign_brands(
    accepted_candidates: List[Candidate],
    scenes_by_id: Dict[str, Scene],
    brands: List[Brand],
) -> Tuple[Dict[str, Tuple[Brand, CreativeSelection, str]], Dict[str, List[str]]]:
    """For each accepted candidate, pick the top eligible brand (or no brand).

    Returns:
        assignments: candidate_id -> (Brand, Creative, scene_context_summary)
        blocked_log:  candidate_id -> blocked brand ids (for explainability)
    """
    assignments: Dict[str, Tuple[Brand, CreativeSelection, str]] = {}
    blocked_log: Dict[str, List[str]] = {}

    # Pre-compute per-scene brand ranking
    scene_ranking: Dict[str, List[BrandDecision]] = {}
    for sc in scenes_by_id.values():
        scene_ranking[sc.scene_id] = rank_brands_for_scene(sc, brands)
        blocked_log.setdefault(sc.scene_id, [])

    for c in accepted_candidates:
        if c.decision != "accepted_pre_brand":
            continue
        scene_id = c.scene_id
        if not scene_id or scene_id not in scenes_by_id:
            # Pause candidates can be inside a scene rather than at its end.
            # Attach them to the containing scene so they can still be brand-matched.
            containing = next(
                (sc for sc in scenes_by_id.values() if sc.start_sec <= c.timestamp_sec <= sc.end_sec),
                None,
            )
            if containing is None:
                continue
            scene_id = containing.scene_id
            c.scene_id = scene_id
        sc = scenes_by_id[scene_id]
        decisions = scene_ranking[scene_id]
        # Top eligible brand (if any)
        top = next((d for d in decisions if d.eligible), None)
        if not top:
            blocked_log[c.candidate_id] = [d.brand_id for d in decisions]
            continue
        # Look up Brand object
        brand = next(b for b in brands if b.brand_id == top.brand_id)
        creative = _choose_creative(brand)
        summary = (
            f"{sc.context.setting}; "
            f"{', '.join(sc.context.activities[:3]) or 'no clear activity'}; "
            f"matched {brand.display_name} ({brand.category})"
        )
        assignments[c.candidate_id] = (brand, creative, summary)
        blocked_log[c.candidate_id] = sorted(d.brand_id for d in decisions if not d.eligible)
    return assignments, blocked_log
