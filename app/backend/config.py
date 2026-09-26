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
class ProviderConfig:
    """Provider selection + model names. Never stores API keys.

    Resolution order (per service):
      1. Explicit env (e.g. `ASR_PROVIDER=groq`).
      2. Auto-detect from credentials (`groq` > `gemini` > `faster_whisper`).
      3. `mock` — never makes a network call. Safe default for sandboxed runs.

    API keys are read directly via `os.getenv` by each provider at construction.
    They are NEVER stored on this dataclass and NEVER logged.
    """
    # Vision
    vision_provider: str = os.getenv("VISION_PROVIDER", "").strip().lower()
    vision_model: str = os.getenv("VISION_MODEL", "gemini-2.0-flash")
    # ASR
    asr_provider: str = os.getenv("ASR_PROVIDER", "").strip().lower()
    asr_fallback_provider: str = os.getenv("ASR_FALLBACK_PROVIDER", "mock").strip().lower()
    # Allow the local CPU ASR fallback even when no cloud credentials present.
    allow_local_asr: bool = _env_bool("ALLOW_LOCAL_ASR", False)
    # Hugging Face token (only for gated HF model downloads).
    hf_token: str = os.getenv("HF_TOKEN", "").strip()


@dataclass(frozen=True)
class ModelConfig:
    # ────── ASR (local fallback only) ──────
    whisper_model: str = os.getenv("WHISPER_MODEL", "tiny")
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "bn")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # ────── Keyframe budget ──────
    max_keyframes: int = _env_int("MAX_KEYFRAMES", 12)

    # ────── Embeddings (kept local — tiny CPU) ──────
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # ────── HF VLM (local fallback only) ──────
    hf_vlm: str = os.getenv("HF_MODEL_VLM", "")
    vision_enabled: bool = os.getenv("HF_MODEL_VLM", "").strip() != ""

    use_llm: bool = _env_bool("USE_LLM", False)
    llm_model: str = os.getenv("HF_MODEL_LLM", "google/flan-t5-small")


@dataclass(frozen=True)
class AppConfig:
    pacing: PacingConfig = field(default_factory=PacingConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    storage_dir: Path = STORAGE_DIR
    project_root: Path = PROJECT_ROOT


CONFIG = AppConfig()
