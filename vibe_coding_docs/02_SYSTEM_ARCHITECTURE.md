# System Architecture

## 1. High-level architecture

```text
                  USER
                   |
          video.mp4 + brand.json
                   |
                   v
            +-------------+
            |   FastAPI   |
            +------+------+
                   |
                   v
          Analysis Orchestrator
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
    Video        Audio       Shots
   pipeline     pipeline    pipeline
       |           |           |
       +-----------+-----------+
                   |
                   v
           Multimodal Context
              / LLM / VLM
                   |
                   v
          Semantic Scene Timeline
                   |
                   v
          Break Candidate Engine
                   |
                   v
          Deterministic Hard Rules
                   |
                   v
            Safe Candidates
                   |
                   v
          Brand Safety Filter
                   |
                   v
         Semantic Brand Ranking
                   |
                   v
          Creative Duration Choice
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
 scenes.json   debug.json   vmap.xml
                               |
                               v
                         Web Player
                               |
                    episode -> ad -> episode
```

---

## 2. Components

### API server

Responsibilities:
- upload files
- create analysis job
- expose job status
- expose generated artifacts
- serve media
- validate requests

Recommended framework: FastAPI.

### Analysis orchestrator

One Python process coordinating:
- preprocessing
- ASR
- shot detection
- keyframe extraction
- VLM/LLM calls
- scene construction
- break decisions
- brand matching
- output generation

Do not split into microservices.

### Media preprocessing

FFmpeg:
- audio extraction
- normalized audio
- keyframe extraction
- media metadata

### Audio analyzer

Produces:
- ASR segments
- speech intervals
- silence intervals
- pause durations
- energy

### Shot analyzer

PySceneDetect or equivalent:
- shot start/end
- transition type if available

### Visual analyzer

Representative frames only.

Avoid sending every frame to a vision model.

### Context fusion

The model receives a bounded context window:
- nearby keyframes
- transcript
- audio features
- shot boundaries

It outputs strict structured JSON.

### Break engine

Generates candidate boundaries, applies hard filters, then scores survivors.

### Brand engine

Loads `brand.json`, blocks negatives, then ranks eligible brands semantically.

### Output generator

Writes:
- scenes.json
- debug.json
- vmap.xml

### Playback engine

Frontend HTML5 video + React state machine.

---

## 3. Playback state machine

```text
PLAYING
  |
  | currentTime reaches break.timestamp
  v
PAUSED_FOR_AD
  |
  v
SHOW_VIRTUAL_AD
  |
  | duration elapsed
  v
RESUME_EPISODE
  |
  v
PLAYING
```

Important:
- seek behavior must not accidentally retrigger an already-consumed break
- maintain a `consumedBreakIds` set
- handle play/pause safely
- tolerate small timestamp drift

---

## 4. No source-video editing

The system stores:

```text
original episode.mp4
```

unchanged.

The ad experience is a UI overlay/card.

Optional future feature:
- actual ad video support

But it is not required for MVP.

---

## 5. Suggested directory structure

```text
app/
├── backend/
│   ├── main.py
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
│   ├── models/
│   │   ├── scene.py
│   │   ├── break.py
│   │   └── brand.py
│   └── services/
│       ├── asr.py
│       ├── llm.py
│       ├── embeddings.py
│       └── ffmpeg.py
│
├── frontend/
│   ├── app/
│   ├── components/
│   │   ├── UploadPanel
│   │   ├── ResultsPanel
│   │   ├── VideoPlayer
│   │   ├── Timeline
│   │   └── BreakDetails
│   └── lib/
│
├── data/
│   └── jobs/
│
├── tests/
└── docs/
```
