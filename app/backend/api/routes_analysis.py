"""Upload + analyze routes."""

from __future__ import annotations

import logging
import shutil
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import CONFIG
from ..pipeline.orchestrator import JobStatus, create_job, launch_in_background, new_job_id

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze(video: UploadFile = File(...), brand_json: UploadFile = File(...)):
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
    launch_in_background(job_id, stored_video, stored_brand, job_dir, status)
    return {"job_id": job_id, "status": status.status}
