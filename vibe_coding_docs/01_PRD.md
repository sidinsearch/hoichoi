# Product Requirements Document
## hoichoi Hackathon'26 — Context-Aware Video Segmentation & Intelligent Ad Placement

## 1. Product summary

Build a web application that ingests a long-form Bengali drama and the provided synthetic brand catalogue, understands the video using audio + visual + language signals, identifies semantically coherent scenes, finds natural advertising opportunities, determines whether each opportunity should actually be used, selects a contextually appropriate synthetic brand, and exposes the decisions through:

- `scenes.json`
- `debug.json`
- `vmap.xml`
- a live playable web demo

The web player must execute the generated break schedule without modifying the original episode file.

### Product sentence

> Understand the story, find a natural interruption boundary, decide whether an ad belongs there, select a safe/contextually relevant synthetic brand, and execute the decision in a live player.

---

## 2. Source requirements

The Participant Handbook defines Problem 1 as:

- ingest a long-form Bengali drama
- segment it into semantically coherent scenes
- score scene boundaries for safe interruption
- match surviving breaks to the most contextually appropriate brand
- emit a standards-compliant ad-break manifest
- provide a playable demo

The handbook explicitly frames the problem as:

### WHERE
Is this timestamp a natural, non-jarring place to cut? Mid-sentence cuts are heavily penalised.

### WHETHER
Is a break warranted at all, considering:
- maximum breaks/hour
- minimum gap
- ad-load percentage

### WHAT
Which brand creative belongs in this slot?
- dominant scene activity matters
- `negative_contexts` are hard blocks, not soft penalties

The MVP must generalise to a 9th unseen brand with zero code changes.

Held-out evaluation checks:
- mid-dialogue cuts
- blind-viewing scene quality
- negative-context brand violations

Auto-disqualifiers include:
- hard-coded timestamps
- hard-coded brand assignments
- negative-context violations
- non-live/non-working demo
- replacing synthetic brands with real company names

---

## 3. Goals

### G1 — Automatic semantic scene segmentation
Turn low-level shots + audio + visual evidence into coherent semantic scenes.

### G2 — Safe break detection
Find candidate boundaries and score them for interruption quality.

### G3 — Break eligibility
Apply deterministic pacing and safety rules.

### G4 — Contextual brand selection
Match each eligible break against the dynamic `brand.json`.

### G5 — Hard negative-context enforcement
A blocked brand must never be selected.

### G6 — Explainability
Every accepted/rejected break should have machine-readable reasons.

### G7 — Standards output
Generate a VMAP manifest representing the selected breaks.

### G8 — Real playback
The web player must actually pause the episode, display the virtual ad, wait for the selected duration, and resume.

### G9 — Generalisation
Adding Brand I to `brand.json` must not require code changes.

---

## 4. Non-goals

The MVP does NOT need:

- permanent editing/rendering of the source episode
- real ad video files
- ad creative generation
- a production ad-serving backend
- user authentication
- payments
- cloud media transcoding infrastructure
- microservices
- Kubernetes
- distributed queues
- a full analytics platform
- a full subtitle product

The ad creative is represented in the player by a dynamically generated black-screen ad card.

---

## 5. User flow

1. Open web application.
2. Upload/select Bengali episode.
3. Upload/select `brand.json`.
4. Click `Analyze Video`.
5. Backend runs the analysis pipeline.
6. UI displays processing progress.
7. Analysis completes.
8. UI shows:
   - number of scenes
   - number of break candidates
   - accepted breaks
   - blocked brands
9. User can view/download:
   - `scenes.json`
   - `debug.json`
   - `vmap.xml`
10. User plays the episode.
11. At generated timestamps, player pauses the original video.
12. Player shows:
   - `ADVERTISEMENT`
   - selected brand name
   - category
   - selected duration
   - optional context/reason
13. Player resumes the episode automatically.

---

## 6. Functional requirements

### FR-01 Video ingestion

Accept a supported video file and extract:
- duration
- frame rate
- audio stream
- resolution
- audio sample information

### FR-02 Bengali ASR

Produce timestamped Bengali transcript segments without manual correction.

Required information:
- text
- start
- end
- confidence where available

### FR-03 Audio analysis

Produce timeline signals including:
- speech activity
- silence
- pause duration
- sentence/utterance completion
- audio energy/intensity
- optional music/background-audio indicator

