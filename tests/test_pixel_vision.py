"""The pixel provider must produce a real label, not 'unknown'.

On a 1-core host the only rung that can serve a few hundred scene windows is the
deterministic pixel analysis. These tests pin that it stays honest: it reports
measurable properties and never claims to understand actors or emotion.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backend.services import vlm  # noqa: E402


def _frame(tmp_path, name, arr, path=None):
    p = path or (tmp_path / f"{name}.jpg")
    Image.fromarray(arr.astype(np.uint8)).save(p)
    return p


def test_dark_frame_is_labelled(tmp_path):
    arr = np.full((48, 48, 3), 12, dtype=np.uint8)
    out = vlm._analyze_frame_cheap(_frame(tmp_path, "dark", arr))
    assert out["setting"] != "unknown"
    assert "low_light" in out["context_tags"]
    assert "pixel_analysis" in out["context_tags"]


def test_bright_frame_is_labelled(tmp_path):
    arr = np.full((48, 48, 3), 245, dtype=np.uint8)
    out = vlm._analyze_frame_cheap(_frame(tmp_path, "bright", arr))
    assert "high_key" in out["context_tags"]


def test_colour_cast_detected(tmp_path):
    arr = np.zeros((48, 48, 3), dtype=np.uint8)
    arr[..., 0] = 200  # strong red
    out = vlm._analyze_frame_cheap(_frame(tmp_path, "red", arr))
    assert "warm_red_cast" in out["context_tags"]


def test_provider_never_invents_semantics(tmp_path):
    """No fabricated activities, objects or emotions — only measurements."""
    arr = np.random.default_rng(0).integers(0, 255, (48, 48, 3))
    out = vlm.PixelVisionProvider().describe_image(_frame(tmp_path, "rnd", arr))
    assert out["activities"] == []
    assert out["objects"] == []
    assert out["emotion"] == "neutral"
    assert "local_model" not in out["context_tags"]


def test_window_merges_frame_agreement(tmp_path):
    dark = _frame(tmp_path, "d", np.full((48, 48, 3), 10, dtype=np.uint8))
    light = _frame(tmp_path, "l", np.full((48, 48, 3), 240, dtype=np.uint8))
    out = vlm.PixelVisionProvider().describe_scene_window([dark, light])
    assert "low_light" in out["context_tags"]
    assert "high_key" in out["context_tags"]


def test_corrupt_file_degrades_gracefully(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    assert vlm._analyze_frame_cheap(bad) == vlm._FALLBACK_CONTEXT


def test_pixel_is_last_resort_rung(monkeypatch):
    """The chain must always end at something that labels a frame."""
    monkeypatch.delenv("VISION_FALLBACK_PROVIDER", raising=False)
    monkeypatch.delenv("VISION_SECONDARY_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert vlm._vision_fallbacks("gemini") == ["pixel", "mock"]


def test_openai_inserted_only_when_key_present(monkeypatch):
    monkeypatch.delenv("VISION_FALLBACK_PROVIDER", raising=False)
    monkeypatch.delenv("VISION_SECONDARY_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert vlm._vision_fallbacks("gemini") == ["openai", "pixel", "mock"]


def test_local_vlm_is_opt_in_only(monkeypatch):
    """Setting HF_MODEL_VLM must NOT silently insert the slow local model."""
    monkeypatch.delenv("VISION_FALLBACK_PROVIDER", raising=False)
    monkeypatch.delenv("VISION_SECONDARY_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HF_MODEL_VLM", "HuggingFaceTB/SmolVLM-256M-Instruct")
    assert "hf" not in vlm._vision_fallbacks("gemini")
    # ...and it is reachable explicitly.
    monkeypatch.setenv("VISION_FALLBACK_PROVIDER", "hf")
    assert vlm._vision_fallbacks("gemini")[0] == "hf"


def test_openai_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        vlm.OpenAIVisionProvider()


def test_openai_429_raises_for_chain(monkeypatch, tmp_path):
    import urllib.error

    def boom(*a, **kw):
        raise urllib.error.HTTPError("u", 429, "rate", {}, None)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(vlm.urllib.request, "urlopen", boom)
    frame = tmp_path / "f.jpg"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(frame)
    with pytest.raises(vlm.ProviderQuotaExhausted):
        vlm.OpenAIVisionProvider().describe_image(frame)
