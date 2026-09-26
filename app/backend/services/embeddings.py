"""Sentence-transformers embedding wrapper. Cached singleton.

Used to score scene-vs-brand context similarity. Stays tiny: `all-MiniLM-L6-v2`
is 80MB, CPU-fast, and good enough for keyword-style brand matching.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

import numpy as np

from ..config import CONFIG


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(CONFIG.models.embedding_model)


def embed(texts: List[str]) -> np.ndarray:
    """Return normalized embeddings so cosine == dot product."""
    model = _get_model()
    vecs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    return vecs


def similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity (assumes inputs are L2-normalized)."""
    return a @ b.T
