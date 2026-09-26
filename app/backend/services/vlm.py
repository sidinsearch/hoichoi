"""Vision/scene-understanding provider registry.

The orchestrator imports `describe_image(image_path)` and `describe_scene_window(...)`
from this module. Implementations are swapped via `VISION_PROVIDER`:

  - `gemini`     Google Gemini multimodal (default when GEMINI_API_KEY is set)
  - `hf`         Local Hugging Face VLM (Florence-2 / Moondream2 / SmolVLM)
  - `mock`       Deterministic blank observation — used in tests

The provider is asked to summarize **bounded scene windows** (already-shrunk
clip regions) — we never upload a full episode to the cloud. The contract is
strict JSON; the orchestrator never invents missing fields.

Hard rules (negative contexts, pacing, sentence-safety) remain Python-enforced.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Protocol

from PIL import Image

log = logging.getLogger(__name__)


# ----------------------------- Provider interface -----------------------------

class VisionProvider(Protocol):
    name: str

    def describe_image(self, image_path: Path) -> dict:
        ...

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        """Multi-frame scene summary — for richer context when budget allows.

        Default implementation averages independent per-image descriptions.
        """
        ...


# ----------------------------- Shared helpers -----------------------------

_FALLBACK_CONTEXT = {
    "setting": "unknown",
    "activities": [],
    "objects": [],
    "emotion": "neutral",
    "context_tags": [],
}


def _normalize(d: dict) -> dict:
    """Coerce a free-form provider response into our strict schema."""
    return {
        "setting": str(d.get("setting", _FALLBACK_CONTEXT["setting"])),
        "activities": [str(a) for a in (d.get("activities") or [])],
        "objects": [str(o) for o in (d.get("objects") or [])],
        "emotion": str(d.get("emotion", _FALLBACK_CONTEXT["emotion"])),
        "context_tags": [str(t) for t in (d.get("context_tags") or [])],
    }


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else None
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _api_key(*names: str) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip()
    return None


# ----------------------------- Provider implementations -----------------------------

class MockVisionProvider:
    """Returns a neutral observation. Fastest path; deterministic for tests."""

    name = "mock"

    def describe_image(self, image_path: Path) -> dict:
        return dict(_FALLBACK_CONTEXT)

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        return dict(_FALLBACK_CONTEXT)


class GeminiVisionProvider:
    """Google Gemini multimodal — sends ONE small JPEG per call.

    Designed for the **bounded window** rule: we send a single low-res JPEG
    (≤ 320 px wide, ≤ 80 KB) per scene. Full video bytes are never uploaded.
    """

    name = "gemini"
    DEFAULT_MODEL = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or _api_key("GEMINI_API_KEY", "GOOGLE_API_KEY")
        self._model = model or os.getenv("VISION_MODEL") or self.DEFAULT_MODEL
        if not self._api_key:
            raise RuntimeError(
                "Gemini vision selected but GEMINI_API_KEY / GOOGLE_API_KEY is not set."
            )

    def _encode(self, image_path: Path) -> tuple[str, str]:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((320, 320))
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"

    def describe_image(self, image_path: Path) -> dict:
        img_b64, mime = self._encode(image_path)
        prompt = (
            "Look at this single video frame. Return ONLY valid JSON with keys: "
            "setting (short string), activities (list of short strings), "
            "objects (list of short strings), emotion (one word), "
            "context_tags (list of short English/Bengali nouns). No prose."
        )
        text = self._call(prompt, img_b64, mime)
        return _normalize(_extract_json(text) or {})

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        """Multi-frame scene summary — pass up to 4 JPEG thumbnails + transcript window."""
        if not frames:
            return dict(_FALLBACK_CONTEXT)
        parts = [{
            "text": (
                "These are several consecutive frames from the same scene. "
                "Consider the transcript snippet too. Return ONLY JSON: "
                "{setting, activities(list), objects(list), emotion, context_tags(list)}."
                + (f"\nTranscript: {transcript_window[:400]}" if transcript_window else "")
            )
        }]
        for f in frames[:4]:
            b64, mime = self._encode(f)
            parts.append({"inline_data": {"mime_type": mime, "data": b64}})
        text = self._call_parts(parts)
        return _normalize(_extract_json(text) or {})

    # --- HTTP plumbing -----------------------------------------------------

    def _call(self, prompt: str, img_b64: str, mime: str) -> str:
        return self._call_parts([
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": img_b64}},
        ])

    def _call_parts(self, parts: list) -> str:
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"},
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                return (
                    payload.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
            except urllib.error.HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    log.warning("Gemini vision failed with HTTP %s", exc.code)
                    return ""
                time.sleep(2 ** attempt)
            except Exception as exc:  # noqa: BLE001
                log.warning("Gemini vision failed: %s", type(exc).__name__)
                return ""
        return ""


class HFVisionProvider:
    """Local Hugging Face VLM. CPU; opt-in via `VISION_PROVIDER=hf`."""

    name = "hf"

    def __init__(self) -> None:
        from ..config import CONFIG
        self._cfg = CONFIG
        self._processor = None
        self._model = None

    def _ensure_loaded(self):
        if self._processor is not None:
            return
        from transformers import AutoProcessor, AutoModelForCausalLM
        import torch
        name = self._cfg.models.hf_vlm
        if not name:
            raise RuntimeError("HF_MODEL_VLM is empty; nothing to load.")
        self._processor = AutoProcessor.from_pretrained(name, trust_remote_code=True)
        self._model = AutoModelForCausalLM.from_pretrained(
            name, trust_remote_code=True, torch_dtype=torch.float32,
        ).eval()

    def describe_image(self, image_path: Path) -> dict:
        self._ensure_loaded()
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            return dict(_FALLBACK_CONTEXT)
        prompt = (
            "Describe this video frame briefly as JSON with keys: "
            "setting, activities (list), objects (list), emotion, context_tags (list). "
            "Only return JSON."
        )
        import torch
        name = self._cfg.models.hf_vlm.lower()
        try:
            if "florence" in name:
                inputs = self._processor(text=prompt, images=image, return_tensors="pt")
                with torch.no_grad():
                    out = self._model.generate(**inputs, max_new_tokens=128, num_beams=2)
                text = self._processor.batch_decode(out, skip_special_tokens=True)[0]
            elif "moondream" in name:
                inputs = self._processor(images=image, text=prompt, return_tensors="pt")
                with torch.no_grad():
                    out = self._model.generate(**inputs, max_new_tokens=128)
                text = self._processor.batch_decode(out, skip_special_tokens=True)[0]
            else:
                inputs = self._processor(images=image, return_tensors="pt")
                out = self._model.generate(**inputs, max_new_tokens=64)
                text = self._processor.batch_decode(out, skip_special_tokens=True)[0]
        except Exception as exc:
            log.warning("HF vision failed: %s", exc)
            return dict(_FALLBACK_CONTEXT)
        return _normalize(_extract_json(text) or {})

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        if not frames:
            return dict(_FALLBACK_CONTEXT)
        # Conservative: only use the first frame on CPU.
        return self.describe_image(frames[0])


# ----------------------------- Registry & public API -----------------------------

def _resolve_provider_name() -> str:
    explicit = os.getenv("VISION_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if _api_key("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("HF_MODEL_VLM", "").strip():
        return "hf"
    return "mock"


@lru_cache(maxsize=1)
def get_provider(name: str | None = None) -> VisionProvider:
    chosen = (name or _resolve_provider_name()).lower()
    if chosen == "gemini":
        return GeminiVisionProvider()
    if chosen == "hf":
        return HFVisionProvider()
    if chosen == "mock":
        return MockVisionProvider()
    raise ValueError(f"Unknown vision provider: {chosen}")


def describe_image(image_path: Path, provider_name: str | None = None) -> dict:
    try:
        provider = get_provider(provider_name)
    except RuntimeError as exc:
        log.warning("%s — falling back to mock vision", exc)
        provider = get_provider("mock")
    try:
        return provider.describe_image(image_path)
    except Exception as exc:  # noqa: BLE001
        log.warning("vision.describe_image failed: %s", exc)
        return dict(_FALLBACK_CONTEXT)


def describe_scene_window(
    frames: List[Path],
    transcript_window: str = "",
    provider_name: str | None = None,
) -> dict:
    """Describe a *bounded scene window* — never the full video."""
    try:
        provider = get_provider(provider_name)
    except RuntimeError as exc:
        log.warning("%s — falling back to mock vision", exc)
        provider = get_provider("mock")
    try:
        return provider.describe_scene_window(frames, transcript_window=transcript_window)
    except Exception as exc:  # noqa: BLE001
        log.warning("vision.describe_scene_window failed: %s", exc)
        return dict(_FALLBACK_CONTEXT)


def reset_for_tests() -> None:
    get_provider.cache_clear()
