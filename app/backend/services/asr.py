"""ASR provider registry.

Provider implementations are swappable through the `ASR_PROVIDER` env var:

  - `groq`        Groq Whisper Large-v3-Turbo (default when API key is present)
  - `gemini`      Google Gemini multimodal fallback (audio/video understanding)
  - `faster_whisper` local CPU fallback (offline / no-key path)
  - `mock`        Synthetic transcription (used in tests; never calls the network)

The orchestrator imports `transcribe(audio_path)` from this module and never
touches a provider class directly. Providers are LRU-cached and selected on
first call.

All HTTP-bound providers require their API key to be present at construction
time; we never hard-code a key, never log one, and never bake one into the
image.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Protocol

from ..models.schemas import ASRSegment

log = logging.getLogger(__name__)


# ----------------------------- Provider interface -----------------------------

class ASRProvider(Protocol):
    name: str

    def transcribe(self, audio_path: Path, language: str | None = None) -> List[ASRSegment]:
        ...


# ----------------------------- Provider implementations -----------------------------

def _api_key(envvar: str) -> str | None:
    val = os.getenv(envvar)
    if not val:
        return None
    return val.strip() or None


class MockASRProvider:
    """Deterministic synthetic provider — used by tests and offline sandboxing."""

    name = "mock"

    def __init__(self, segments: List[ASRSegment] | None = None) -> None:
        self._segments = segments or []

    def transcribe(self, audio_path: Path, language: str | None = None) -> List[ASRSegment]:
        if self._segments:
            return list(self._segments)
        # Default: three synthetic segments anchored at 0 / mid / near-end.
        # No audio is decoded.
        return [
            ASRSegment(start=0.0, end=8.0, text="Synthetic opening narration.", confidence=0.95),
            ASRSegment(start=12.0, end=20.0, text="Synthetic dialogue sample.", confidence=0.92),
            ASRSegment(start=24.0, end=32.0, text="Synthetic scene description.", confidence=0.90),
        ]


class FasterWhisperProvider:
    """Local CPU ASR (faster-whisper + 8 kHz cache + VAD). Kept offline-friendly."""

    name = "faster_whisper"

    def __init__(self) -> None:
        from ..config import CONFIG
        self._cfg = CONFIG
        self._model = None
        self._ensure_8k = None  # lazy-bound function, set on first call

    def _ensure_audio(self, audio_path: Path) -> Path:
        if self._ensure_8k is None:
            from .asr_local import ensure_8k_audio
            self._ensure_8k = ensure_8k_audio
        return self._ensure_8k(audio_path)

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            m = self._cfg.models
            self._model = WhisperModel(
                m.whisper_model, device=m.whisper_device, compute_type=m.whisper_compute_type,
            )
        return self._model

    def transcribe(self, audio_path: Path, language: str | None = None) -> List[ASRSegment]:
        audio = self._ensure_audio(audio_path)
        model = self._get_model()
        language = language or self._cfg.models.whisper_language
        log.info("ASR (faster-whisper %s) decoding %s", self._cfg.models.whisper_model, audio.name)
        segs_iter, _ = model.transcribe(
            str(audio), language=language,
            beam_size=1, best_of=1, vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400, "speech_pad_ms": 200},
            condition_on_previous_text=False, word_timestamps=False, chunk_length=15,
        )
        return [
            ASRSegment(
                start=float(s.start or 0.0),
                end=float(s.end or 0.0),
                text=(s.text or "").strip(),
                confidence=getattr(s, "avg_logprob", None),
            )
            for s in segs_iter
        ]


class GroqWhisperProvider:
    """Hosted Groq Whisper Large-v3-Turbo. Reads `GROQ_API_KEY` lazily."""

    name = "groq"
    DEFAULT_MODEL = "whisper-large-v3-turbo"
    ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or _api_key("GROQ_API_KEY")
        self._model = model or os.getenv("ASR_MODEL", self.DEFAULT_MODEL)
        if not self._api_key:
            raise RuntimeError(
                "Groq ASR selected but GROQ_API_KEY is not set. "
                "Set it in the environment, or switch ASR_PROVIDER."
            )

    def transcribe(self, audio_path: Path, language: str | None = None) -> List[ASRSegment]:
        import json
        import urllib.request

        log.info("ASR (Groq %s) uploading %s", self._model, audio_path.name)
        boundary = "----hoichoi"
        # Multipart body
        with open(audio_path, "rb") as fh:
            data = fh.read()
        body = (
            f"--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"model\"\r\n\r\n"
            f"{self._model}\r\n"
            f"--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"response_format\"\r\n\r\n"
            "verbose_json\r\n"
            f"--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\n"
            "Content-Type: audio/wav\r\n\r\n"
        ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            self.ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "hoichoi/0.1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Groq ASR failed: {exc}") from exc

        # Whisper verbose_json: { "segments": [ { start, end, text }, ... ], "language": "bn" }
        out: List[ASRSegment] = []
        for s in payload.get("segments") or []:
            try:
                out.append(
                    ASRSegment(
                        start=float(s.get("start", 0.0)),
                        end=float(s.get("end", 0.0)),
                        text=str(s.get("text", "")).strip(),
                        confidence=s.get("no_speech_prob"),
                    )
                )
            except Exception:
                continue
        if not out and payload.get("text"):
            out.append(ASRSegment(start=0.0, end=0.0, text=str(payload["text"]).strip()))
        log.info("Groq ASR returned %d segments", len(out))
        return out


class GeminiASRProvider:
    """Google Gemini multimodal fallback (audio / video understanding)."""

    name = "gemini"
    DEFAULT_MODEL = "gemini-3.5-transcribe"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or _api_key("GEMINI_API_KEY") or _api_key("GOOGLE_API_KEY")
        self._model = model or os.getenv("GEMINI_ASR_MODEL") or self.DEFAULT_MODEL
        if not self._api_key:
            raise RuntimeError(
                "Gemini ASR selected but GEMINI_API_KEY / GOOGLE_API_KEY is not set."
            )

    def transcribe(self, audio_path: Path, language: str | None = None) -> List[ASRSegment]:
        """Upload audio and ask Gemini for a Bengali transcript with timestamps."""
        import base64
        import json
        import urllib.request

        log.info("ASR (Gemini %s) decoding %s", self._model, audio_path.name)
        with open(audio_path, "rb") as fh:
            audio_b64 = base64.b64encode(fh.read()).decode("ascii")

        prompt = """Transcribe this audio in its original language (bn by default).
