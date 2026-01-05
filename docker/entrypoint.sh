#!/bin/bash
set -e

echo "[$(date +'%Y-%m-%d %H:%M:%S')] PromoPulse API starting..."
echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running database migrations..."

alembic upgrade head

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Migrations completed successfully"
echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting FastAPI application..."

exec uvicorn promopulse.app.main:app --host 0.0.0.0 --port 8000
