# hoichoi · Context-Aware Ad Intelligence

[![status](https://img.shields.io/badge/status-production--ready-4ade80)](#)
[![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Next.js%20%2B%20PyTorch--CPU-6c5ce7)](#)
[![python](https://img.shields.io/badge/python-3.11-3776ab)](#)
[![node](https://img.shields.io/badge/node-%E2%89%A520-339933)](#)
[![license](https://img.shields.io/badge/license-MIT-yellow)](#)

> **hoichoi Hackathon'26 — Problem 1**
>
> A semantic pipeline that turns a long-form Bengali drama into a brand-safe,
> standards-compliant ad-break schedule — **without ever modifying the source video**.

The system answers three questions for every ad-insertion opportunity:

| Question      | Means                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **WHERE**     | End of a semantic scene · completed sentence · dialogue pause · ≥ 1.5 s silence                                                    |
| **WHETHER**   | Deterministic pacing: ≥ 60 s before first break · ≥ 120 s gap · ≤ 4 breaks/h · ≤ 15 % ad-load · no emotional climax                 |
| **WHAT**      | MiniLM similarity against each brand's `target_contexts` — minus any brand whose `negative_contexts` match the scene              |

Adding a 9th brand to `brands.json` requires **zero** changes to Python or TypeScript. The UI automatically generates ad-pods and surfaces them inside the custom video player.

---

## 🏗️ Architecture & High-Availability Fallbacks

The backend is built to run on constrained hardware (1 CPU, 5GB RAM) without compromising analysis quality or crashing during API limits.

### Multi-Tier Vision Pipeline (VLM)
To extract visual context (setting, emotion, objects) without hitting a quota wall, we implemented a robust **latching multi-tier fallback chain**:
1. **Gemini (`gemini-3.5-flash-lite`)**: Primary extraction. If it hits an HTTP 429 quota limit, the backend instantly marks it exhausted for the entire process.
2. **OpenAI (`gpt-4o-mini`)**: Kicks in automatically. Extremely fast (~2s/frame) and cheap.
3. **Local VLM (`SmolVLM-256M`)**: Opt-in via `VISION_FALLBACK_PROVIDER=hf` (requires GPU/multi-core, ~140s/frame on 1 CPU).
4. **Deterministic Pixel Fallback**: The ultimate safety net. If all cloud APIs fail, it instantly (0.05s) calculates brightness, contrast, and color-cast from pixel data and extracts setting hints from the transcript. **Never hallucinated, never fails.**

### Speech-to-Text (ASR) & Translation
* **Groq (`whisper-large-v3-turbo`)**: Sub-second extraction of Bengali audio.
* **CPU Fallback (`faster-whisper`)**: Deterministic local fallback.
* **Auto-Translation**: Bengali ASR transcripts are safely translated to English (`text_en`) on a best-effort basis for English-first brand analysis while preserving the original Bengali captions.

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

## 🚀 Setup & Execution

### 1. Environment
Create a `.env` in the root folder:
```bash
# Core API Keys
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-proj-...

# Fallback Configuration
ALLOW_LOCAL_ASR=true
ASR_PROVIDER=groq
ASR_FALLBACK_PROVIDER=faster_whisper

# Vision Fallback Chain: gemini -> openai -> pixel -> mock
VISION_PROVIDER=gemini
OPENAI_VISION_MODEL=gpt-4o-mini
```

### 2. Start the Backend
```bash
# Creates .venv, installs deps, and starts uvicorn on port 8000
bash scripts/run_backend.sh
```
Health probe: `curl http://localhost:8000/api/health`

### 3. Start the Web UI
```bash
cd app/frontend
npm install
npm run build
npm start
# Runs on port 3000
```
If you open the UI from a different machine (e.g. tailscale), set `BACKEND_URL` in `app/frontend/.env.local` so the Next.js rewrite proxy follows.

### 4. Tests
The test suite (38 tests) enforces rule correctness (e.g., maximum breaks per hour, correct fallback chain triggering).
```bash
source app/backend/.venv/bin/activate
pytest tests/ -v
```

---

## ✅ Compliance with the handbook (auto-disqualifier checklist)

- [x] No hard-coded timestamps anywhere in code.
- [x] No hard-coded brand → activity mappings.
- [x] ASR runs automatically; no hand-corrected transcripts.
- [x] `negative_contexts` are **hard blocks** (set intersection in `pipeline/brands.py`), never soft penalties.
- [x] Source video is **never permanently modified** — the player renders the original file with a virtual ad overlay.
- [x] Synthetic brand names remain synthetic (`Brand A…H`, optionally `Brand I`).
- [x] Live demo works end-to-end (smoke test observed 25-30 s; 23-min episode observed ~6 min).
- [x] Generates all three required artifacts (`scenes.json`, `debug.json`, `vmap.xml`).

---

© 2026 hoichoi Hackathon'26 entry · MIT-licensed demo code