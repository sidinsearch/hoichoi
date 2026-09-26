# hoichoi Hackathon'26 — Context-Aware Ad Intelligence

This repository specification describes a compact, production-minded MVP for **Problem 1 — Context-Aware Video Segmentation & Intelligent Ad Placement**.

## Core idea

Input:

- A long-form Bengali drama video (`.mp4`)
- The provided synthetic `brand.json`

Output:

- `scenes.json` — semantic scene timeline
- `debug.json` — explainable break/brand decisions
- `vmap.xml` — generated ad-break manifest
- A live web player that uses those decisions to play:

`episode → virtual black-screen ad card → episode`

The source video is **never permanently edited**.

## Why this design

The handbook requires:

- semantic scene segmentation
- safe break scoring
- deciding whether a break should happen
- contextual brand matching
- hard negative-context blocking
- generalisation to a 9th unseen brand without code changes
- VMAP manifest
- debug JSON
- a playable demo that actually cuts to the ad and resumes

The system therefore separates:

1. AI perception and semantic understanding
2. deterministic hard constraints
3. semantic brand matching
4. manifest generation
5. client-side playback execution

## Recommended stack

Backend:
- Python
- FastAPI
- FFmpeg
- PySceneDetect
- Bengali-capable Whisper ASR
- OpenCV
- sentence-transformers
- configurable LLM/VLM provider
- Pydantic
- XML generation
- JSON/SQLite persistence

Frontend:
- React/Next.js
- HTML5 `<video>`
- Tailwind CSS or equivalent
- no unnecessary component complexity

## Important constraints

Do not:
- hard-code timestamps
- hard-code brand assignments
- use hand-corrected transcripts
- violate negative contexts
- permanently edit the episode as the core output
- require real ad creative files
- build microservices/Kubernetes for the MVP

The ad shown in the player is a **virtual black-screen ad card** populated dynamically from the selected brand information and selected duration metadata.

## Source

Primary source: hoichoi Hackathon'26 Participant Handbook, Problem 1, pages 4–5.
