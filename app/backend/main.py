"""FastAPI entry — exposes /api/* endpoints and serves nothing else.

The frontend is served separately by Next.js. CORS is wide open for local dev.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes_analysis import router as analysis_router
from .api.routes_results import router as results_router
from .config import CONFIG

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="hoichoi Context-Aware Ad Intelligence", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analysis_router, prefix="/api")
app.include_router(results_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "hoichoi-backend", "version": "0.1.0"}


@app.get("/")
def root():
    return JSONResponse({"service": "hoichoi-backend", "docs": "/docs"})
