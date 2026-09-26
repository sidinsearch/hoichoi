# hoichoi · Context-Aware Ad Intelligence

[![status](https://img.shields.io/badge/status-hackathon--26-ff3b6b)](#)
[![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Next.js%20%2B%20PyTorch--CPU-6c5ce7)](#)
[![python](https://img.shields.io/badge/python-3.11-3776ab)](#)
[![node](https://img.shields.io/badge/node-%E2%89%A520-339933)](#)
[![license](https://img.shields.io/badge/license-MIT-yellow)](#)

> **hoichoi Hackathon'26 — Problem 1**
>
> A semantic pipeline that turns a long-form Bengali drama into a brand-safe,
> standards-compliant ad-break schedule — **without ever modifying the source video**.

The system answers three questions for every opportunity:

| Question      | Means                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **WHERE**     | End of a semantic scene · completed sentence · dialogue pause · ≥ 1.5 s silence                                                    |
| **WHETHER**   | Deterministic pacing: ≥ 120 s gap · ≤ 4 breaks/h · ≤ 15 % ad-load · no emotional climax                                             |
| **WHAT**      | MiniLM similarity against each brand's `target_contexts` — minus any brand whose `negative_contexts` match the scene              |

Adding a 9th brand to `brand.json` requires **zero** changes to Python or TypeScript. This is enforced by `tests/test_brands.py::test_unknown_brand_ingestion_zero_code_change`.

---

## 🎬 Demo flow (what the user sees)

```
[upload video] ──► [upload brands.json] ──► Analyze Video
                                              │
                                              ▼
                          ┌───────────────────────────────────────┐
                          │ 01 uploading                          │
                          │ 02 extracting_audio                   │
                          │ 03 transcribing_bengali               │
                          │ 04 detecting_shots                    │
                          │ 05 analyzing_visual_context           │
                          │ 06 building_scenes                    │
                          │ 07 finding_break_candidates           │
                          │ 08 applying_safety_rules              │
                          │ 09 matching_brands                    │
                          │ 10 generating_outputs                 │
                          │ 11 ready                              │
                          └───────────────────────────────────────┘
                                              │
                       ┌──────────────────────┼───────────────────────┐
                       ▼                      ▼                       ▼
                 scenes.json            debug.json                vmap.xml
              (semantic scenes)    (every candidate +      (VMAP 1.0 ad-break
                                    reasons)                  manifest)

            ┌─── next: play the episode ───►
            ▼
    <video> at 0.0s ──── @ break_001 ──── virtual ad card ──── resume
                       Brand A
                       food / spices
                       20s countdown
```

---

## 🏗 Architecture

```
                    video.mp4 + brand.json
                              │
                              ▼
              ┌───────────────────────────────┐
              │   FastAPI · /api/analyze       │   single Python process
              └─────────────┬─────────────────┘
                            │
              ┌─────────────▼─────────────────┐
              │     Orchestrator (thread)      │   background, persists status.json
              └─┬──────┬──────┬──────┬──────┬──┘
                │      │      │      │      │
                ▼      ▼      ▼      ▼      ▼
              ffmpeg   ASR   Shots  KeyFrm Brand
              probe    (bn)  PyScn  VLM*   load
                │      │      │      │      │
                └──────┴──────┴──────┴──────┘
                              │
                              ▼
                  Multimodal fusion (LLM-free)
                              │
                              ▼
                      Hard rules + scoring
                              │
                              ▼
                      Brand ranking + VMAP
                              │
                              ▼
       scenes.json · debug.json · vmap.xml · playback.json
                              │
                              ▼
                ┌───────────────────────────────┐
                │  Next.js · virtual ad player  │
                └───────────────────────────────┘
```

*The VLM is **opt-in**. Default path uses pure lexical fusion of BN↔EN keywords so the pipeline stays inside the **10 min / 40-min video** budget on a CPU laptop.

---

## 🧠 Models — hybrid fast/free, never a general chat LLM

| Layer        | Default (env override)                                                | Why                                                                                                  |
| ------------ | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| ASR (cloud)  | `Groq Whisper Large-v3-Turbo` (`ASR_PROVIDER=groq`, `ASR_MODEL=…`)   | Free tier, fastest Bengali/English; ~15-30 s for a 40-min episode. Set `GROQ_API_KEY`.               |
| ASR (cloud alt) | Gemini multimodal ASR (`ASR_FALLBACK_PROVIDER=gemini`)             | Used if Groq is rate-limited or creds absent.                                                        |
| ASR (local)  | `faster-whisper tiny` int8 (`ALLOW_LOCAL_ASR=true`)                  | Last-resort CPU fallback. RTF ≈ 0.23 on a 23-min episode → ~5.4 min total.                          |
| Shots        | PySceneDetect `ContentDetector`                                       | Industry-standard content-aware cut detector. Shots are *evidence*, never final scenes.               |
| Vision (cloud) | Google Gemini multimodal (`VISION_PROVIDER=gemini`, `VISION_MODEL=gemini-3.8-flash`) | Sends **bounded windows** (≤4 JPEGs + transcript slice), never the full video. Free tier. |
| Vision (local opt-in) | Florence-2 / Moondream2 / SmolVLM (`VISION_PROVIDER=hf`)     | Opt-in. Off by default — defeats the budget otherwise.                                              |
| Embeddings   | `sentence-transformers/all-MiniLM-L6-v2`                             | 80 MB, 384-dim. Tiny CPU cost; used only for brand-context ranking.                                  |
| LLM rerank   | `google/flan-t5-small` 60M (`USE_LLM=1`)                              | Seq-to-seq, never used for hard rules. Opt-in.                                                       |
| **Hard rules** | **Custom Python** (`pipeline/breaks.py`, `brands.py`)               | **Authoritative for safety.** The LLM never overrides sentence/dialogue/gap/negative-context rules.   |

See [`docs/MODEL_REGISTRY.md`](docs/MODEL_REGISTRY.md) for the full research trail, alternatives, and swap instructions. **API keys are never stored on dataclasses or logged.** Set them in `.env` and they resolve transparently.

---

## ⚙️ Quick start

### Backend (binds `0.0.0.0:8000` so LAN/tailscale can reach it)

```bash
cd hoichoi
python3 -m venv app/backend/.venv
source app/backend/.venv/bin/activate
pip install -r app/backend/requirements.txt
bash scripts/run_backend.sh        # → http://0.0.0.0:8000
```

Health probe: `curl http://localhost:8000/api/health`  →  `{"status":"ok",…}`

### Frontend

```bash
cd hoichoi/app/frontend
npm install
npm run dev                        # → http://localhost:3000
```

If you open the UI from a different machine (e.g. tailscale), set `BACKEND_URL` so the Next.js rewrite proxy follows:

```bash
# app/frontend/.env.local
BACKEND_URL=http://100.104.222.121:8000   # this box's tailscale IP
```

Then visit `http://100.104.222.121:3000`.

### End-to-end via curl

```bash
curl -F video=@test_assets/smoke.mp4 \
     -F brand_json=@resources/brands.json \
     http://127.0.0.1:8000/api/analyze

# poll status
curl http://127.0.0.1:8000/api/jobs/<job_id>

# download artifacts
curl -OJ http://127.0.0.1:8000/api/jobs/<job_id>/scenes
curl -OJ http://127.0.0.1:8000/api/jobs/<job_id>/debug
curl -OJ http://127.0.0.1:8000/api/jobs/<job_id>/vmap
curl -OJ http://127.0.0.1:8000/api/jobs/<job_id>/playback
```

---

## 🔧 Configuration (env vars)

| Var                       | Default                                  | Effect                                                              |
| ------------------------- | ---------------------------------------- | ------------------------------------------------------------------- |
| `WHISPER_MODEL`           | `tiny`                                   | `tiny`/`base`/`small`/`medium`                                      |
| `WHISPER_LANGUAGE`        | `bn`                                     | ASR language (force Bengali to avoid detect-on-every-call overhead) |
| `WHISPER_COMPUTE_TYPE`    | `int8`                                   | `int8`/`float16`/`float32`                                          |
| `ASR_BACKEND`             | `faster_whisper`                         | `distil` for English-only 5-6× speedup                              |
| `EMBEDDING_MODEL`         | `sentence-transformers/all-MiniLM-L6-v2` | Any sentence-transformers or HF model                               |
| `HF_MODEL_VLM`            | *(empty)*                                | Set to `HuggingFaceTB/SmolVLM-Instruct` to enable vision            |
| `USE_LLM`                 | `0`                                      | `1` enables `flan-t5-small` reranker                                |
| `MAX_KEYFRAMES`           | `12`                                     | Visual pipeline budget                                               |
| `MIN_GAP_SECONDS`         | `120`                                    | Min seconds between accepted breaks                                 |
| `MAX_BREAKS_PER_HOUR`     | `4`                                      | Pacing cap                                                           |
| `MAX_AD_LOAD_PERCENT`     | `15`                                     | Target total ad time over episode                                   |
| `BREAK_SCORE_THRESHOLD`   | `0.55`                                   | Candidate acceptance cutoff                                         |
| `JOB_STORAGE_DIR`         | `data/jobs`                              | Where artifacts land                                                 |

---

## 📦 Repository layout

```
hoichoi/
├── app/
│   ├── backend/                       FastAPI · Pydantic v2
│   │   ├── config.py                  tunables + per-model rationale
│   │   ├── main.py                    FastAPI entry, /api/health
│   │   ├── api/                       routes_analysis, routes_results
│   │   ├── models/schemas.py          Pydantic contracts (Brand, Scene, …)
│   │   ├── services/                  asr.py, embeddings.py, vlm.py,
│   │   │                              ffmpeg.py, player_state.py
│   │   └── pipeline/                  audio.py, shots.py, vision.py,
│   │                                  scenes.py, breaks.py, brands.py,
│   │                                  outputs.py, orchestrator.py
│   └── frontend/                      Next.js 14 + Tailwind
│       ├── app/page.tsx               single page, polls backend
│       ├── components/                Header, Hero, HowItWorks,
│       │                              FeatureGrid, UploadPanel,
│       │                              ResultsPanel, ProgressPanel,
│       │                              VideoPlayer, BreakDetails,
│       │                              ArtifactCards, TranscriptPanel,
│       │                              Footer
│       └── lib/playback.ts            browser-side state machine
├── tests/                             13 pytest tests · all green
├── docs/
│   ├── MODEL_REGISTRY.md              per-model picks + research trail
│   └── vibe_coding_docs/              original spec (verbatim)
├── scripts/
│   ├── run_backend.sh                 binds 0.0.0.0:8000
│   └── check_no_hardcodes.py          CI guard
├── resources/brands.json              8-brand synthetic catalogue
└── test_assets/                       gitignored smoke slice
```

---

## 🧪 Tests & CI guards

```bash
cd hoichoi
source app/backend/.venv/bin/activate
python -m pytest tests/ -q                 # 13 passed
python scripts/check_no_hardcodes.py      # 0 anti-patterns
```

What's covered:

| Test class           | Asserts                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------- |
| `test_brands`        | positive matching · hard-negative blocks · hospital-specific blocks · Brand I ingest    |
| `test_breaks`        | mid-sentence reject · dialogue-active reject · 120 s gap · 4/h cap · emotional climax · score bounded [0,1] |
| `test_outputs`       | VMAP XML well-formed and contains `AdBreak id=break_001`                               |
| `test_player`        | state-machine: break fired · consumed (no re-fire) · countdown · completion            |

`check_no_hardcodes.py` fails the build if any Python file contains:

- a literal `if timestamp == <number>`
- a literal `if activity == "…": return "brand_…"`
- any `score -= 0.<n>` (soft-penalty scoring is forbidden — negative_contexts must be hard blocks).

---

## ✅ Compliance with the handbook (auto-disqualifier checklist)

- [x] No hard-coded timestamps anywhere in code.
- [x] No hard-coded brand → activity mappings.
- [x] ASR runs automatically; no hand-corrected transcripts.
- [x] `negative_contexts` are **hard blocks** (set intersection in `pipeline/brands.py`), never soft penalties.
- [x] Source video is **never permanently modified** — the player renders the original file with a virtual ad overlay.
- [x] Synthetic brand names remain synthetic (`Brand A…H`, optionally `Brand I`).
- [x] Live demo works end-to-end (smoke test observed 25-30 s; 23-min episode observed ~6 min; 40-min budget ≤ 10 min).
- [x] Adding a 9th brand to `brand.json` requires zero code changes — covered by `test_unknown_brand_ingestion_zero_code_change`.
- [x] Generates all three required artifacts (`scenes.json`, `debug.json`, `vmap.xml`).

---

## 📊 Observed performance (CPU laptop)

| Episode length         | Stages                                            | Wall-clock          |
| ---------------------- | ------------------------------------------------- | ------------------- |
| 30 s smoke clip        | everything (no VLM, `tiny`)                       | **~25-30 s**        |
| 23 min (`mohanagar`)   | ffmpeg probe + ASR (tiny) + scenes + brands + VMAP | **~6 min**          |
| 40 min (projected)     | extrapolated from 23-min measurement              | **≤ 10 min budget** |

---

## 🌐 Network access

The backend binds `0.0.0.0:8000` so it is reachable from anywhere on your LAN or tailscale network:

| Where                | URL                              |
| -------------------- | -------------------------------- |
| Same machine         | `http://localhost:8000`          |
| Same machine, IP     | `http://127.0.0.1:8000`          |
| LAN / tailscale      | `http://<this-host-ip>:8000`     |
| Frontend default     | `http://localhost:3000`          |

To find this host's tailscale IP: `tailscale ip -4` or `ip -4 addr show tailscale0`.

---

## 🛠 Troubleshooting

- **`ffmpeg not found`** — install via your OS package manager; the backend's `/api/health` will still return 200 but pipeline stages will fail. Check `/tmp/hoichoi-uvicorn.log` for `FileNotFoundError`.
- **`No module named 'app'`** when launching uvicorn — always run from repo root, or use `bash scripts/run_backend.sh` which handles this.
- **`Port 8000 already in use`** — `lsof -i :8000` and kill the stray process, or `PORT=8001 bash scripts/run_backend.sh`.
- **VLM too slow** — leave `HF_MODEL_VLM` empty (the default) and rely on lexical fusion. Anything more than 12 small-keyframe inferences on CPU will not finish in budget.
- **Sentence segments look noisy** — bump `WHISPER_MODEL=base` (still fits in RAM, ~3× slower) or `small` if you have ≥ 8 GB free.

---

## 📚 References

- Hoichoi Hackathon'26 Participant Handbook, Problem 1 (the canonical problem statement).
- Florence-2: Microsoft, 2023.
- SmolVLM: Hugging Face, 2025.
- Distil-Whisper: Gandhi et al., 2023 ("Robust Knowledge Distillation via Large-Scale Pseudo-Labelling").
- shihab17/bangla-sentence-transformer: Uddin et al., UEMCON 2024.
- Faster-Whisper: Systran, 2024 — CTranslate2 backend.

---

© 2026 hoichoi Hackathon'26 entry · MIT-licensed demo code
