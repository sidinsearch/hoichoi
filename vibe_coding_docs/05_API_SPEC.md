# API Specification

## Base

`/api`

---

## POST `/api/analyze`

Multipart form:
- `video`: video file
- `brand_json`: JSON file

Response:

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

---

## GET `/api/jobs/{job_id}`

Response:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "artifacts": {
    "scenes": "/api/jobs/abc123/scenes",
    "debug": "/api/jobs/abc123/debug",
    "vmap": "/api/jobs/abc123/vmap"
  }
}
```

---

## GET `/api/jobs/{job_id}/scenes`

Returns `scenes.json`.

---

## GET `/api/jobs/{job_id}/debug`

Returns `debug.json`.

---

## GET `/api/jobs/{job_id}/vmap`

Returns `vmap.xml`.

---

## GET `/api/jobs/{job_id}/video`

Streams the original episode.

---

## GET `/api/jobs/{job_id}/playback`

Returns only the player-relevant break schedule.

Example:

```json
{
  "video_url": "/api/jobs/abc123/video",
  "breaks": [
    {
      "id": "break_001",
      "timestamp_sec": 842.4,
      "duration_sec": 20,
      "brand_id": "brand_a",
      "display_name": "Brand A",
      "category": "food/spices/cooking"
    }
  ]
}
```

---

## GET `/api/health`

Returns:

```json
{
  "status": "ok"
}
```

---

## Processing model

MVP may use background execution inside the same application process.

Do not add Celery/Redis unless actual runtime needs justify it.
