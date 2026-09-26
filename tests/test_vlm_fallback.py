"""Regression: a cloud 429 must reach the local fallback, not become 'unknown'.

Gemini used to catch HTTP 429 internally and return an empty string, which the
strict-JSON normalizer turned into `_FALLBACK_CONTEXT` ("unknown"). Every scene
in the job silently lost its visual context even though the local model was
configured and available.
"""
import json
import os
import sys
import urllib.error
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backend.services import vlm  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_provider_state():
    """The quota latch and dead-key set are process-global; isolate each test."""
    vlm.reset_for_tests()
    yield
    vlm.reset_for_tests()


class _FakeResponse:
    """Minimal stand-in for the urlopen context manager."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://example.invalid", code, "err", {}, None
    )


def test_gemini_429_raises_so_fallback_runs(monkeypatch, tmp_path):
    """A quota wall must raise, not retry, so the chain moves to a fallback."""
    calls = {"n": 0}

    def boom(*a, **kw):
        calls["n"] += 1
        raise _http_error(429)

    monkeypatch.setattr(vlm.urllib.request, "urlopen", boom)
    monkeypatch.setattr(vlm.time, "sleep", lambda *_: None)
    monkeypatch.setenv("GEMINI_API_KEY", "key-one")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    frame = tmp_path / "f.jpg"
    Image.new("RGB", (8, 8), (120, 90, 60)).save(frame)

    provider = vlm.GeminiVisionProvider()
    provider._api_key = "key-one"
    provider._model = "m"

    with pytest.raises(vlm.ProviderQuotaExhausted):
        provider.describe_image(frame)

    # One HTTP call per configured key — no retry ladder against a quota wall.
    assert calls["n"] == 1


def test_gemini_rotates_to_second_key(monkeypatch, tmp_path):
    """First key 429s, second key answers — no failure reaches the caller."""
    seen = []

    def flaky(req, *a, **kw):
        seen.append(req.full_url)
        if "key-one" in req.full_url:
            raise _http_error(429)
        payload = json.dumps({
            "candidates": [{"content": {"parts": [
                {"text": '{"setting": "a Kolkata street", "activities": []}'}
            ]}}]
        }).encode()
        return _FakeResponse(payload)

    monkeypatch.setattr(vlm.urllib.request, "urlopen", flaky)
    monkeypatch.setenv("GEMINI_API_KEY", "key-one,key-two")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    frame = tmp_path / "f.jpg"
    Image.new("RGB", (8, 8), (120, 90, 60)).save(frame)

    out = vlm.GeminiVisionProvider().describe_image(frame)
    assert out["setting"] == "a Kolkata street"
    assert len(seen) == 2


def test_dead_gemini_key_is_not_retried(monkeypatch, tmp_path):
    """Once a key is dead the rotation must skip it on the next call."""
    seen = []

    def always_429(req, *a, **kw):
        seen.append(req.full_url)
        raise _http_error(429)

    monkeypatch.setattr(vlm.urllib.request, "urlopen", always_429)
    monkeypatch.setenv("GEMINI_API_KEY", "key-one,key-two")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    frame = tmp_path / "f.jpg"
    Image.new("RGB", (8, 8), (120, 90, 60)).save(frame)

    provider = vlm.GeminiVisionProvider()
    for _ in range(2):
        with pytest.raises(vlm.ProviderQuotaExhausted):
            provider.describe_image(frame)

    # 2 keys on the first call, 0 on the second: both already marked dead.
    assert len(seen) == 2


def test_describe_scene_window_falls_back_to_local(monkeypatch):
    """The public entry point must serve local output when cloud is exhausted."""
    class Exhausted:
        name = "gemini"

        def describe_scene_window(self, frames, transcript_window=""):
            raise vlm.ProviderQuotaExhausted("429")

    class Local:
        name = "hf"

        def describe_scene_window(self, frames, transcript_window=""):
            return {"setting": "a crowded Kolkata street", "activities": ["walking"],
                    "objects": ["rickshaw"], "emotion": "calm",
                    "context_tags": ["local_model"]}

    monkeypatch.setattr(vlm, "get_provider", lambda name=None: {
        "gemini": Exhausted(), "hf": Local(),
    }[name])
    monkeypatch.setenv("VISION_FALLBACK_PROVIDER", "hf")

    out = vlm.describe_scene_window([Path("x.jpg")], provider_name="gemini")
    assert out["setting"] == "a crowded Kolkata street"
    assert out["context_tags"] == ["local_model"]


def test_normalize_local_coerces_prose():
    """Tiny VLMs answer in prose; that must still become a real setting."""
    out = vlm._normalize_local({}, "  people are  waiting near a tea stall  ")
    assert out["setting"].startswith("people are waiting near a tea stall")
    assert out["context_tags"] == ["local_model"]


def test_normalize_local_rejects_empty():
    assert vlm._normalize_local({}, "  ")== vlm._FALLBACK_CONTEXT
    assert vlm._normalize_local({}, "ok") == vlm._FALLBACK_CONTEXT
