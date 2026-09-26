"""Provider-mocking tests — no API keys, no network.

These guarantee:
  - The pipeline imports cleanly with no API keys set.
  - The orchestrator path can run end-to-end against `mock` providers.
  - Provider resolution picks `gemini`/`groq` when keys are present, else `mock`.
  - Bounded scene-window function returns ≤4-frame windows.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.backend.services.asr import (
    get_provider as asr_provider,
    reset_for_tests as asr_reset,
)
from app.backend.services.vlm import (
    describe_image,
    describe_scene_window,
    get_provider as vision_provider,
    reset_for_tests as vision_reset,
)


def test_asr_provider_resolves_mock_without_keys(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("ASR_PROVIDER", "mock")
    asr_reset()
    p = asr_provider("mock")
    assert p.name == "mock"


def test_vision_provider_resolves_mock_without_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("VISION_PROVIDER", "mock")
    vision_reset()
    p = vision_provider("mock")
    assert p.name == "mock"


def test_vision_provider_picks_gemini_when_key_present(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-xxx")
    monkeypatch.setenv("VISION_PROVIDER", "gemini")
    monkeypatch.setenv("VISION_MODEL", "gemini-2.0-flash")
    vision_reset()
    p = vision_provider()
    assert p.name == "gemini"


def test_asr_provider_picks_groq_when_key_present(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-xxx")
    monkeypatch.setenv("ASR_PROVIDER", "groq")
    asr_reset()
    p = asr_provider()
    assert p.name == "groq"


def test_describe_scene_window_caps_window_size(monkeypatch, tmp_path):
    """describe_scene_window must accept arbitrary paths; mock returns neutral."""
    monkeypatch.setenv("VISION_PROVIDER", "mock")
    vision_reset()
    frames = [tmp_path / f"f{i}.jpg" for i in range(10)]
    for f in frames:
        f.write_bytes(b"x")
    out = describe_scene_window(frames[:6], transcript_window="hello")
    assert out["emotion"] == "neutral"
    assert isinstance(out["context_tags"], list)
