# Model registry — what we use, why, and how to swap

> All choices are **CPU-first**. No GPU is assumed anywhere.

| Layer       | Default (override via env)                                                       | Why                                                                                                           | Swap if…                                                              |
| ----------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| ASR (bn)    | `faster-whisper base` int8 (`WHISPER_MODEL`, `WHISPER_COMPUTE_TYPE`)              | `faster-whisper` runs Whisper via CTranslate2 — 4-5x faster than OpenAI Whisper. Bengali is `language="bn"`. | You have ≥ 16 GB RAM and 1 h+ of analysis time → bump to `small`.     |
| Embeddings  | `sentence-transformers/all-MiniLM-L6-v2` (`EMBEDDING_MODEL`)                       | 80 MB, 384-dim, 22 M params — most-used compact ST model.                                                     | Bengali-native semantics → `shihab17/bangla-sentence-transformer`.    |
| VLM         | `HuggingFaceTB/SmolVLM-Instruct` (256 M) (`HF_MODEL_VLM`)                         | Smallest credible VLM that accepts JSON-instruction prompts and runs in <2 GB on CPU.                        | You need richer descriptions → `vikhyatk/moondream2` (1.8 B).         |
| LLM rerank  | `google/flan-t5-small` (60 M) (`USE_LLM=1`, `HF_MODEL_LLM`)                       | Only an *optional* reranker for close brand candidates — **never** used for hard constraints.               | …you're sure you don't want it → leave `USE_LLM=0` (default).         |
| Shots       | PySceneDetect `ContentDetector`                                                    | Industry standard for fast content-aware cuts.                                                                | …you have transnetv2 weights → swap for `scenedetect`'s TransNetV2.   |
| Vision feats| OpenCV headless + Pillow                                                           | Zero extra deps, frame extraction only.                                                                       | n/a                                                                    |

## How these were chosen (research trail)

- **faster-whisper base int8**: Confirmed by the official `faster-whisper` README and
  Community benchmarks (CTranslate2 quantization gives the lowest memory ceiling while
  retaining Word Error Rate close to fp16).
- **SmolVLM-Instruct**: HF blog "Vision Language Models (Better, faster, stronger)" and
  the dedicated SmolVLM card recommend it as the best sub-2 B VLM for inference on
  consumer hardware.
- **shihab17/bangla-sentence-transformer**: Uddin et al., "Bangla SBERT – Sentence
  Embedding Using Multilingual Knowledge Distillation" (UEMCON 2024). Distilled from
  XLM-R, ~278 MB.
- **flan-t5-small**: A pure seq-to-seq model — explicit, reproducible, JSON-friendly.
  Picked deliberately to avoid the "general chat LLM" trap.

## Hard constraints still belong in deterministic Python

Even with a VLM available, sentence-safety, dialogue-active, minimum-gap, max-breaks-per-hour,
max-ad-load, and negative-context blocks remain Python-enforced. See
[`app/backend/pipeline/breaks.py`](../app/backend/pipeline/breaks.py) and
[`app/backend/pipeline/brands.py`](../app/backend/pipeline/brands.py).

## Tuning

Most users won't need to touch these. If you do:

```bash
export WHISPER_MODEL=small          # better Bengali accuracy
export EMBEDDING_MODEL=shihab17/bangla-sentence-transformer
export HF_MODEL_VLM=vikhyatk/moondream2
export USE_LLM=1
```
