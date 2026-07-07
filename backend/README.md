# Backend API Module

**Owner:** Backend Engineer

## Purpose

FastAPI-based REST API for SOCIETAS simulation. Provides the interface between the frontend dashboard and the simulation/AI modules. Uses a **thin service orchestrator** architecture — routers delegate to services, which coordinate the simulation engine and SQLite persistence.

## Directory Structure

```
backend/
├── app/
│   ├── config/          Environment-based settings (dataclass + singleton)
│   ├── database/        Async SQLite connection, init, and migrations
│   ├── repositories/    Data access layer (PolicyRepository, SimulationRepository)
│   ├── services/        Orchestrators (Simulation, Policy, Agent, Metrics)
│   ├── dependencies/    FastAPI Depends() wiring for DI
│   ├── routers/         HTTP route handlers (thin, call services)
│   ├── middleware/      Request logging middleware
│   ├── websocket/       WebSocket connection manager with broadcast
│   └── main.py          App factory, lifespan, error handlers, WS endpoint
├── requirements.txt
└── README.md
```

## Architecture

```
Routers (HTTP concerns)
  → Services (orchestration)
    → Engine (ISimulationEngine) — simulation control
    → Repositories (IDataRepository) — SQLite persistence
```

Dependency injection via FastAPI `Depends()` — each router declares its service dependency, which is wired from a global engine reference in `dependencies/container.py`.

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi>=0.104.0` | Web framework |
| `uvicorn[standard]>=0.24.0` | ASGI server |
| `pydantic>=2.0.0` | Data validation |
| `websockets>=12.0` | WebSocket protocol |
| `aiosqlite>=0.20.0` | Async SQLite driver |
| `pytest>=7.4.0` | Test runner |
| `pytest-cov>=4.1.0` | Coverage reporting |
| `httpx>=0.25.0` | HTTP client for tests |

## Configuration

All settings loaded from `SOCIETAS_*` environment variables via `config/settings.py`.

| Variable | Default | Description |
|----------|---------|-------------|
| `SOCIETAS_DATABASE_PATH` | `societas.db` | SQLite database file path |
| `SOCIETAS_CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins |
| `SOCIETAS_LOG_LEVEL` | `INFO` | Logging level |
| `SOCIETAS_SIMULATION_POPULATION_SIZE` | `100` | Default agent count for new simulations |
| `SOCIETAS_SIMULATION_SEED` | (none) | Optional deterministic RNG seed |

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check — always returns 200 |
| `GET` | `/api/v1/ready` | Readiness check — validates engine is initialized |

### Simulation

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/simulation/status` | Current simulation status (running, tick count) |
| `POST` | `/api/v1/simulation/start` | Start simulation with config (population, seed) |
| `POST` | `/api/v1/simulation/stop` | Stop running simulation |
| `POST` | `/api/v1/simulation/tick` | Advance one tick (400 if not started) |
| `GET` | `/api/v1/simulation/state` | Full simulation state snapshot |
| `POST` | `/api/v1/simulation/reset` | Reset simulation (optional new seed) |

### Policies

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/policies/` | List all policies |
| `POST` | `/api/v1/policies/` | Create a new policy (category, weights) |
| `GET` | `/api/v1/policies/{id}` | Get policy by ID (404 if not found) |
| `DELETE` | `/api/v1/policies/{id}` | Revoke policy by ID (404 if not found) |

### Metrics

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/metrics/` | Get metrics (optional `tick_from`, `tick_to`) |
| `GET` | `/api/v1/metrics/dashboard` | Aggregated dashboard data |

### Agents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/agents/` | List agents (optional `limit`, `offset`) |
| `GET` | `/api/v1/agents/{id}` | Get agent detail (404 if not found) |
| `GET` | `/api/v1/agents/{id}/history` | Get agent history |

### WebSocket

| Path | Description |
|------|-------------|
| `WS /ws` | Real-time simulation event stream (broadcast) |

## Database Schema

Three tables managed by `database/migrations.py`:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `policies` | Stored policy definitions | `policy_id`, `name`, `category`, `weights` (JSON), `is_active` |
| `state_snapshots` | Simulation state checkpoints | `tick` (PK), `state_json` (full state) |
| `tick_history` | Per-tick event log | `tick`, `event_type`, `data_json`, indexed by `tick` |

## Services

Each service is a stateless orchestrator — instantiated per request via `Depends()`:

### SimulationService
- Wraps `ISimulationEngine` lifecycle (start, stop, tick, reset)
- Saves snapshots to `SimulationRepository` on each tick
- `advance_tick()` runs engine tick via `asyncio.to_thread()`

### PolicyService
- Creates policies: persists via `PolicyRepository` + applies to engine
- List/Get/Revoke operations with proper 404 handling

### AgentService
- Reads agent data from engine (`get_agents`, `get_agent`)
- Maps `AgentState` → DTOs via `_agent_to_summary()` / `_agent_to_detail()`
- Supports pagination (`limit`, `offset`)

### MetricsService
- Aggregates metrics from engine + tick history from repository
- Dashboard endpoint combines state summary + recent history

## Setup & Running

```bash
pip install -r backend/requirements.txt

# Start development server (hot reload)
uvicorn backend.app.main:app --reload --port 8000

# Interactive API docs
open http://localhost:8000/docs
open http://localhost:8000/redoc
```

## Testing

```bash
# Run all backend tests
pytest tests/unit/backend/ -v

# With coverage
pytest tests/unit/backend/ --cov=backend.app -v
```

Tests use mock engine fixtures (`conftest.py`) — no simulation engine required. 17 test cases covering all routers and services.

## Error Handling

| Status | Condition |
|--------|-----------|
| `400` | Invalid operation (e.g., tick before simulation start) |
| `404` | Resource not found (policy, agent) |
| `422` | Request validation failure (Pydantic) |
| `500` | Unhandled server exception (logged with traceback) |
