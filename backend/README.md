# Backend API

FastAPI REST API bridging the frontend dashboard to the simulation engine and SQLite persistence.

## Key Files

- `app/main.py` — App factory, lifespan, WebSocket endpoint
- `app/routers/` — HTTP route handlers (simulation, policies, agents, metrics)
- `app/services/` — Orchestrators (Simulation, Policy, Agent, Metrics)
- `app/repositories/` — SQLite data access layer
- `app/database/` — Async SQLite connection and migrations

## How to Run

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## How to Test

```bash
pytest tests/unit/backend/ -v
```

## Dependencies

- FastAPI, uvicorn, pydantic
- aiosqlite, websockets
- pytest, httpx (dev)
