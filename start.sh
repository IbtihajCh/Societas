#!/usr/bin/env bash
# SOCIETAS - AMD Hackathon Act 2 Quick Start
# Starts the backend server on port 8000

set -e

echo "[Societas] Installing dependencies..."
pip install -r backend/requirements.txt -q

echo "[Societas] Starting server on http://localhost:8000 ..."
echo "[Societas] API docs at http://localhost:8000/docs"
echo "[Societas] Press Ctrl+C to stop."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
