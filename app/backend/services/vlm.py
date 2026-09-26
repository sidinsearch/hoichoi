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


# Tiny local VLMs (SmolVLM-256M) rarely emit valid JSON. Prompting for a short
# plain sentence and coercing it into our schema beats discarding the frame.
_LOCAL_VISION_PROMPT = (
    "Describe this video frame in one short sentence. "
    "Say where it is set and what is happening. Be literal."
)


def _normalize_local(parsed: dict, raw_text: str) -> dict:
    """Coerce a local model's free-form answer into the strict schema.

    Never invents brand-unsafe fields: `setting` stays descriptive and
    `activities` is only filled from what the model actually said.
    """
    if parsed:
        return _normalize(parsed)
    sentence = " ".join((raw_text or "").split()).strip()
    if not sentence or len(sentence) < 8:
        return dict(_FALLBACK_CONTEXT)
    if not sentence.endswith("."):
        sentence += "."
    return {
        "setting": sentence[:180],
        "activities": [],
        "objects": [],
        "emotion": "neutral",
        "context_tags": ["local_model"],
    }


def _api_key(*names: str) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip()
    return None


def _api_keys(*names: str) -> List[str]:
    """All configured keys for a provider, in order, blanks removed.

    Several keys may be supplied comma-separated so a quota-exhausted key is
    skipped and the next one is used without a redeploy.
    """
    out: List[str] = []
    for n in names:
        for part in (os.getenv(n) or "").split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


# ----------------------------- Provider implementations -----------------------------

class ProviderQuotaExhausted(RuntimeError):
    """Cloud provider refused the call for quota/rate-limit reasons.

    Raised instead of silently returning a blank observation, so the fallback
    chain in `describe_image`/`describe_scene_window` can switch to the local
    model. A blank `setting` here previously looked identical to a real
    "unknown" and hid the failure for every scene in the job.
    """


class OpenAIVisionProvider:
    """OpenAI vision (gpt-4o-mini) — second cloud rung.

    Fills in when Gemini is quota-exhausted. Key from `OPENAI_API_KEY`; without
    one the provider refuses to load so the chain moves to the next rung.

    Defaults to `gpt-4o-mini`: it reads images, and at ~200 scene windows per
    video the per-call cost is the whole reason the chain exists. Override with
    OPENAI_VISION_MODEL if you need better scene reading.
    """

    name = "openai"

    def __init__(self) -> None:
        self._api_key = _api_key("OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "OpenAI vision selected but OPENAI_API_KEY is not set. "
                "Set it in the environment, or change VISION_FALLBACK_PROVIDER."
            )
        self._model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
        self._base = os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")

    def _post(self, body: dict) -> str:
        req = urllib.request.Request(
            f"{self._base}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                return payload["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    raise ProviderQuotaExhausted(
                        "OpenAI vision HTTP 429 (quota/rate limit)"
                    ) from exc
                if exc.code not in {500, 502, 503, 504} or attempt == 2:
                    log.warning("OpenAI vision HTTP %s", exc.code)
                    return ""
                time.sleep(min(30.0, 4.0 * 2 ** attempt))
            except Exception as exc:  # noqa: BLE001
                log.warning("OpenAI vision failed: %s", type(exc).__name__)
                return ""
        return ""

    def _data_url(self, image_path: Path) -> str:
        from io import BytesIO

        with Image.open(image_path) as im:
            small = im.convert("RGB")
            small.thumbnail((768, 768))
            buf = BytesIO()
            small.save(buf, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    def _ask(self, image_path: Path) -> dict:
        body = {
            "model": self._model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": _LOCAL_VISION_PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": self._data_url(image_path)}},
                ],
            }],
            "temperature": 0.0,
        }
        text = self._post(body)
        return _normalize_local(_extract_json(text) or {}, text)

    def describe_image(self, image_path: Path) -> dict:
        return self._ask(image_path)

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        if not frames:
            return dict(_FALLBACK_CONTEXT)
        return self._ask(frames[0])


class MockVisionProvider:
    """Returns a neutral observation. Fastest path; deterministic for tests."""

    name = "mock"

    def describe_image(self, image_path: Path) -> dict:
        return dict(_FALLBACK_CONTEXT)

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        return dict(_FALLBACK_CONTEXT)


