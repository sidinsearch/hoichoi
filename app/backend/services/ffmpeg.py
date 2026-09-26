"""FFmpeg wrapper — metadata, audio extraction, keyframe sampling.

All subprocess calls are isolated here so the pipeline never spawns `ffmpeg` directly.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def probe_metadata(video_path: Path) -> dict:
    """Return a flat dict of ffprobe metadata for the first video+audio stream."""
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path),
    ]
    out = subprocess.check_output(cmd, timeout=60).decode("utf-8", errors="ignore")
    data = json.loads(out)

    fmt = data.get("format", {}) or {}
    duration = float(fmt.get("duration", 0.0)) if fmt.get("duration") else 0.0
    streams = data.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    fps = 0.0
    if v_stream.get("avg_frame_rate"):
        try:
            num, den = v_stream["avg_frame_rate"].split("/")
            fps = float(num) / float(den) if float(den) else 0.0
        except Exception:
            fps = 0.0

    return {
        "duration_sec": duration,
        "width": int(v_stream.get("width") or 0),
        "height": int(v_stream.get("height") or 0),
        "fps": fps,
        "video_codec": v_stream.get("codec_name", "unknown"),
        "audio_codec": a_stream.get("codec_name", "unknown"),
        "audio_sample_rate": int(a_stream.get("sample_rate") or 0),
        "audio_channels": int(a_stream.get("channels") or 0),
    }


def extract_audio(video_path: Path, audio_path: Path, sample_rate: int = 16000) -> None:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-f", "wav", str(audio_path),
    ]
    subprocess.check_call(cmd, timeout=600)


def extract_keyframes(
    video_path: Path, frames_dir: Path, timestamps: list[float], size: int = 320
) -> list[Path]:
    """Extract a frame per timestamp into frames_dir.

    Uses ffmpeg's `-ss` seek before `-i` for fast keyframe-style seek.
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, ts in enumerate(timestamps):
        out = frames_dir / f"frame_{i:05d}_{int(ts*1000):09d}.jpg"
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{ts:.3f}", "-i", str(video_path),
            "-frames:v", "1",
            "-vf", f"scale={size}:-2",
            "-q:v", "2",
            str(out),
        ]
        try:
            subprocess.check_call(cmd, timeout=30)
            if out.exists() and out.stat().st_size > 0:
                written.append(out)
        except Exception:
            # Skip unreadable timestamps — pipeline continues
            continue
    return written


def safe_video_url(job_dir: Path) -> str:
    return f"/api/jobs/{job_dir.name}/video"
