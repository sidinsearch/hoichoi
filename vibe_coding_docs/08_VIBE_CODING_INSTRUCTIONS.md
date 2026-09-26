# Vibe Coding / Coding Agent Instructions

You are implementing the hoichoi Hackathon'26 Problem 1 MVP.

## Product

Input:
- Bengali drama video
- synthetic `brand.json`

Outputs:
- scenes.json
- debug.json
- vmap.xml
- playable web experience

The source video is not permanently edited.

The player renders a virtual black-screen ad card using the selected brand metadata.

---

## Non-negotiable rules

### 1. No hard-coded timestamps

Never write:
```python
if timestamp == 842:
```

All break timestamps must be generated from analysis.

### 2. No hard-coded brand mappings

Never write:
```python
if activity == "cooking":
    return "brand_a"
```

Brands must come from `brand.json`.

### 3. Negative contexts are hard blocks

Never:
```python
score -= 0.2
```

Instead:
```python
if blocked:
    exclude_brand()
```

### 4. No hand-corrected transcript

All transcript evidence must come from the automatic ASR pipeline.

### 5. LLM does not enforce hard constraints

The model can provide semantic evidence.
Python rules enforce:
- sentence/dialogue safety
- pacing
- ad-load
- negative context

### 6. Do not edit the source video

The player performs virtual insertion.

### 7. Keep interfaces stable

Use Pydantic models between pipeline stages.

### 8. Fail conservatively

If a candidate is uncertain:
- lower confidence
- reject the candidate if safety cannot be established

Never invent a safe break.

### 9. Structured AI output

LLM/VLM output must be schema validated.

Do not parse arbitrary prose.

### 10. No unnecessary infrastructure

Avoid:
- Kubernetes
- microservices
- Redis
- Celery
- message brokers
- cloud orchestration

unless a real implementation problem requires them.

---

## Coding style

Prefer:
- small modules
- typed Python
- explicit models
- deterministic functions
- testable pure decision functions
- environment variables for API keys
- structured logging

Avoid:
- giant `pipeline.py`
- hidden global state
- magic constants
- provider-specific logic everywhere

---

## Configuration

Put tunable values in one config:

```text
MIN_GAP_SECONDS
MAX_BREAKS_PER_HOUR
MAX_AD_LOAD_PERCENT
BREAK_SCORE_THRESHOLD
ASR_MODEL
EMBEDDING_MODEL
LLM_MODEL
VLM_MODEL
```

Do not bury them inside functions.

---

## AI provider abstraction

Implement interfaces like:

```python
class ASRProvider:
    def transcribe(...): ...

class VisionProvider:
    def analyze(...): ...

class LLMProvider:
    def analyze_scene(...): ...

class EmbeddingProvider:
    def embed(...): ...
```

This allows changing providers without rewriting the pipeline.

---

## Definition of a good implementation

A judge can:

1. open the app
2. upload video
3. upload brand.json
4. click Analyze
5. wait for real processing
6. inspect scenes.json
7. inspect debug.json
8. inspect vmap.xml
9. press play
10. see a generated ad break
11. see the selected brand
12. see playback resume

If all twelve work, the MVP is complete.