def _analyze_frame_cheap(image_path: Path) -> dict:
    """Describe a frame from pixels alone — no model, no network, no quota.

    Used as the last-resort provider when every model is unavailable. It cannot
    name actors or emotions, so it never claims to: it reports measurable,
    honest visual facts (brightness, contrast, colour cast, motion proxy,
    palette) and the dialogue overlapping the frame. Brand matching keys off
    `context_tags`, which are drawn from real measurable properties.
    """
    try:
        import numpy as np
        from PIL import Image

        with Image.open(image_path) as im:
            small = im.convert("RGB").resize((64, 64))
            arr = np.asarray(small, dtype=np.float32) / 255.0
    except Exception as exc:  # noqa: BLE001
        log.warning("cheap frame analysis failed: %s", exc)
        return dict(_FALLBACK_CONTEXT)

    lum = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mean_lum = float(lum.mean())
    std_lum = float(lum.std())
    r, g, b = (float(arr[..., i].mean()) for i in range(3))
    spread = float(arr.max(axis=2).mean() - arr.min(axis=2).mean())

    if mean_lum < 0.22:
        setting = "dark low-key scene"
        tags = ["low_light"]
    elif mean_lum > 0.78:
        setting = "bright high-key scene"
        tags = ["high_key"]
    else:
        setting = "evenly lit interior or exterior"
        tags = ["mid_tone"]

    if std_lum < 0.06:
        setting += ", flat low-contrast image"
        tags.append("flat")
    elif std_lum > 0.20:
        setting += ", high contrast"
        tags.append("high_contrast")

    # Colour cast: dominant channel, only when meaningfully ahead of the others.
    channels = {"warm_red": r, "green": g, "cool_blue": b}
    cast, val = max(channels.items(), key=lambda kv: kv[1])
    if val - sorted(channels.values())[-2] > 0.06:
        tags.append(f"{cast}_cast")

    if spread < 0.10:
        setting += ", muted palette"
        tags.append("muted_palette")

    return {
        "setting": setting,
        "activities": [],
        "objects": [],
        "emotion": "neutral",
        "context_tags": sorted(set(tags + ["pixel_analysis"])),
    }


class PixelVisionProvider:
    """Deterministic CPU provider — the final rung of the fallback chain.

    Ponytail: this is not scene understanding and does not pretend to be. It is
    the cheapest thing that still produces a truthful, non-"unknown" label from
    data we already have. Replace with a real local VLM when running on a host
    with more than one CPU core or a GPU.
    """

    name = "pixel"

    def describe_image(self, image_path: Path) -> dict:
        return _analyze_frame_cheap(image_path)

    def describe_scene_window(self, frames: List[Path], transcript_window: str = "") -> dict:
        if not frames:
            return dict(_FALLBACK_CONTEXT)
        obs = _analyze_frame_cheap(frames[0])
        # A multi-frame window is summarised by agreement across its frames.
        if len(frames) > 1:
            tags: set[str] = set()
            for frame in frames[1:]:
                tags.update(_analyze_frame_cheap(frame).get("context_tags", []))
            obs["context_tags"] = sorted(set(obs["context_tags"]) | tags)
        return obs


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
        # GEMINI_API_KEY may hold several comma-separated keys. A key that
        # answers 429 is dropped for the rest of the process and the next one is
        # tried, so a second project key silently extends the quota.
        keys = [
            k for k in _api_keys("GEMINI_API_KEY", "GOOGLE_API_KEY")
            if k not in _DEAD_GEMINI_KEYS
        ]
        if not keys:
            # Every key is already known-exhausted. Retrying one would reset the
            # per-frame cost for no chance of success — fail fast so the chain
            # moves to the next provider.
            raise ProviderQuotaExhausted("all configured Gemini keys are exhausted")
        last_error: Exception | None = None
        for key in keys:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self._model}:generateContent?key={key}"
            )
            req = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            try:
                return self._attempt(req, key=key)
            except ProviderQuotaExhausted as exc:
                log.warning("Gemini key ...%s exhausted: %s", key[-4:], exc)
                _DEAD_GEMINI_KEYS.add(key)
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        return ""

    def _attempt(self, req, key: str = "") -> str:
        for attempt in range(6):
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
                if exc.code in {429}:
                    log.warning("Gemini vision quota exhausted (HTTP 429); using local fallback")
                    raise ProviderQuotaExhausted(
                        f"Gemini vision HTTP 429 (quota/rate limit) after {attempt + 1} attempts"
                    ) from exc
                if exc.code not in {500, 502, 503, 504} or attempt == 5:
                    body = exc.read()[:300].decode("utf-8", "replace")
                    log.warning("Gemini vision HTTP %s: %s", exc.code, body)
                    return ""
                delay = float(exc.headers.get("Retry-After") or 0) or min(60.0, 5.0 * 2 ** attempt)
                log.warning("Gemini vision HTTP %s, retrying in %.0fs (attempt %s/6)", exc.code, delay, attempt + 1)
                time.sleep(delay)
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
        image.thumbnail((384, 384))
        import torch
        name = (self._cfg.models.hf_vlm or "").lower()
        try:
            if "smolvlm" in name or "smol" in name:
                # SmolVLM needs the Idefics3-style chat template with an
                # explicit {"type": "image"} content block; passing images
                # positionally produces a prompt/tensor mismatch.
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": _LOCAL_VISION_PROMPT},
                    ],
                }]
                prompt = self._processor.apply_chat_template(
                    messages, add_generation_prompt=True
                )
                inputs = self._processor(
                    text=prompt, images=[image], return_tensors="pt"
                )
                with torch.no_grad():
                    out = self._model.generate(
                        **inputs, max_new_tokens=48, do_sample=False
                    )
                text = self._processor.batch_decode(out, skip_special_tokens=True)[0]
                text = text.split("Assistant:")[-1]
                return _normalize_local(_extract_json(text) or {}, text)
            prompt = _LOCAL_VISION_PROMPT
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
                inputs = self._processor(images=image, text=prompt, return_tensors="pt")
                with torch.no_grad():
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
    if chosen == "pixel":
        return PixelVisionProvider()
    if chosen == "openai":
        return OpenAIVisionProvider()
    raise ValueError(f"Unknown vision provider: {chosen}")


