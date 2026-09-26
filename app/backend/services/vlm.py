"""Optional local VLM via Hugging Face `transformers`.

Disabled by default; enabled when `HF_MODEL_VLM` is non-empty and `vision_enabled` is True.
We pick **small, fast** models:

  - `microsoft/Florence-2-base` (~270M, runs on CPU with int8 quantization in 1-2GB)
  - `vikhyatk/moondream2` (~1.8B, slower but richer)

The output is always coerced into a strict JSON dict for downstream scene fusion.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from PIL import Image

from ..config import CONFIG


_FALLBACK_CONTEXT = {
    "setting": "unknown",
    "activities": [],
    "objects": [],
    "emotion": "neutral",
    "context_tags": [],
}


@lru_cache(maxsize=1)
def _get_processor_and_model():
    from transformers import AutoProcessor, AutoModelForCausalLM
    import torch

    name = CONFIG.models.hf_vlm
    processor = AutoProcessor.from_pretrained(name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        name, trust_remote_code=True, torch_dtype=torch.float32
    )
    model.eval()
    return processor, model


def _parse_json_safely(text: str) -> Optional[dict]:
    """Find the first JSON object/array in a free-form string. Returns dict if possible."""
    if not text:
        return None
    # Try direct parse first
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else None
    except Exception:
        pass
    # Look for the first {...} block
    m = re.search(r"\{[\s\S]*?\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _fallback_from_filename(path: Path) -> dict:
    """Fallback VLM: just synthesize a blank observation. Avoids silent invention."""
    return dict(_FALLBACK_CONTEXT)


def describe_image(image_path: Path) -> dict:
    """Return a structured scene-context dict for one keyframe.

    Schema (always):
        {
          "setting": str,
          "activities": list[str],
          "objects": list[str],
          "emotion": str,
          "context_tags": list[str]
        }
    """
    if not CONFIG.models.vision_enabled:
        return _fallback_from_filename(image_path)

    try:
        processor, model = _get_processor_and_model()
    except Exception:
        return _fallback_from_filename(image_path)

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception:
        return _fallback_from_filename(image_path)

    name = CONFIG.models.hf_vlm.lower()
    prompt = (
        "Describe this video frame briefly as JSON with keys: "
        "setting, activities (list), objects (list), emotion, context_tags (list). "
        "Only return JSON."
    )

    try:
        if "florence" in name:
            import torch
            inputs = processor(text=prompt, images=image, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(
                    **inputs, max_new_tokens=128, num_beams=2, do_sample=False
                )
            text = processor.batch_decode(out, skip_special_tokens=True)[0]
        elif "moondream" in name:
            import torch
            inputs = processor(images=image, text=prompt, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=128)
            text = processor.batch_decode(out, skip_special_tokens=True)[0]
        else:
            # Generic captioning fallback
            inputs = processor(images=image, return_tensors="pt")
            out = model.generate(**inputs, max_new_tokens=64)
            text = processor.batch_decode(out, skip_special_tokens=True)[0]
    except Exception:
        return _fallback_from_filename(image_path)

    parsed = _parse_json_safely(text) or {}
    return {
        "setting": str(parsed.get("setting", _FALLBACK_CONTEXT["setting"])),
        "activities": list(parsed.get("activities") or []),
        "objects": list(parsed.get("objects") or []),
        "emotion": str(parsed.get("emotion", _FALLBACK_CONTEXT["emotion"])),
        "context_tags": list(parsed.get("context_tags") or []),
    }
