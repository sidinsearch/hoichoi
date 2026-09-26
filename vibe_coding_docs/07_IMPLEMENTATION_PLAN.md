# Implementation Plan

## Hackathon constraint

The handbook gives a 12-hour hackathon window. Build the smallest complete end-to-end system first.

## Phase 0 — 20 minutes

Create:
- repo
- FastAPI
- frontend
- environment configuration
- `/health`

Verify frontend ↔ backend.

---

## Phase 1 — 60 minutes

Implement:
- video upload
- brand JSON upload
- job creation
- result directory
- original video serving

Deliverable:
upload works.

---

## Phase 2 — 90 minutes

Implement audio pipeline:
- FFmpeg extraction
- Bengali Whisper
- speech intervals
- silence/energy
- sentence/utterance evidence

Deliverable:
timestamped transcript + audio signals.

---

## Phase 3 — 60 minutes

Implement:
- shot detection
- keyframe extraction

Deliverable:
shot timeline.

---

## Phase 4 — 90 minutes

Implement semantic scene builder:
- combine shots
- transcript windows
- representative frames
- VLM/LLM structured output

Deliverable:
`scenes.json`

Do not polish UI yet.

---

## Phase 5 — 90 minutes

Implement break engine:
- candidate generation
- hard constraints
- scoring

Deliverable:
accepted/rejected candidates in `debug.json`.

---

## Phase 6 — 60 minutes

Implement brand engine:
- load brand.json dynamically
- normalize contexts
- negative hard blocks
- embeddings
- brand ranking

Test with synthetic Brand I.

---

## Phase 7 — 45 minutes

Implement:
- creative duration choice
- VMAP generation

Deliverable:
`vmap.xml`

---

## Phase 8 — 90 minutes

Implement player:
- episode playback
- generated break markers
- break detection
- virtual black ad overlay
- countdown
- resume

This is mandatory.

---

## Phase 9 — 45 minutes

Implement artifact viewing/downloading and break detail UI.

---

## Phase 10 — 30 minutes

Held-out-style tests:
- mid-sentence
- dialogue
- funeral/grief
- hospital
- violence
- accident
- minimum gap
- max breaks/hour
- ad-load
- unseen Brand I

---

## Phase 11 — remaining time

Polish:
- loading states
- errors
- visual consistency
- demo flow
- README
- screenshots
- 5-minute explanation video

Do not sacrifice correctness for visual polish.

---

# Development order rule

Always maintain a runnable end-to-end path.

Preferred milestones:

```text
Upload → result
Upload → ASR
Upload → scenes.json
Upload → break decisions
Upload → brand decisions
Upload → VMAP
Upload → playable virtual ads
```

Never spend hours building isolated infrastructure.
