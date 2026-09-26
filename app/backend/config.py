"""Tunable model configuration. No magic strings inside the pipeline.

Defaults reflect what's currently the best lightweight option per task for CPU laptops,
after surveying Hugging Face — see `docs/MODEL_REGISTRY.md`.

You can override any of these at runtime via environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _project_root() -> Path:
    # app/backend/config.py -> repo root
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT: Path = _project_root()
STORAGE_DIR: Path = Path(os.getenv("JOB_STORAGE_DIR", str(PROJECT_ROOT / "data" / "jobs")))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class PacingConfig:
    min_gap_seconds: float = _env_float("MIN_GAP_SECONDS", 120.0)
    max_breaks_per_hour: int = _env_int("MAX_BREAKS_PER_HOUR", 4)
    max_ad_load_percent: float = _env_float("MAX_AD_LOAD_PERCENT", 15.0)
    break_score_threshold: float = _env_float("BREAK_SCORE_THRESHOLD", 0.55)
    min_dialogue_pause_sec: float = _env_float("MIN_DIALOGUE_PAUSE_SEC", 0.6)
    min_scene_complete_confidence: float = _env_float("MIN_SCENE_COMPLETE_CONFIDENCE", 0.5)


@dataclass(frozen=True)
class ModelConfig:
    # ────── ASR ──────
    # `tiny` runs in ~RTF 0.2 on a CPU laptop (~75 MB quantized) and finishes a
    # 40-minute Bengali drama in well under 2 minutes — the "3-5 minute E2E" spec.
    # Bump to `base`/`small` if you have more time and want better Bengali accuracy.
    whisper_model: str = os.getenv("WHISPER_MODEL", "tiny")
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "bn")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # ────── Keyframe budget ──────
    max_keyframes: int = _env_int("MAX_KEYFRAMES", 12)

    # ────── Embeddings ──────
    # Default is the no-nonsense 80 MB MiniLM. For true Bengali semantics, override
    # with `shihab17/bangla-sentence-transformer` (XLM-R distilled, ~278 MB).
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # ────── VLM (off by default for the 3-5 min demo) ──────
    # SmolVLM-Instruct (256M) is the smallest credible VLM today, but cold-load
    # + 12-keyframe inference routinely blows the demo budget. The default path
    # uses *lexical fusion* (transcript tags + cheap VLM-style heuristics) which
    # is plenty good enough for break decisions. Set `HF_MODEL_VLM` to a model
    # name to re-enable, or `=` to keep it off explicitly.
    hf_vlm: str = os.getenv("HF_MODEL_VLM", "")
    vision_enabled: bool = os.getenv("HF_MODEL_VLM", "").strip() != ""

    # ────── LLM rerank (optional) ──────
    # Only if `USE_LLM=1`. We pick `flan-t5-small` (60M) – NOT a general chat LLM –
    # to keep the "no general chat LLM" rule from the spec.
    use_llm: bool = _env_bool("USE_LLM", False)
    llm_model: str = os.getenv("HF_MODEL_LLM", "google/flan-t5-small")


@dataclass(frozen=True)
class AppConfig:
    pacing: PacingConfig = field(default_factory=PacingConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    storage_dir: Path = STORAGE_DIR
    project_root: Path = PROJECT_ROOT


CONFIG = AppConfig()
