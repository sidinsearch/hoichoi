# Data Contracts

## 1. Job

```json
{
  "job_id": "uuid",
  "status": "queued|processing|completed|failed",
  "video_filename": "episode.mp4",
  "created_at": "ISO-8601"
}
```

---

## 2. Scene

```json
{
  "scene_id": "scene_001",
  "start_sec": 0.0,
  "end_sec": 142.4,
  "shot_ids": [1, 2, 3],
  "transcript": "...",
  "context": {
    "setting": "family home",
    "activities": ["conversation"],
    "objects": ["phone"],
    "emotion": "neutral",
    "narrative_state": "routine",
    "context_tags": ["family", "home", "conversation"]
  },
  "confidence": 0.88
}
```

---

## 3. Break candidate

```json
{
  "candidate_id": "candidate_014",
  "timestamp_sec": 842.4,
  "scene_id": "scene_007",
  "signals": {
    "scene_boundary": true,
    "sentence_complete": true,
    "dialogue_active": false,
    "audio_silence_sec": 1.7,
    "visual_transition": true,
    "emotional_intensity": 0.12
  },
  "hard_constraints": {
    "minimum_gap_ok": true,
    "hourly_limit_ok": true,
    "ad_load_ok": true
  },
  "score": 0.94,
  "decision": "accepted"
}
```

---

## 4. Brand decision

```json
{
  "brand_id": "brand_a",
  "display_name": "Brand A",
  "category": "food/spices/cooking",
  "semantic_score": 0.91,
  "eligible": true,
  "blocked_by": []
}
```

Blocked example:

```json
{
  "brand_id": "brand_d",
  "eligible": false,
  "blocked_by": ["hospital"]
}
```

---

## 5. Final break

```json
{
  "break_id": "break_001",
  "timestamp_sec": 842.4,
  "duration_sec": 20,
  "brand": {
    "brand_id": "brand_a",
    "display_name": "Brand A",
    "category": "food/spices/cooking"
  },
  "creative": {
    "creative_id": "a_20s_bn",
    "language": "bn",
    "duration_sec": 20
  },
  "score": 0.94
}
```

---

## 6. `scenes.json`

```json
{
  "schema_version": "1.0",
  "video": {
    "filename": "episode.mp4",
    "duration_sec": 1684.2
  },
  "scenes": []
}
```

---

## 7. `debug.json`

```json
{
  "schema_version": "1.0",
  "video": {
    "filename": "episode.mp4",
    "duration_sec": 1684.2
  },
  "candidates": [],
  "accepted_breaks": [],
  "summary": {
    "scene_count": 0,
    "candidate_count": 0,
    "accepted_count": 0
  }
}
```

---

## 8. `vmap.xml`

The generated XML must be well-formed and represent the accepted ad breaks.

Implementation must keep the VMAP generator isolated so the XML shape can be adjusted after validating against the chosen VMAP specification/library.

Do not fake standards compliance by merely naming an XML file `vmap.xml`.
