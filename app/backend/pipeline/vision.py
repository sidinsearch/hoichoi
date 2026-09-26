"""Visual preprocessing — representative frame extraction only.

We never send every frame to the VLM. Per shot we keep one representative frame
at the midpoint; for very long shots we add ~1 frame per 30 seconds.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..config import CONFIG
from ..models.schemas import Shot, KeyFrame
from ..services.ffmpeg import extract_keyframes


def choose_representative_times(shots: List[Shot], max_frames: int | None = None) -> List[float]:
    if max_frames is None:
        max_frames = CONFIG.models.max_keyframes
    if not shots:
        return []
    times = []
    for sh in shots:
        mid = (sh.start + sh.end) / 2.0
        times.append(mid)
        # Long-shot extras
        if sh.end - sh.start > 60:
            t = sh.start
            while t < sh.end and len(times) < max_frames * 2:
                t += 30
                if t < sh.end:
                    times.append(t)
    # Cap to a sensible budget for CPU inference
    if len(times) > max_frames:
        # uniform stride across the whole video
        stride = len(times) / max_frames
        times = [times[int(i * stride)] for i in range(max_frames)]
    return times


def extract_keyframes_for(video_path: Path, shots: List[Shot], frames_dir: Path) -> List[KeyFrame]:
    times = choose_representative_times(shots)
    written = extract_keyframes(video_path, frames_dir, times)
    keyframes: List[KeyFrame] = []
    for path in written:
        # Filename pattern: frame_{i:05d}_{ms:09d}.jpg
        try:
            stem = path.stem
            ts_part = stem.split("_")[-1]
            ts_sec = int(ts_part) / 1000.0
        except Exception:
            ts_sec = 0.0
        # Store an absolute path; pipeline reads it as Path directly.
        keyframes.append(KeyFrame(timestamp=ts_sec, path=str(path)))
    return keyframes