### FR-04 Shot detection

Detect low-level visual shot boundaries.

Shot boundaries are inputs to semantic scene construction, not final semantic scenes.

### FR-05 Visual analysis

Extract representative frames and infer:
- setting
- activities
- objects
- people count/roles where useful
- visual state
- coarse emotional/narrative context

### FR-06 Multimodal scene understanding

Fuse:
- transcript
- audio signals
- keyframes
- shot boundaries

into structured semantic scenes.

### FR-07 Break candidate generation

Generate candidate break points primarily around:
- scene boundaries
- shot transitions
- sentence completion
- dialogue pauses
- audio silence
- natural narrative transitions

### FR-08 Hard break filtering

Reject candidates when:
- inside a sentence
- active dialogue
- minimum gap violated
- max breaks/hour exceeded
- max ad-load exceeded
- strong interruption/emotional safety rule is violated

### FR-09 Break scoring

Score remaining candidates using configurable features such as:
- scene completion
- sentence completion
- dialogue pause
- audio silence
- visual transition
- visual stability
- emotional neutrality
- narrative independence

### FR-10 Brand loading

Load all brands dynamically from `brand.json`.

No brand-specific code.

### FR-11 Negative-context hard blocking

For every candidate:
1. derive scene context tags
2. compare against each brand's `negative_contexts`
3. immediately exclude blocked brands

Do not implement negative contexts as a numeric penalty.

### FR-12 Semantic brand matching

For eligible brands:
- compare scene context to target contexts
- use semantic embeddings
- optionally use an LLM/VLM-generated context representation
- rank eligible brands

Dominant scene activity should have strong influence.

### FR-13 Creative metadata selection

Choose an available duration from the selected brand metadata according to the project's configured duration policy.

No real creative file is required for playback.

### FR-14 VMAP generation

Generate `vmap.xml` from accepted break decisions.

### FR-15 Debug JSON

Generate detailed decision records.

### FR-16 Player execution

The player reads generated break data and performs virtual ad insertion without editing the source episode.

### FR-17 Download/view outputs

User can inspect and download all three generated files.

---

## 7. AI architecture

AI is core to the solution, not a bolt-on.

### Audio AI
Whisper/Bengali-capable ASR:
- speech recognition
- timestamps
- transcript evidence

Signal processing:
- silence
- pauses
- energy

### Vision AI
Vision model / VLM:
- setting
- activities
- objects
- visual context
- coarse emotional state

### LLM/VLM
Used for semantic fusion:
- combine transcript + visual observations + audio signals
- infer coherent scene context
- identify dominant activity
- produce structured JSON

### Embeddings
Sentence-transformers:
- represent scene context
- represent brand target contexts
- semantic similarity

### Deterministic engine
Python rules:
- hard break constraints
- pacing
- ad-load
- negative-context blocking
- creative duration validation
- playback schedule

The LLM must not be the sole authority for hard constraints.

---

## 8. Output contract

### `scenes.json`

Contains:
- scene id
- start/end
- constituent shots
- transcript summary
- context
- activities
- objects
- emotion/state
- confidence

### `debug.json`

Contains:
- every candidate or a configurable complete candidate audit
- accepted/rejected
- reasons
- score
- signals
- scene context
- blocked brands
- selected brand
- selected duration

### `vmap.xml`

Contains the accepted ad breaks and associated ad metadata in the agreed VMAP structure.

### Player

Consumes the generated decision data and produces:
`episode → virtual ad card → episode`

---

## 9. Success criteria

The MVP is successful when:

1. A new Bengali episode can be analyzed without timestamp editing.
2. Semantic scenes are generated automatically.
3. Mid-sentence/mid-dialogue opportunities are rejected.
4. Pacing constraints are enforced.
5. Negative-context brands are impossible to select.
6. Brand I can be added to JSON with no code change.
7. `scenes.json`, `debug.json`, and `vmap.xml` are generated.
8. The player executes selected breaks.
9. The source video is never permanently modified.
10. A judge can run the live demo.

---

## 10. Performance priorities

Given the solo 12-hour hackathon constraint:

Priority 1:
- correctness of break decisions
- negative-context safety
- playable demo

Priority 2:
- semantic scene quality
- explainability

Priority 3:
- UI polish

Avoid optimising infrastructure before the decision engine works.