Return ONLY valid JSON of this shape:
{"segments":[{"start":<float seconds>,"end":<float seconds>,"text":<string>,"confidence":<float 0..1>}]}
No prose, no markdown, no code fences."""

        body = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
                ]
            }],
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
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Gemini ASR failed: {exc}") from exc

        text = (
            payload.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        try:
            parsed = json.loads(text)
        except Exception:
            log.warning("Gemini ASR returned non-JSON: %r", text[:200])
            return []
        out: List[ASRSegment] = []
        for s in parsed.get("segments", []):
            try:
                out.append(
                    ASRSegment(
                        start=float(s.get("start", 0.0)),
                        end=float(s.get("end", 0.0)),
                        text=str(s.get("text", "")).strip(),
                        confidence=s.get("confidence"),
                    )
                )
            except Exception:
                continue
        log.info("Gemini ASR returned %d segments", len(out))
        return out


# ----------------------------- Registry & public API -----------------------------

def _resolve_provider_name() -> str:
    """Pick a provider based on `ASR_PROVIDER` and available credentials."""
    explicit = os.getenv("ASR_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if _api_key("GROQ_API_KEY"):
        return "groq"
    if _api_key("GEMINI_API_KEY") or _api_key("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("ALLOW_LOCAL_ASR", "").strip().lower() in {"1", "true", "yes", "on"}:
        return "faster_whisper"  # explicit opt-in only
    return "mock"  # safe default — never makes a network call


@lru_cache(maxsize=1)
def get_provider(name: str | None = None) -> ASRProvider:
    """Return a cached provider instance.

    Resolution order:
      1. Explicit `ASR_PROVIDER` env.
      2. Auto-detect from credentials (`groq` > `gemini`).
      3. Local CPU fallback (`faster_whisper`) if allowed.
      4. `mock` for offline / tests.
    """
    chosen = (name or _resolve_provider_name()).lower()
    if chosen == "groq":
        return GroqWhisperProvider()
    if chosen == "gemini":
        return GeminiASRProvider()
    if chosen == "faster_whisper":
        return FasterWhisperProvider()
    if chosen == "mock":
        return MockASRProvider()
    raise ValueError(f"Unknown ASR provider: {chosen}")


def transcribe(audio_path: Path, language: str | None = None,
               provider_name: str | None = None) -> List[ASRSegment]:
    """Public entry point with configured fallback on provider failure.

    A transient Groq failure must not silently switch to local heavy inference.
    The configured `ASR_FALLBACK_PROVIDER` wins; local faster-whisper is used
    only when explicitly allowed.
    """
    try:
        provider = get_provider(provider_name)
    except RuntimeError as exc:
        log.warning("%s", exc)
        provider = None

    if provider is not None:
        try:
            return provider.transcribe(audio_path, language=language)
        except Exception as exc:  # noqa: BLE001
            log.warning("ASR provider %s failed: %s", provider.name, exc)

    fallback = os.getenv("ASR_FALLBACK_PROVIDER", "mock").strip().lower() or "mock"
    if fallback == "faster_whisper" and os.getenv("ALLOW_LOCAL_ASR", "").lower() not in {"1", "true", "yes", "on"}:
        log.warning("Ignoring faster_whisper fallback because ALLOW_LOCAL_ASR is false")
        fallback = "mock"
    if fallback == (provider.name if provider is not None else ""):
        fallback = "mock"
    try:
        return get_provider(fallback).transcribe(audio_path, language=language)
    except Exception as exc:  # noqa: BLE001
        log.error("ASR fallback %s failed: %s", fallback, exc)
        return []


def reset_for_tests() -> None:
    """Drop the cached provider instance — useful in unit tests."""
    get_provider.cache_clear()
