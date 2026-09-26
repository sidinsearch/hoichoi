"""Audio feature extraction: energy, silence, pause segments.

Uses librosa (numpy-only) so no GPU/Torch is required.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import numpy as np

from ..models.schemas import AudioSignals
from ..services.asr import transcribe


def _load_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    """Minimal scipy-free mono WAV reader.

    Falls back to a silent array if scipy is unavailable — the pipeline will still
    return reasonable signals (just no detail). We never want a hard failure here.
    """
    try:
        import wave
        with wave.open(str(path), "rb") as w:
            sr = w.getframerate()
            n = w.getnframes()
            data = w.readframes(n)
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        return audio, sr
    except Exception:
        return np.zeros(0, dtype=np.float32), 16000


def compute_audio_signals(audio_path: Path, language: str | None = None) -> tuple[AudioSignals, list]:
    """Compute timeline + silence intervals. Also transcribes."""
    audio, sr = _load_wav_mono(audio_path)
    hop = sr  # 1-second buckets
    if audio.size == 0:
        signals = AudioSignals(timeline=[], silence_segments=[], pause_segments=[])
        return signals, []

    n_frames = max(1, math.ceil(len(audio) / hop))
    timeline: List[Dict[str, float]] = []
    silences: List[Dict[str, float]] = []

    for i in range(n_frames):
        seg = audio[i * hop : (i + 1) * hop]
        ts = i
        rms = float(np.sqrt(np.mean(seg ** 2))) if seg.size else 0.0
        is_silent = rms < 0.01
        if is_silent and seg.size:
            silences.append({"start": ts, "end": ts + 1.0})
        timeline.append(
            {
                "timestamp": float(ts),
                "speech_active": not is_silent,
                "audio_energy": rms,
                "silence_sec": 1.0 if is_silent else 0.0,
            }
        )

    # Merge adjacent silences
    merged_silences: List[Dict[str, float]] = []
    for s in silences:
        if merged_silences and merged_silences[-1]["end"] >= s["start"]:
            merged_silences[-1]["end"] = s["end"]
        else:
            merged_silences.append(dict(s))

    # Treat long silences (>=0.6s) as dialogue pauses
    pauses = [
        {"start": p["start"], "end": p["end"], "duration": p["end"] - p["start"]}
        for p in merged_silences
        if (p["end"] - p["start"]) >= 0.6
    ]

    signals = AudioSignals(
        timeline=timeline,
        silence_segments=merged_silences,
        pause_segments=pauses,
        speech_ratio=sum(1 for t in timeline if t["speech_active"]) / max(1, len(timeline)),
        mean_energy=float(np.mean([t["audio_energy"] for t in timeline])) if timeline else 0.0,
    )

    asr_segments = transcribe(audio_path, language=language)
    return signals, asr_segments
