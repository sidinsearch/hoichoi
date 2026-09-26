"""Translate Bengali ASR segments to English after transcription.

Translation is best-effort: a failed or rate-limited call leaves the original
text untouched rather than failing the whole job.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import List

log = logging.getLogger(__name__)

_MODEL = os.getenv("TRANSLATE_MODEL", "gemini-3.5-flash-lite")
_MAX_SEGMENTS = int(os.getenv("TRANSLATE_MAX_SEGMENTS", "0") or 0)  # 0 = all
_BATCH = 40


def _api_key() -> str | None:
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _is_bengali(text: str) -> bool:
    return any("\u0980" <= ch <= "\u09ff" for ch in text)


def _call(prompt: str, key: str) -> str:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent?key={key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            return payload.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 4:
                log.warning("Translation HTTP %s", exc.code)
                return ""
            delay = float(exc.headers.get("Retry-After") or 0) or min(45.0, 4.0 * 2 ** attempt)
            time.sleep(delay)
        except Exception as exc:  # noqa: BLE001
            log.warning("Translation failed: %s", type(exc).__name__)
            return ""
    return ""


def translate_segments(segments: List) -> List:
    """Attach `text_en` to each segment, leaving `text` as the original."""
    key = _api_key()
    if not key or os.getenv("TRANSLATE_ENABLED", "1").lower() in {"0", "false", "no"}:
        return segments

    targets = [s for s in segments if getattr(s, "text", "") and _is_bengali(s.text)]
    if _MAX_SEGMENTS:
        targets = targets[:_MAX_SEGMENTS]
    if not targets:
        return segments

    done = 0
    for start in range(0, len(targets), _BATCH):
        chunk = targets[start : start + _BATCH]
        payload = [{"i": start + n, "text": s.text} for n, s in enumerate(chunk)]
        prompt = (
            "Translate each Bengali subtitle line into natural English. "
            "Keep meaning; do not invent dialogue. Return ONLY JSON: "
            '{"results":[{"i":<index>,"en":"<english>"}]}. Lines: '
            + json.dumps(payload, ensure_ascii=False)
        )
        raw = _call(prompt, key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            for item in data.get("results", []):
                idx = item.get("i")
                en = (item.get("en") or "").strip()
                if isinstance(idx, int) and 0 <= idx < len(targets) and en:
                    targets[idx].text_en = en
                    done += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("Translation parse failed: %s", type(exc).__name__)
    log.info("Translated %s/%s segments", done, len(targets))
    return segments
