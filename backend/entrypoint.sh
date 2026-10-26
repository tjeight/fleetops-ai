#!/bin/sh
set -e

echo "[FleetOps Backend] Running Alembic migrations..."
alembic upgrade head

echo "[FleetOps Backend] Ingesting standard operating procedures (SOPs)..."
python -m app.retrieval.ingest

echo "[FleetOps Backend] Seeding initial demonstration incidents..."
python -m app.db.seed || echo "Seed data already present or skipped"

echo "[FleetOps Backend] Starting FastAPI server on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
