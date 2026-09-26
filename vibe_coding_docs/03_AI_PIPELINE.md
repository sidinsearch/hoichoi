# AI / Multimodal Pipeline Specification

## Principle

Use AI for **understanding**.
Use deterministic code for **constraints and enforcement**.

Do not ask one model:
> "Watch this episode and tell me where to put ads."

Instead build evidence first.

---

## Stage 1 — Video preprocessing

Input:
`episode.mp4`

Extract:
- metadata
- normalized audio
- representative frames
- low-level shot boundaries

Output:
```json
{
  "duration_sec": 1684.2,
  "shots": [
    {"id": 1, "start": 0.0, "end": 8.2},
    {"id": 2, "start": 8.2, "end": 14.8}
  ]
}
```

---

## Stage 2 — Bengali ASR

Run a Bengali-capable Whisper implementation.

Output:
```json
{
  "segments": [
    {
      "start": 10.2,
      "end": 13.7,
      "text": "...",
      "confidence": 0.91
    }
  ]
}
```

ASR must be generated automatically. No hand-corrected transcript.

---

## Stage 3 — Audio feature extraction

Generate a timeline:
- speech_active
- silence
- pause duration
- energy
- optional music/background signal

Example:
```json
{
  "timestamp": 842.4,
  "speech_active": false,
  "silence_sec": 1.7,
  "audio_energy": 0.12
}
```

---

## Stage 4 — Sentence / utterance boundaries

Use ASR timestamps + punctuation/segmentation + pause structure.

We need a conservative signal:
- `sentence_complete`
- `dialogue_active`

If uncertain, prefer rejecting a break candidate.

---

## Stage 5 — Shot detection

Use PySceneDetect or equivalent.

Important:
- shot boundary != semantic scene boundary

Shots are evidence for semantic scene construction.

---

## Stage 6 — Visual context

Sample representative frames around each shot/scene.

VLM extracts:
- setting
- activity
- objects
- people
- visual context
- coarse emotional/narrative state

Example:
```json
{
  "setting": "family kitchen",
  "activities": ["cooking", "conversation"],
  "objects": ["spices", "food"],
  "emotion": "neutral"
}
```

---

## Stage 7 — Multimodal scene fusion

The LLM/VLM receives a bounded context package:

```json
{
  "time_range": [830.0, 845.0],
  "transcript": "...",
  "audio_signals": {
    "speech": true,
    "silence_before_end": 1.6
  },
  "shots": [
    {"start": 830, "end": 837},
    {"start": 837, "end": 842}
  ],
  "visual_observations": [
    {
      "setting": "family kitchen",
      "objects": ["phone", "food"]
    }
  ]
}
```

The model returns structured scene context:

```json
{
  "scene_type": "family conversation",
  "setting": "family kitchen",
  "dominant_activity": "cooking",
  "activities": ["cooking", "conversation"],
  "objects": ["phone", "food"],
  "emotion": "neutral",
  "narrative_state": "routine",
  "context_tags": [
    "family",
    "home",
    "cooking",
    "food"
  ]
}
```

Use structured output/schema validation.

---

## Stage 8 — Break candidate generation

Candidates should primarily be generated around:
- semantic scene endings
- shot transitions
- sentence completion
- dialogue pauses
- silence

Do not generate arbitrary timestamps every N seconds and ask the LLM to pick.

---

## Stage 9 — Hard filters

Example:

```python
def hard_filter(candidate, schedule):
    if candidate.inside_sentence:
        return False, "sentence_incomplete"

    if candidate.dialogue_active:
        return False, "dialogue_active"

    if schedule.gap_since_previous < MIN_GAP:
        return False, "minimum_gap"

    if schedule.breaks_in_hour >= MAX_BREAKS_PER_HOUR:
        return False, "max_breaks_per_hour"

    if schedule.ad_load_percent >= MAX_AD_LOAD:
        return False, "max_ad_load"

    return True, None
```

---

## Stage 10 — Break scoring

Suggested features:

```text
scene_completion
sentence_completion
dialogue_pause
audio_silence
shot_transition
visual_stability
emotional_safety
narrative_independence
```

Weights must be configurable.

Do not hard-code weights before testing on the actual supplied videos.

---

## Stage 11 — Brand safety

For every candidate:

```python
blocked = set(scene.context_tags) & set(brand.negative_contexts)

if blocked:
    brand.is_eligible = False
```

The exact matching implementation may use normalized tags, phrase matching and semantic expansion.

The important rule:

> negative_contexts are hard blocks.

---

## Stage 12 — Brand semantic ranking

Only eligible brands reach ranking.

Create a scene representation:

```text
family kitchen cooking food spices
```

Represent brand target contexts:

```text
cooking kitchen food spices seasoning
```

Use sentence-transformers similarity.

Optional LLM/VLM reranking can be used for close candidates, but deterministic hard blocks remain authoritative.

---

## Stage 13 — Unseen brand test

Adding:

```json
{
  "brand_id": "brand_i",
  "display_name": "Brand I",
  "category": "pet care",
  "target_contexts": ["dog", "cat", "pet", "vet"],
  "negative_contexts": ["funeral", "hospital", "violence"],
  "creatives": [...]
}
```

must require **zero Python code changes**.

---

## Stage 14 — Creative duration

No actual ad media is required.

Use creative metadata in `brand.json` to choose a duration according to a configurable policy.

For the MVP, the chosen duration drives the black-screen ad card.

---

## Stage 15 — Explainability

Every accepted break should expose:

- timestamp
- score
- scene
- audio evidence
- visual evidence
- hard-filter results
- selected brand
- blocked brands
- selected duration

Every rejected candidate should expose:
- timestamp
- rejected
- reasons

---

## Failure strategy

If AI output is invalid:
- validate schema
- retry once if appropriate
- otherwise mark uncertain
- do not silently invent context

If ASR confidence is poor:
- reduce confidence
- prefer conservative break rejection

If visual analysis is unavailable:
- use available audio/text signals but lower confidence
- never bypass hard negative rules.
