# AMD Hackathon Demo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build an interactive demo dashboard with AI Historian narrative, live policy controls, crisis injection, and Governor recommendation panels showcasing all 3 Gemma 4 models on AMD MI300X.

**Architecture:** Wrap the existing simulation engine in a demo layer — new FastAPI endpoints for policy/crisis/history, new frontend dashboard page with panels for each AI model output, WebSocket broadcasting for live metrics.

**Tech Stack:** FastAPI, Next.js Pages Router, Recharts (already in deps), Zustand, Axios, WebSocket

## Global Constraints
- 1-day build time — zero engine changes, pure demo-layer additions
- Frontend uses Next.js Pages Router (`pages/` not `app/`)
- All inline styles (existing pattern)
- Backend routes under `/api/v1/` prefix
- Frontend API client in `services/api.ts` using Axios
- WebSocket endpoint exists at `ws://localhost:8000/ws` (needs client)
- 3 vLLM model endpoints on ports 8000 (31B), 8001 (E2B), 8002 (26B MoE)

---

### Task 1: AI Historian Service + Governor Recommendations

**Files:**
- Create: `backend/app/services/ai_historian.py`
- Create: `backend/app/routers/ai_historian.py`
- Modify: `models/router/vllm_router.py`

- [ ] Step 1: Add `generate_narrative()` and `moral_assessment()` to VLLMRouter

In `vllm_router.py`:
```python
def generate_narrative(self, context: str) -> str:
    results = self._call_vllm(self._client_dense, context, api_key=self._config.api_key_dense_31b, temperature=0.7, max_tokens=256, model=self._config.model_dense_31b)
    return results[0]

def moral_assessment(self, question: str) -> str:
    results = self._call_vllm(self._client_moe, question, api_key=self._config.api_key_moe_26b, temperature=0.3, max_tokens=256, model=self._config.model_moe_26b)
    return results[0]
```

- [ ] Step 2: Write test `tests/unit/ai/test_ai_historian.py`
- [ ] Step 3: Run test to verify it fails
- [ ] Step 4: Create `AHistorianService` in `backend/app/services/ai_historian.py`
  - `generate_entry(world_state, tick) -> dict` — builds prompt from metrics, calls 31B, appends to `_entries`
  - `get_governance_advice(world_state) -> dict` — calls 31B for governance + 26B MoE for ethics
  - `get_history() -> list[dict]` — returns all entries
- [ ] Step 5: Run test to verify it passes
- [ ] Step 6: Create `backend/app/routers/ai_historian.py`
  - `GET /api/v1/ai/history` — returns chronicle entries from AHistorianService
  - `GET /api/v1/ai/policy-advice` — returns governance+ethics from AHistorianService
- [ ] Step 7: Register router in `backend/app/main.py`
- [ ] Step 8: Wire historian into SimulationService — init in `start_simulation()`, call `generate_entry()` every 10 ticks in `advance_tick()`
- [ ] Step 9: Commit

### Task 2: Policy Controls + Crisis Injection Endpoints

**Files:**
- Create: `backend/app/routers/policy_controls.py`

- [ ] Step 1: Create router with:
  - `POST /api/v1/simulation/policy` — body: `{ tax_rate?, welfare_enabled?, welfare_amount? }` — modifies world state via `setattr`
  - `POST /api/v1/simulation/crisis` — body: `{ type: "famine"|"plague"|"rebellion"|"tech_boom" }` — applies predefined world state changes
- [ ] Step 2: Register in `main.py`
- [ ] Step 3: Commit

### Task 3: WebSocket Broadcasting for Live Metrics

**Files:**
- Modify: `backend/app/services/simulation_service.py`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] Step 1: In `advance_tick()`, after saving snapshot, broadcast via `ws_manager.broadcast({"type": "metrics_update", "tick": tick, "state": state_dict})`. Also broadcast chronicle entries.
- [ ] Step 2: Create `frontend/src/hooks/useWebSocket.ts` hook
  - Connects to `ws://localhost:8000/ws`
  - Parses `metrics_update` → updates `latestMetrics` state
  - Parses `chronicle` → appends to `chronicle[]` array
  - Returns `{ connected, latestMetrics, chronicle }`
- [ ] Step 3: Commit

### Task 4: Demo Dashboard — Frontend Components

**Files (create all in `frontend/src/components/dashboard/`):**
- `PolicyControls.tsx` — tax rate slider (0-100%), calls `api.updatePolicy()`
- `AiHistorianPanel.tsx` — scrolling chronicle entries, newest first
- `GovernorPanel.tsx` — two boxes: Governance Advice (31B) + Ethical Assessment (26B MoE), polls `/api/v1/ai/policy-advice` every 10s
- `CrisisButton.tsx` — dropdown + red "TRIGGER" button, calls `api.triggerCrisis()`
- `MetricsChart.tsx` — Recharts LineChart showing population + unlust over time
- `ScenarioSelector.tsx` — dropdown for 3 demo scenarios, calls `api.loadScenario()`
- Modify: `frontend/src/pages/dashboard.tsx` — compose all panels in grid layout
- Modify: `frontend/src/services/api.ts` — add `updatePolicy()`, `triggerCrisis()`, `getPolicyAdvice()`, `loadScenario()` methods

- [ ] Step 1: Add API methods
- [ ] Step 2: Create PolicyControls
- [ ] Step 3: Create AiHistorianPanel
- [ ] Step 4: Create GovernorPanel
- [ ] Step 5: Create CrisisButton
- [ ] Step 6: Create MetricsChart
- [ ] Step 7: Create ScenarioSelector
- [ ] Step 8: Rebuild dashboard page
- [ ] Step 9: Commit

### Task 5: Demo Scenarios + Guide

**Files:**
- Create: `simulation/test_reports/scenarios_demo.py`
  - 3 scenarios: utopia_plague, dictatorship_revolt, anarchy_recovery
  - Each has n_agents, ticks, seed, world state params, description
- Modify: `backend/app/services/simulation_service.py` — read scenario from request, initialize world with scenario params
- Modify: `backend/app/routers/simulation.py` — accept optional `scenario` field in start request DTO
- Create: `DEMO_SCRIPT.md` — 5-minute judge walkthrough

- [ ] Step 1: Create scenario definitions
- [ ] Step 2: Add scenario support to backend
- [ ] Step 3: Write DEMO_SCRIPT.md
- [ ] Step 4: Commit

### Task 6: Integration Test + Final Polish

- [ ] Step 1: `pytest tests/unit/ -v --tb=short` — fix failures
- [ ] Step 2: `npm test` in frontend/ — fix failures
- [ ] Step 3: Commit final polish
