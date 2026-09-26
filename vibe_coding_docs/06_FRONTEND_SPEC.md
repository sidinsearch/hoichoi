# Frontend Specification

## Single-page application

Sections:

1. Header
2. Input panel
3. Analysis progress
4. Results summary
5. Artifact cards
6. Video player
7. Timeline
8. Break details

---

## Input panel

Fields:
- video upload
- brand.json upload

Primary CTA:
`Analyze Video`

---

## Progress panel

Display real stages:

```text
Uploading
Extracting audio
Transcribing Bengali
Detecting shots
Analyzing visual context
Building scenes
Finding break candidates
Applying safety rules
Matching brands
Generating outputs
Ready
```

Do not fake progress.

---

## Results panel

Show:

```text
Scenes detected       18
Candidates            42
Accepted breaks        4
Blocked brand matches  9
```

Numbers come from actual output.

---

## Artifact cards

Three cards:

### scenes.json
Buttons:
- View
- Download

### debug.json
Buttons:
- View
- Download

### vmap.xml
Buttons:
- View
- Download

---

## Player

Use HTML5 video.

The player receives:
- original video URL
- generated break schedule

Break behavior:

```text
if currentTime >= break.timestamp and break not consumed:
    pause video
    show virtual ad overlay
    wait break.duration
    hide overlay
    resume video
```

Use a small threshold to account for browser time-update granularity.

Example:
`currentTime >= timestamp - 0.15`

---

## Virtual ad overlay

Black background.

Display:

```text
ADVERTISEMENT

Brand A
Food / Spices / Cooking

20 seconds

Contextually selected for:
Family cooking
```

Optional:
- countdown
- progress bar

No real ad creative is required.

---

## Timeline

Render accepted breaks as markers.

Clicking a marker:
- seeks to just before the break
- opens the break details panel

---

## Break details

Show:
- timestamp
- score
- scene context
- audio signals
- visual signals
- selected brand
- selected duration
- blocked brands/reasons

---

## UX principles

- simple
- fast
- no dashboard bloat
- judges should understand the system in under 30 seconds
- never hide why an ad appeared
