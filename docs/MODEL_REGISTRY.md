# Model registry — current hosted providers and local fallbacks

> Verified against the provider APIs and first-party model pages on 2026-09-26.
> All hard safety decisions remain deterministic Python.

| Layer | Production default | Fallback | Why |
| --- | --- | --- | --- |
| Bengali ASR | Groq `whisper-large-v3-turbo` | Gemini `gemini-3.5-transcribe`; local `faster-whisper tiny` only with `ALLOW_LOCAL_ASR=true` | Groq is the fast hosted Whisper path; Gemini is a current audio transcription model. |
| Vision | Gemini `gemini-2.5-flash-lite` | Gemini `gemini-3.1-flash-lite` or opt-in HF VLM | Current lightweight multimodal model; receives only bounded scene windows. |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | `shihab17/bangla-sentence-transformer` | Small CPU-local model used for brand ranking. |
| Shot detection | PySceneDetect `ContentDetector` | TransNetV2 if weights are deliberately added | Fast local cut detection. |

## Current provider model IDs

### Groq

Official production IDs relevant to this project:

- `whisper-large-v3-turbo` — speech transcription; selected default.
- `whisper-large-v3` — higher-cost Whisper alternative.
- `llama-3.1-8b-instant` — current text model for lightweight text tasks.
- `llama-3.3-70b-versatile` — current larger text model.
- `openai/gpt-oss-20b` and `openai/gpt-oss-120b` — current production text models.

This project does not use a Groq chat model for scene decisions. The scene and ad logic remains deterministic; Groq is used for ASR only.

### Gemini

The live Gemini API model listing currently exposes:

- `gemini-2.5-flash-lite` — selected vision default for low-latency bounded image windows.
- `gemini-3.1-flash-lite` — current alternative.
- `gemini-3.5-transcribe` — selected Gemini ASR fallback.
- `gemini-2.5-flash` — quality-oriented multimodal alternative.
- `gemini-embedding-001` — available embedding alternative, not used because brand embeddings stay local.

Do not use `gemini-2.0-flash`; the API reports it as shut down. Avoid unpinned `*-latest` aliases in production because they can change without a code commit.

## Configuration

```bash
VISION_PROVIDER=gemini
VISION_MODEL=gemini-2.5-flash-lite
ASR_PROVIDER=groq
ASR_MODEL=whisper-large-v3-turbo
ASR_FALLBACK_PROVIDER=gemini
GEMINI_ASR_MODEL=gemini-3.5-transcribe
ALLOW_LOCAL_ASR=false
```

Keys are read from environment variables and never stored in this document or logged.

## Sources

- Groq supported models: https://console.groq.com/docs/models
- Gemini models: https://ai.google.dev/gemini-api/docs/models
- Groq model listing endpoint: `https://api.groq.com/openai/v1/models`
- Gemini model listing endpoint: `https://generativelanguage.googleapis.com/v1beta/models`

## Hard constraints

Sentence-safety, active-dialogue protection, minimum-gap, maximum breaks per hour, maximum ad load, score threshold, and negative-context blocks remain Python-enforced in `pipeline/breaks.py` and `pipeline/brands.py`. Hosted models only provide transcription or bounded visual context.