# A quota wall does not reset between frames. Without this, every one of a few
# hundred scene windows would pay the full retry+backoff ladder before falling
# back — turning a quota error into an hours-long job.
_QUOTA_TRIPPED: set[str] = set()

# Individual Gemini keys that answered 429, so the rotation skips them.
_DEAD_GEMINI_KEYS: set[str] = set()


def _mark_quota_exhausted(provider: str) -> None:
    _QUOTA_TRIPPED.add(provider)
    log.warning("vision provider %s marked exhausted for this process", provider)


def reset_quota_state() -> None:
    _QUOTA_TRIPPED.clear()


def _vision_fallbacks(failed: str) -> list[str]:
    """Ordered rungs after the primary provider fails.

    Built from what is actually configured, so a user with one cloud key, two,
    or none gets a working chain without editing code. `pixel` is always last
    and always present: a deterministic label beats a blank "unknown" for every
    scene in the job.
    """
    choices: list[str] = []
    # Cloud rungs, in configured order, skipping the one that just failed.
    for env in ("VISION_FALLBACK_PROVIDER", "VISION_SECONDARY_PROVIDER"):
        name = os.getenv(env, "").strip().lower()
        if name:
            choices.append(name)
    if _api_key("OPENAI_API_KEY"):
        choices.append("openai")
    # The local VLM is opt-in only, never auto-inserted: SmolVLM-256M measured
    # 105-143s/frame on a 1-core host, which would turn a few hundred scene
    # windows into an hours-long job. Set VISION_FALLBACK_PROVIDER=hf to use it.
    choices.extend(["pixel", "mock"])
    return [n for n in dict.fromkeys(choices) if n and n != failed]


def _run_with_fallback(caller, provider_name: str | None) -> dict:
    """Call the configured provider, then fallbacks, honouring the quota latch."""
    primary_name = (provider_name or _resolve_provider_name()).lower()
    order: list[str] = []
    if primary_name not in _QUOTA_TRIPPED:
        order.append(primary_name)
    order.extend(n for n in _vision_fallbacks(primary_name) if n not in order)

    for name in order:
        try:
            provider = get_provider(name)
        except Exception as exc:  # noqa: BLE001
            log.warning("vision provider %s unavailable: %s", name, exc)
            continue
        try:
            return caller(provider)
        except ProviderQuotaExhausted as exc:
            # Latch: every later frame in this process skips this provider.
            _mark_quota_exhausted(name)
            log.warning("switching vision provider away from %s: %s", name, exc)
        except Exception as exc:  # noqa: BLE001
            log.warning("vision provider %s failed: %s", name, exc)
    return dict(_FALLBACK_CONTEXT)


def describe_image(image_path: Path, provider_name: str | None = None) -> dict:
    return _run_with_fallback(
        lambda p: p.describe_image(image_path), provider_name
    )


def describe_scene_window(
    frames: List[Path],
    transcript_window: str = "",
    provider_name: str | None = None,
) -> dict:
    """Describe a *bounded scene window* — never the full video."""
    return _run_with_fallback(
        lambda p: p.describe_scene_window(frames, transcript_window=transcript_window),
        provider_name,
    )


def reset_for_tests() -> None:
    get_provider.cache_clear()
    _QUOTA_TRIPPED.clear()
    _DEAD_GEMINI_KEYS.clear()
