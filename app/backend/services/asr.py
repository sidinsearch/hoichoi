"""ASR via faster-whisper. Bengali-capable, runs on CPU.

`faster-whisper` is a CTranslate2 port: orders of magnitude faster than openai/whisper
on the same hardware, and `int8` quantization fits the `base` model in well under 1GB.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from ..models.schemas import ASRSegment
from ..config import CONFIG


@lru_cache(maxsize=1)
def _get_model():
    from faster_whisper import WhisperModel  # local import keeps startup fast

    m = CONFIG.models
    return WhisperModel(
        m.whisper_model,
        device=m.whisper_device,
        compute_type=m.whisper_compute_type,
    )


def transcribe(audio_path: Path, language: str | None = None) -> List[ASRSegment]:
    """Transcribe a 16k mono wav. Returns time-stamped segments.

    `condition_on_previous_text=False` keeps segments independent so no manual fixes
    bleed across cuts.
    """
    model = _get_model()
    if language is None:
        language = CONFIG.models.whisper_language
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=3,  # smaller beam → faster
        vad_filter=True,
        condition_on_previous_text=False,
        word_timestamps=False,
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
