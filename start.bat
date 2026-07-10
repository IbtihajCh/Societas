@echo off
REM SOCIETAS - AMD Hackathon Act 2 Quick Start
REM Starts the backend server on port 8000

echo [Societas] Installing dependencies...
pip install -r backend/requirements.txt > nul 2>&1

echo [Societas] Starting server on http://localhost:8000 ...
echo [Societas] API docs at http://localhost:8000/docs
echo [Societas] Press Ctrl+C to stop.
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
