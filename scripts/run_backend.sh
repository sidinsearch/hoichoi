#!/usr/bin/env bash
# Run the backend. Always invoke from the repo root so `app.backend.main:app` resolves.
set -euo pipefail
cd "$(dirname "$0")/.."
source app/backend/.venv/bin/activate
exec uvicorn app.backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
