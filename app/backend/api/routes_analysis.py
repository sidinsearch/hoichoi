"""Upload + analyze routes."""

from __future__ import annotations

import logging
import shutil
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config import CONFIG
from ..pipeline.orchestrator import JobStatus, create_job, launch_in_background, new_job_id

log = logging.getLogger(__name__)
router = APIRouter()

_RESOURCE_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def _resources_dir() -> Path:
    return CONFIG.project_root / "resources"


def _safe_resource(name: str) -> Path:
    root = _resources_dir().resolve()
    target = (root / name).resolve()
    if not str(target).startswith(str(root)) or not target.is_file():
        raise HTTPException(status_code=404, detail="Resource not found")
    return target


@router.get("/resources")
def resources():
    root = _resources_dir()
    return {"resources": [{"name": p.name, "kind": "brand_json" if p.suffix == ".json" else "video", "size": p.stat().st_size, "url": f"/api/resources/{p.name}"} for p in sorted(root.iterdir()) if p.is_file() and (p.suffix.lower() in _RESOURCE_EXTENSIONS or p.name == "brands.json")]}


@router.get("/resources/{name}")
def resource(name: str):
    target = _safe_resource(name)
    media = "application/json" if target.suffix == ".json" else {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".mkv": "video/x-matroska"}.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(target, media_type=media, filename=target.name)


@router.post("/analyze-resource")
async def analyze_resource(
    resource_name: str = Form(...),
    brand_name: str = Form("brands.json"),
    language: str = Form("bn"),
    brand_json: UploadFile | None = File(None),
):
    video_path = _safe_resource(resource_name)
    if video_path.suffix.lower() not in _RESOURCE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Choose a resource video")
    if brand_json is not None:
        brand_bytes = await brand_json.read()
        if not brand_json.filename or not brand_json.filename.lower().endswith(".json"):
            raise HTTPException(status_code=400, detail="Custom brand file must be JSON")
    else:
        brand_path = _safe_resource(brand_name)
        if brand_path.name != "brands.json":
            raise HTTPException(status_code=400, detail="Choose brands.json")
        brand_bytes = brand_path.read_bytes()
    job_id = new_job_id()
    job_dir = CONFIG.storage_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    stored_video = job_dir / video_path.name
    stored_brand = job_dir / "brands.uploaded.json"
    stored_video.symlink_to(video_path)
    stored_brand.write_bytes(brand_bytes)
    status, stored_video, stored_brand = create_job(stored_video, stored_brand, job_dir)
    launch_in_background(job_id, stored_video, stored_brand, job_dir, status, language=language)
    return {"job_id": job_id, "status": status.status}


@router.post("/analyze")
async def analyze(video: UploadFile = File(...), brand_json: UploadFile = File(...), language: str = Form("bn")):
    if not video.filename or not brand_json.filename:
        raise HTTPException(status_code=400, detail="Both video and brand_json are required")

    job_id = new_job_id()
    job_dir: Path = CONFIG.storage_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Save brand json first (small, fast)
    brand_path = job_dir / "brands.uploaded.json"
    brand_bytes = await brand_json.read()
    brand_path.write_bytes(brand_bytes)

    # Save video
    video_path = job_dir / video.filename
    with video_path.open("wb") as out:
        shutil.copyfileobj(video.file, out)

    status, stored_video, stored_brand = create_job(video_path, brand_path, job_dir)
    launch_in_background(job_id, stored_video, stored_brand, job_dir, status, language=language)
    return {"job_id": job_id, "status": status.status}
