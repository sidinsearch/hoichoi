"""Local-only ASR helpers used by `FasterWhisperProvider`.

Keeps the local-only path (ffmpeg pre-decode cache, file-hash, silence-removal
filter) out of the provider interface — these are private impl details.
"""

from __future__ import annotations

import hashlib
import logging
import subprocess
from pathlib import Path

from ...config import PROJECT_ROOT

log = logging.getLogger(__name__)


def ensure_8k_audio(audio_path: Path) -> Path:
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
