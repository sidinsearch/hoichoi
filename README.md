# hoichoi — Context-Aware Video Segmentation & Intelligent Ad Placement

> **hoichoi Hackathon'26 — Problem 1**
>
> Input: a long-form Bengali drama + a synthetic `brand.json`.
> Output: `scenes.json` • `debug.json` • `vmap.xml` • a playable web demo that executes the generated breaks against the **original, unmodified** episode via a virtual black-screen ad card.

The system answers three questions for every ad opportunity:

- **WHERE** is it safe to interrupt (no mid-sentence cuts, no active dialogue)?
- **WHETHER** should a break happen at all (pacing, density, ad-load)?
- **WHAT** brand belongs there (contextual, never violating a `negative_context`)?

Adding a 9th brand to `brand.json` works without changing a single line of Python or TypeScript.

---

## Architecture (one process)

```
   video.mp4 + brand.json
            │
   ┌────────▼─────────┐
   │     FastAPI      │   POST /api/analyze, GET /api/jobs/{id}/*
   └────────┬─────────┘
            │
   ┌────────▼─────────┐
   │   Orchestrator   │   one async job in-process
   └──┬─────┬─────┬───┘
      │     │     │
      ▼     ▼     ▼
   audio  shots  vision       ← faster-whisper (bn), PySceneDetect, OpenCV
      │     │     │
      └─────┼─────┘
            ▼
       Multimodal
      scene fusion         ← local VLM (Moondream2 / Florence-2) for visual cues
            │
            ▼
      Break candidates     ← deterministic rules
            │
            ▼
      Brand engine         ← embeddings (sentence-transformers-MiniLM)
            │
            ▼
   scenes.json • debug.json • vmap.xml
            │
            ▼
      Web player           ← Next.js + HTML5 video, virtual ad overlay
```

No microservices, no Redis/Celery, no Kubernetes, no cloud GPU. Runs on a laptop.

## Stack

| Layer       | Choice                                                              |
| ----------- | ------------------------------------------------------------------- |
| Backend     | Python 3.11, FastAPI, Pydantic                                      |
| ASR         | faster-whisper (`base` int8 Bengali, CPU)                           |
| Shots       | PySceneDetect `ContentDetector`                                     |
| Vision      | OpenCV keyframes + optional local **Florence-2-base** or **Moondream2** via `transformers` |
| Scene fusion| Lightweight rule + lexical fusion (LLM-free path); optional HF `flan-t5-small` for richer scenes |
| Embeddings  | `sentence-transformers/all-MiniLM-L6-v2` (CPU)                      |
| Audio feats | librosa (RMS energy, silence) + Whisper pause decoding              |
| Frontend    | Next.js 14 (App Router), React, Tailwind                            |
| Player      | HTML5 `<video>` + reactive state machine                           |
| Manifest    | VMAP 1.0 (custom lxml serializer, isolated module)                  |

The default pipeline ships **LLM-free**: a fast multimodal heuristic (transcript + audio cues + visual tags) drives scene understanding. If `HF_TOKEN` and `USE_LLM=1` are set, a small HF `flan-t5-small` reranks scene candidates — keeping the "no general chat LLM" rule.

## Quick start

### 1. Backend

```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd app/frontend
npm install
npm run dev
# open http://localhost:3000
```

Open the UI → upload an `.mp4` and `brand.json` → **Analyze Video** → play with breaks.

## Environment variables

All optional; defaults are sensible.

| Var                 | Default                                  | Purpose                              |
| ------------------- | ---------------------------------------- | ------------------------------------ |
| `WHISPER_MODEL`     | `base`                                   | faster-whisper size                  |
| `WHISPER_DEVICE`    | `cpu`                                    | `cpu` or `cuda`                      |
| `EMBEDDING_MODEL`   | `sentence-transformers/all-MiniLM-L6-v2` | brand/scene embeddings               |
| `HF_MODEL_VLM`      | `microsoft/Florence-2-base`              | local VLM (set empty to disable)     |
| `USE_LLM`           | `0`                                      | `1` enables HF `flan-t5-small` rerank|
| `HF_TOKEN`          | (none)                                   | Hugging Face token for gated models  |
| `MIN_GAP_SECONDS`   | `120`                                    | pacing                               |
| `MAX_BREAKS_PER_HOUR` | `4`                                    | pacing                               |
| `MAX_AD_LOAD_PERCENT` | `15`                                   | pacing (target share)                |
| `BREAK_SCORE_THRESHOLD` | `0.55`                                | acceptance cutoff                    |
| `JOB_STORAGE_DIR`   | `data/jobs`                              | where artifacts land                 |

## Repository layout

```
app/
├── backend/
│   ├── main.py                 # FastAPI entry
│   ├── api/
│   │   ├── routes_analysis.py
│   │   └── routes_results.py
│   ├── pipeline/
│   │   ├── orchestrator.py
│   │   ├── preprocess.py
│   │   ├── audio.py
│   │   ├── vision.py
│   │   ├── shots.py
│   │   ├── scenes.py
│   │   ├── breaks.py
│   │   ├── brands.py
│   │   └── outputs.py
│   ├── models/                 # Pydantic
│   └── services/               # asr, llm, embeddings, ffmpeg wrappers
├── frontend/
│   ├── app/page.tsx
│   ├── components/             # UploadPanel, VideoPlayer, Timeline, BreakDetails, ResultsPanel
│   └── lib/playback.ts
data/jobs/                      # per-job artifacts (gitignored)
resources/                      # sample videos/brands.json (gitignored)
tests/                          # pytest
scripts/                        # helper scripts
docs/                           # the original vibe_coding_docs (kept verbatim)
```

## Tests

```bash
cd app/backend
pytest -q
```

Tests cover: brand hard-blocks, mid-sentence rejection, unknown brand ingestion, VMAP well-formedness, deterministic scoring.

## Compliance (anti-disqualifier checklist)

- ❌ no hard-coded timestamps
- ❌ no hard-coded brand assignments
- ❌ no hand-corrected transcripts
- ❌ no negative-context violations
- ❌ no real-company brand substitution
- ✅ source video never permanently modified
- ✅ live demo runs end-to-end
- ✅ adding Brand I → zero code changes

See [`docs/vibe_coding_docs/`](docs/vibe_coding_docs/) for the original specification.
