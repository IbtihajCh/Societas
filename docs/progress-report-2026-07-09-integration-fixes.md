# Progress Report: Backend Integration Fixes & Docker Setup

**Date:** July 9, 2026
**Author:** Technical Lead
**Branch:** `main` (working tree, uncommitted)

---

## Context

Following the Tech Lead audit (July 8), the Backend ↔ Simulation Engine integration had ~15 discrepancies preventing the system from running. The frontend was a static shell with no API wiring. As Tech Lead, I performed a targeted fix session to resolve all blocking discrepancies and get the full stack running via Docker.

---

## Files Touched (Uncommitted)

### Integration Fixes

| File | Change | Status |
|---|---|---|
| `backend/app/services/simulation_service.py` | Added `engine.start()` after construction (was never called → RuntimeError) | ✅ Resolved |
| `backend/app/services/simulation_service.py` | `result.agent_results` → `result.agent_actions` (field renamed in TickResult) | ✅ Resolved |
| `backend/app/services/simulation_service.py` | Mapped 8 missing SimulationState fields: `food_availability`, `water_availability`, `crime_rate`, `protest_intensity`, `unemployment_rate`, `tax_rate`, `welfare_enabled`, `welfare_amount` | ✅ Resolved |
| `backend/app/services/simulation_service.py` | Enriched WebSocket broadcast with `duration_ms`, `state_hash`, `ambiguity_count`, `ai_calls` | ✅ Resolved |
| `backend/app/services/agent_service.py` | Mapped 3 missing summary fields: `emotion` (from emotions.primary), `unlust`, `job_type` | ✅ Resolved |
| `backend/app/services/agent_service.py` | Mapped 25 detail fields: `gender`, `culture`, `born_tick`, `unlust`, `happiness_score`, `emotion`, `emotion_timer`, `good_acts`, `crimes_committed`, `notoriety`, `trust_in_govt`, `protest_count`, `money`, `base_salary`, `employed`, `education`, `property`, `health`, `job_type`, `grid_x`, `grid_y`, `spouse`, `enemies`, `community_id`, `last_reasoning`. Fixed `last_action` (was decision_scores.top_action → now agent.last_action). | ✅ Resolved |
| `backend/app/main.py` | Removed `ai_router` import and route registration (pulls in `models/` which requires `jinja2` and other uninstalled deps — not needed since we use MockAIRouter internally) | ✅ Resolved |
| `frontend/src/types/api.ts` | Synced `ActionType` enum (15 correct values), `WealthClass` (3 values), `SimulationStateResponseDTO` (17 fields), `AgentSummaryDTO` (9 fields), `AgentDetailDTO` (35 fields) to match Python DTOs | ✅ Resolved |

### Docker Infrastructure

| File | Change | Status |
|---|---|---|
| `.dockerignore` | Created — excludes `.git/`, `node_modules/`, `vault/`, cache/DB files to speed builds | ✅ New |
| `docker/docker-compose.yml` | Fixed `file:` → `dockerfile:` (3 services); removed `simulation` dependency (doesn't exist as separate service — engine is embedded); removed volume mounts (overrode built `.next` for frontend, unnecessary for backend); set VLLM env vars for remote MI300X server | ✅ Resolved |
| `docker/docker-compose.override.yml` | Created — disables `vllm` (ROCm-only, not available locally) and `simulation` services via profiles, sets backend remote VLLM connection | ✅ New |
| `docker/backend.Dockerfile` | Changed `COPY backend/ .` → `COPY .. .` and `uvicorn app.main:app` → `uvicorn backend.app.main:app` (app imports from `backend.app.main`, needs repo root as WORKDIR) | ✅ Resolved |
| `docker/frontend.Dockerfile` | `npm ci` → `npm install` (no `package-lock.json` in repo) | ✅ Resolved |
| `backend/requirements.txt` | Added `numpy>=1.24.0` (required by simulation engine's DeterministicRNG) | ✅ Resolved |

---

## What Was Verified (Running in Docker)

The full stack is running and verified via curl:

| Endpoint | Result |
|---|---|
| `GET /api/v1/health` | `{"status":"healthy"}` |
| `POST /api/v1/simulation/start` | Creates 10 agents, returns status with tick=0, is_running=true |
| `POST /api/v1/simulation/tick` | Advances 1 tick, returns all 17 state fields with real simulation values |
| `GET /api/v1/simulation/state` | Returns complete world state |
| `GET /api/v1/agents/` | List of 10 agents with emotion, unlust, job_type populated |
| `GET /api/v1/agents/{id}` | Full 35-field agent detail |
| `GET /` (frontend) | HTTP 200 — Next.js static pages served |

---

## What Still Doesn't Work

### Frontend State Management (⚠️ Blocking UX)
`frontend/src/contexts/SimulationContext.tsx` is entirely TODO stubs:

```typescript
const startSimulation = async () => {
  // TODO: Call API to start simulation
  setIsRunning(true);
};
```

- `isConnected` never transitions from `false` (no WebSocket or API polling)
- `startSimulation` never calls `apiService.startSimulation()`
- `advanceTick` is an empty async function
- `useEffect` for initial state fetch and WebSocket connection is placeholder

**Result:** Dashboard shows "Status: Disconnected", "World State: null", buttons do nothing.

### Frontend ↔ Backend Engineer Conflict Risk

The frontend engineer likely started from the committed state (before today's changes). My changes to `frontend/src/types/api.ts` will **conflict** if the frontend engineer also modified the same file, because I changed:
- `ActionType` — replaced 9 enum values with 10 different ones
- `WealthClass` — went from 6 values to 3
- `SimulationStateResponseDTO` — added 8 fields
- `AgentSummaryDTO` — added 3 fields
- `AgentDetailDTO` — added 20+ fields, changed `last_action` type from `ActionType | null` to `string | null`

The `SimulationContext.tsx` is all TODOs so conflict there is unlikely, but the `api.ts` type file will have a direct merge conflict.

### Deferred Issues

| Issue | Target | Notes |
|---|---|---|
| Frontend → API wiring | Frontend Engineer | SimulationContext needs to call apiService methods |
| Frontend WebSocket client | Frontend Engineer | Need WS connection and event handling |
| MockAIRouter ↔ IAIRouter alignment | AI Systems Engineer | Type signatures differ (see audit); defer to VLLM integration |
| Prompt files (old model refs) | AI Systems Engineer | Still reference `gemma-2-9b-it`, old schemas |
| VLLMRouter implementation | AI Systems Engineer | MockAIRouter is placeholder; real implementation uses Gemma 4 at 165.245.130.202:8000 |

---

## Recomendation

1. **Frontend Engineer merges `main` first** before pushing any new work — today's type changes will conflict with any branch based on pre-session commits
2. **Wire SimulationContext to apiService** — ~30 lines of implementation, no new patterns needed
3. **Rebuild frontend Docker image** after frontend changes to pick up `NEXT_PUBLIC_API_URL=http://localhost:8000`
4. **Add WebSocket endpoint registration** in backend routers (existing ws_manager is unused by routes)
