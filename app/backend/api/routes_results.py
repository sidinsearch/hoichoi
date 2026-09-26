"""Job status + artifact routes + original video streaming."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ..config import CONFIG
from ..pipeline.orchestrator import STAGE_ORDER

log = logging.getLogger(__name__)
router = APIRouter()


def _job_dir(job_id: str) -> Path:
    safe = (CONFIG.storage_dir / job_id).resolve()
    base = CONFIG.storage_dir.resolve()
    if not str(safe).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Bad job_id")
    if not safe.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    return safe


def _status_dict(job_dir: Path) -> dict:
    p = job_dir / "status.json"
    if not p.exists():
        return {"job_id": job_dir.name, "status": "queued", "progress": 0}
    return json.loads(p.read_text(encoding="utf-8"))


@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    job_dir = _job_dir(job_id)
    s = _status_dict(job_dir)
    s["stage_order"] = STAGE_ORDER
    # Surface artifact paths only when present
    for fname, key in [
        ("scenes.json", "scenes"),
        ("debug.json", "debug"),
        ("vmap.xml", "vmap"),
        ("playback.json", "playback"),
        ("transcript.json", "transcript"),
    ]:
        if (job_dir / fname).exists():
            s.setdefault("artifacts", {})[key] = f"/api/jobs/{job_id}/vmap" if key == "vmap" else f"/api/jobs/{job_id}/{fname.removesuffix('.json')}"
    return s


@router.get("/jobs/{job_id}/scenes")
def scenes(job_id: str):
    f = _job_dir(job_id) / "scenes.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(f, media_type="application/json", filename="scenes.json")


@router.get("/jobs/{job_id}/debug")
def debug(job_id: str):
    f = _job_dir(job_id) / "debug.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(f, media_type="application/json", filename="debug.json")


@router.get("/jobs/{job_id}/vmap")
def vmap(job_id: str):
    f = _job_dir(job_id) / "vmap.xml"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(f, media_type="application/xml", filename="vmap.xml")


@router.get("/jobs/{job_id}/playback")
def playback(job_id: str):
    f = _job_dir(job_id) / "playback.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(f, media_type="application/json", filename="playback.json")


@router.get("/jobs/{job_id}/transcript")
def transcript(job_id: str):
    f = _job_dir(job_id) / "transcript.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(f, media_type="application/json", filename="transcript.json")


@router.get("/jobs/{job_id}/video")
def video(job_id: str):
    job_dir = _job_dir(job_id)
    # Find original video (any non-service file)
    candidates = sorted(
        [p for p in job_dir.iterdir()
         if p.is_file()
         and p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm")
         and p.name not in {"audio.wav"}],
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    if not candidates:
        raise HTTPException(status_code=404, detail="Video not found")
    target = candidates[0]
    # Determine media type
    ext = target.suffix.lower()
    media = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
    }.get(ext, "application/octet-stream")
    # Range support so seeking works in HTML5 video
    return FileResponse(target, media_type=media, filename=target.name)
