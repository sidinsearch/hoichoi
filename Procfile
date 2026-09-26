# Stage 0 — backend service on port 8000.
Hoichoi-Backend:
  stage: backend
  description: FastAPI service for the hoichoi video analysis pipeline.
  command: uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
  directory: app/backend
  ports:
    - 8000
