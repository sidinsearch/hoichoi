"""Shot-boundary detection using PySceneDetect's ContentDetector.

These boundaries are *low-level evidence* — never final scene boundaries.
"""

from __future__ import annotations

from typing import List

from ..models.schemas import Shot


def detect_shots(video_path) -> List[Shot]:
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
    except Exception:
        # If PySceneDetect unavailable, return empty list — orchestrator handles gracefully.
        return []

    video = open_video(str(video_path))
    sm = SceneManager()
    sm.add_detector(ContentDetector(threshold=27.0, min_scene_len=15))
    sm.detect_scenes(video)
    scene_list = sm.get_scene_list()
    shots: List[Shot] = []
    for i, (start, end) in enumerate(scene_list, start=1):
        shots.append(
            Shot(
                id=i,
                start=float(start.get_seconds()),
                end=float(end.get_seconds()),
            )
        )
    return shots
