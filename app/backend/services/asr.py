"""ASR via faster-whisper. Bengali-capable, runs on CPU.

`faster-whisper` is a CTranslate2 port — orders of magnitude faster than openai-whisper
on the same hardware. int8 quantization fits the `tiny` model in ~75 MB.

Speed strategy for the **10-min / 40-min video** budget:
  1. Downsample extracted wav to **8 kHz mono** (~2× decode speedup).
  2. `silenceremove` filter pre-trims silence (VAD pre-step).
  3. `beam_size=1` greedy decode.
  4. `chunk_length=15` keeps CPU warm.
  5. `language="bn"` skips auto-detection overhead.

For English-only, set `ASR_BACKEND=distil` to use `distil-whisper` via CTranslate2
(5-6× faster than tiny). Bengali **must** stay on faster-whisper.
"""

from __future__ import annotations

import hashlib
import logging
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from ..models.schemas import ASRSegment
from ..config import CONFIG, PROJECT_ROOT

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_faster_model():
    from faster_whisper import WhisperModel  # local import keeps startup fast
    m = CONFIG.models
    return WhisperModel(
        m.whisper_model,
        device=m.whisper_device,
        compute_type=m.whisper_compute_type,
    )


def _ensure_8k_audio(audio_path: Path) -> Path:
    """Downsample to 8 kHz mono + silence-trim. Cached to avoid recomputing."""
    cache_root = PROJECT_ROOT / "data" / ".asr_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    sig = hashlib.md5(
        f"{audio_path.stat().st_mtime_ns}-{audio_path.stat().st_size}".encode()
    ).hexdigest()[:12]
    out = cache_root / f"{audio_path.stem}.{sig}.8k.wav"
    if out.exists() and out.stat().st_size > 0:
        return out
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(audio_path),
        "-ac", "1", "-ar", "8000",
        "-af", "silenceremove=stop_periods=-1:stop_duration=0.4:stop_threshold=-38dB",
        str(out),
    ]
    try:
        subprocess.check_call(cmd, timeout=300)
        if out.exists() and out.stat().st_size > 0:
            return out
    except Exception as exc:
        log.warning("ASR cache preprocess failed: %s; falling back to original", exc)
    return audio_path


def transcribe(audio_path: Path, language: Optional[str] = None) -> List[ASRSegment]:
    """Transcribe and return time-stamped segments."""
    if language is None:
        language = CONFIG.models.whisper_language

    backend = os.getenv("ASR_BACKEND", "faster_whisper").strip().lower()
    if backend == "distil":
        # English only — fall back to faster_whisper if a non-English code is requested.
        if language and language not in ("en", "english"):
            log.info("distil-whisper is English-only; falling back to faster_whisper for %s", language)
        else:
            return _transcribe_distil(audio_path)

    model = _get_faster_model()
    audio_for_asr = _ensure_8k_audio(audio_path)
    log.info("ASR (faster-whisper %s) decoding: %s", CONFIG.models.whisper_model, audio_for_asr.name)
    segments_iter, _info = model.transcribe(
        str(audio_for_asr),
        language=language,
        beam_size=1,                   # greedy — fastest
        best_of=1,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 400,
            "speech_pad_ms": 200,
        },
        condition_on_previous_text=False,
        word_timestamps=False,
        chunk_length=15,
    )
    out: List[ASRSegment] = []
    for seg in segments_iter:
        out.append(
            ASRSegment(
                start=float(seg.start or 0.0),
                end=float(seg.end or 0.0),
                text=(seg.text or "").strip(),
                confidence=getattr(seg, "avg_logprob", None),
            )
        )
    return out


@lru_cache(maxsize=1)
def _get_distil_model():
    """Distil-Whisper via CTranslate2 (English only). ~5-6× faster than tiny."""
    from faster_whisper import WhisperModel
    return WhisperModel(
        "Systran/faster-distil-whisper-large-v3",
        device=CONFIG.models.whisper_device,
        compute_type=CONFIG.models.whisper_compute_type,
    )


def _transcribe_distil(audio_path: Path) -> List[ASRSegment]:
    model = _get_distil_model()
    audio_for_asr = _ensure_8k_audio(audio_path)
    segs_iter, _ = model.transcribe(
        str(audio_for_asr),
        language="en",
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
        chunk_length=15,
    )
    out: List[ASRSegment] = []
    for seg in segs_iter:
        out.append(
            ASRSegment(
                start=float(seg.start or 0.0),
                end=float(seg.end or 0.0),
                text=(seg.text or "").strip(),
                confidence=getattr(seg, "avg_logprob", None),
            )
        )
    return out
