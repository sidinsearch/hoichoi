"""Pydantic models shared across the pipeline.

These are the strict interfaces between stages — keeping them small and explicit
prevents accidental coupling between perception, rules, and outputs.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------- Brand ----------

class BrandCreative(BaseModel):
    id: str
    duration_sec: int
    language: str
    url: str


class Brand(BaseModel):
    brand_id: str
    display_name: str
    category: str
    target_contexts: List[str] = Field(default_factory=list)
    negative_contexts: List[str] = Field(default_factory=list)
    creatives: List[BrandCreative] = Field(default_factory=list)


# ---------- Audio ----------

class ASRSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class AudioSignals(BaseModel):
    """Per-second audio features (sampled at 1Hz)."""
    timeline: List[Dict[str, float]] = Field(default_factory=list)
    # Convenience aggregates
    speech_ratio: float = 0.0
    mean_energy: float = 0.0
    silence_segments: List[Dict[str, float]] = Field(default_factory=list)
    pause_segments: List[Dict[str, float]] = Field(default_factory=list)


# ---------- Shots & frames ----------

class Shot(BaseModel):
    id: int
    start: float
    end: float


class KeyFrame(BaseModel):
    timestamp: float
    path: str  # relative to job dir


# ---------- Scenes ----------

class SceneContext(BaseModel):
    setting: str = "unknown"
    activities: List[str] = Field(default_factory=list)
    objects: List[str] = Field(default_factory=list)
    emotion: str = "neutral"
    narrative_state: str = "routine"
    context_tags: List[str] = Field(default_factory=list)


class Scene(BaseModel):
    scene_id: str
    start_sec: float
    end_sec: float
    shot_ids: List[int] = Field(default_factory=list)
    transcript: str = ""
    context: SceneContext = Field(default_factory=SceneContext)
    confidence: float = 0.0


# ---------- Breaks ----------

class BreakSignals(BaseModel):
    scene_boundary: bool = False
    sentence_complete: bool = False
    dialogue_active: bool = True
    audio_silence_sec: float = 0.0
    visual_transition: bool = False
    emotional_intensity: float = 0.5
    narrative_independence: float = 0.5


class HardConstraints(BaseModel):
    minimum_gap_ok: bool = True
    hourly_limit_ok: bool = True
    ad_load_ok: bool = True
    sentence_complete_ok: bool = False
    dialogue_ok: bool = False


class Candidate(BaseModel):
    candidate_id: str
    timestamp_sec: float
    scene_id: Optional[str] = None
    signals: BreakSignals = Field(default_factory=BreakSignals)
    hard_constraints: HardConstraints = Field(default_factory=HardConstraints)
    score: float = 0.0
    decision: str = "candidate"
    rejected_reasons: List[str] = Field(default_factory=list)
    blocked_brands: List[str] = Field(default_factory=list)


class BrandDecision(BaseModel):
    brand_id: str
    display_name: str
    category: str
    semantic_score: float = 0.0
    eligible: bool = True
    blocked_by: List[str] = Field(default_factory=list)


class CreativeSelection(BaseModel):
    creative_id: str
    language: str
    duration_sec: int


class AcceptedBreak(BaseModel):
    break_id: str
    timestamp_sec: float
    duration_sec: int
    brand: BrandDecision
    creative: CreativeSelection
    score: float
    scene_id: Optional[str] = None
    reason: str = ""


# ---------- Output envelopes ----------

class ScenesDoc(BaseModel):
    schema_version: str = "1.0"
    video: Dict[str, Any] = Field(default_factory=dict)
    scenes: List[Scene] = Field(default_factory=list)


class DebugDoc(BaseModel):
    schema_version: str = "1.0"
    video: Dict[str, Any] = Field(default_factory=dict)
    candidates: List[Candidate] = Field(default_factory=list)
    accepted_breaks: List[AcceptedBreak] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)


class PlaybackBreak(BaseModel):
    id: str
    timestamp_sec: float
    duration_sec: int
    brand_id: str
    display_name: str
    category: str
    context_summary: str = ""


class PlaybackDoc(BaseModel):
    video_url: str
    breaks: List[PlaybackBreak] = Field(default_factory=list)
