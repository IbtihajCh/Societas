# SOCIETAS Frontend

**Owner:** Frontend Engineer

## Purpose

React/Next.js dashboard for the SOCIETAS simulation. Provides real-time visualization of simulation state, agent behavior, and policy effects.

## Tech Stack

- **Framework:** Next.js 14 (React 18)
- **Language:** TypeScript
- **State Management:** Zustand
- **Charts:** Recharts
- **HTTP Client:** Axios
- **Styling:** CSS Modules

## Features

- Real-time simulation monitoring via WebSocket
- Dashboard with key metrics and charts
- Agent browser with detail view
- Policy management interface
- News and narrative feed
- Simulation controls (start/stop/step)

## Pages

- `/` - Home page with overview
- `/dashboard` - Main simulation dashboard
- `/policies` - Policy management
- `/agents` - Agent browser

## Components

### Dashboard
- `MetricsPanel` - Key metrics display
- `SimulationControls` - Start/stop/step controls
- `EventLog` - Real-time event feed

### Policies
- `PolicyList` - Active policies display
- `PolicyForm` - Policy creation form

### Agents
- `AgentList` - Agent browser
- `AgentDetail` - Agent detail view

## API Integration

All API calls go through `services/api.ts` which wraps Axios and provides typed
methods for each endpoint. Responses are typed against `src/types/api.ts`.

### Contract source of truth

The TypeScript types in `src/types/api.ts` **mirror the canonical Python DTOs**
in [`shared/dto/`](../shared/dto/) — not the `contracts/openapi.yaml` spec,
which is currently stale. Field names are consumed as **snake_case** (e.g.
`is_running`, `economic_health`) to match the backend serialization directly,
with no transform layer. Keep `src/types/api.ts` in sync with `shared/dto/*`
when the backend DTOs change.

Backend endpoints (FastAPI, default `http://localhost:8000/api/v1`):

| Area | Endpoint | Method |
|------|----------|--------|
| Health | `/health` | GET |
| Simulation | `/simulation/status`, `/state` | GET |
| Simulation | `/simulation/start`, `/stop`, `/tick`, `/reset` | POST |
| Policies | `/policies` | GET, POST |
| Policies | `/policies/{id}` | GET, DELETE |
| Metrics | `/metrics`, `/metrics/dashboard` | GET |
| Agents | `/agents` | GET |
| Agents | `/agents/{id}`, `/agents/{id}/history` | GET |
| WebSocket | `/ws` | WS |

The proxy in `next.config.js` forwards `/api/*` and `/ws` to the backend, so
the UI can also use relative paths in development.

## Development

```bash
npm install
npm run dev
```

Open http://localhost:3000

### Prerequisites

The SOCIETAS backend (FastAPI) must be running at `http://localhost:8000`.
Start it from the repository root:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Set `NEXT_PUBLIC_API_URL` to override the default API base URL.

## Future Work

- Implement WebSocket connection for real-time updates
- Add chart components for metrics visualization
- Implement policy effect visualization
- Add agent behavior timeline
- Add news feed with AI-generated narratives
- Implement responsive design
- Add dark mode support
- Add export/import functionality
