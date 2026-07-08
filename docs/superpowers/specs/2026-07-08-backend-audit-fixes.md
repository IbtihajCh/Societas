---
type: spec
status: draft
date: 2026-07-08
tags: [backend, audit-fixes, integration, sprint-001]
owner: Backend Engineer
---

# Backend Audit Fixes — Integration Gaps

## Context

The tech lead code audit (July 8, 2026) identified 5 real backend issues in the service layer implementation (PR #9). This spec covers the fixes needed to close these integration gaps, prioritizing hackathon pragmatism over architectural purity.

## Issues Overview

| # | Issue | Severity | Module | Approach |
|---|-------|----------|--------|----------|
| 1 | Engine lost between requests after `/start` | Critical | `routers/simulation.py` | Sync engine to global ref |
| 2 | `stop_simulation` accesses private `_is_running` | Medium | `services/simulation_service.py` + `ISimulationEngine` | Add public `stop()` method |
| 3 | API endpoint return shapes don't match DTOs | Critical | All mutation routers | Return DTOs directly |
| 4 | Test global side effect (`set_engine(None)`) | Medium | `tests/unit/backend/test_api.py` | Save/restore engine ref |
| 5 | WebSocket broadcast never triggered | Medium | `services/simulation_service.py` | Call `ws_manager.broadcast()` |

---

## Fix 1: Engine Persistence Across Requests

### Problem

`container.py` creates a new `SimulationService` per request. When `POST /simulation/start` creates a `SimulationEngine`, it sets it on that service instance — but the next request gets a fresh service with `engine=None`.

### Implementation

In `routers/simulation.py`, after the service creates the engine in `/start`, sync it to the global ref:

```python
@router.post("/start")
async def start_simulation(
    request: SimulationStartRequestDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    status = await service.start_simulation(request)
    engine = service.get_engine()
    if engine is not None:
        set_engine(engine)
    return {...}
```

The global `_engine` ref in `container.py` remains the single source of truth across requests. All subsequent `Depends()` calls will pick up the engine via `SimulationService(engine=_engine, ...)`.

### Files Changed
- `backend/app/routers/simulation.py` — add `set_engine()` call after start

---

## Fix 2: Private `_is_running` Access in `stop_simulation`

### Problem

`simulation_service.py` line 48-49:
```python
if hasattr(self._engine, "_is_running"):
    self._engine._is_running = False
```

The `ISimulationEngine` interface defines `is_running()` (public getter) but no public stop method.

### Implementation

**Step 1:** Add `stop()` to `ISimulationEngine` interface:

```python
@abstractmethod
def stop(self) -> None:
    """Stop the simulation."""
    ...
```

**Step 2:** Implement in `SimulationEngine`:

```python
def stop(self) -> None:
    self._is_running = False
```

**Step 3:** Update `SimulationService.stop_simulation()`:

```python
async def stop_simulation(self) -> SimulationStatusDTO:
    if self._engine is not None:
        self._engine.stop()
    return await self.get_status()
```

### Files Changed
- `shared/interfaces/i_simulation_engine.py` — add `stop()` abstract method
- `simulation/engine/simulation_engine.py` — implement `stop()`
- `backend/app/services/simulation_service.py` — use `self._engine.stop()`

---

## Fix 3: API Endpoint Return Shapes

### Problem

Mutation endpoints return hardcoded dicts that don't match the shared DTOs:

| Endpoint | Current Return | Should Return |
|----------|---------------|---------------|
| `POST /start` | `{"simulation_id": "sim-001", "status": "started", "tick": ...}` | `SimulationStatusDTO` |
| `POST /stop` | `{"status": "stopped", "tick": ...}` | `SimulationStatusDTO` |
| `POST /tick` | `{"tick": ..., "status": "completed"}` | `SimulationStateResponseDTO` |
| `POST /reset` | `{"status": "reset", "tick": ...}` | `SimulationStatusDTO` |

### Implementation

Return the DTO directly from each endpoint:

```python
@router.post("/start", response_model=SimulationStatusDTO)
async def start_simulation(...):
    status = await service.start_simulation(request)
    engine = service.get_engine()
    if engine is not None:
        set_engine(engine)
    return status  # Already a SimulationStatusDTO
```

Same pattern for stop, tick (returns the state DTO), and reset.

### Files Changed
- `backend/app/routers/simulation.py` — return DTOs, add `response_model`

---

## Fix 4: Test Global Side Effect

### Problem

`test_advance_tick_when_not_started` calls `set_engine(None)` at module level, mutating global state that leaks to subsequent tests.

### Implementation

Save and restore the engine ref within the test:

```python
def test_advance_tick_when_not_started(self, client, mock_engine):
    from backend.app.dependencies import get_engine, set_engine
    prev = get_engine()
    set_engine(None)
    try:
        response = client.post("/api/v1/simulation/tick")
        assert response.status_code == 400
    finally:
        set_engine(prev)
```

The `try/finally` ensures cleanup even if the assertion fails.

### Files Changed
- `tests/unit/backend/test_api.py` — wrap test with save/restore

---

## Fix 5: WebSocket Broadcast in Tick Lifecycle

### Problem

`ws_manager.broadcast()` is implemented but never called. The `/ws` endpoint only echoes. The frontend report flags this as critical for real-time updates.

### Implementation

In `simulation_service.py`, after each tick completes, import and call `ws_manager`:

```python
from backend.app.main import ws_manager

# Inside advance_tick():
await ws_manager.broadcast({
    "type": "tick_completed",
    "tick": result.tick,
    "population": state.population,
})

# And for each agent action:
for action_result in result.agent_results:
    if action_result is not None:
        await ws_manager.broadcast({
            "type": "agent_acted",
            "agent_id": str(action_result.agent_id),
            "action": str(action_result.action),
        })
```

This mirrors the existing pattern in `advance_tick()` where it already iterates `result.agent_results` for persistence. The broadcast is additive — no functional changes to the tick logic.

### Files Changed
- `backend/app/services/simulation_service.py` — import `ws_manager`, add broadcast calls

---

## Files Summary

| File | Change Type | Fixes |
|------|-------------|-------|
| `shared/interfaces/i_simulation_engine.py` | Modify | Fix 2 — add `stop()` abstract method |
| `simulation/engine/simulation_engine.py` | Modify | Fix 2 — implement `stop()` |
| `backend/app/services/simulation_service.py` | Modify | Fix 2 + Fix 5 — use `stop()`, add WS broadcast |
| `backend/app/routers/simulation.py` | Modify | Fix 1 + Fix 3 — sync engine, return DTOs |
| `tests/unit/backend/test_api.py` | Modify | Fix 4 — save/restore engine ref |

## Test Plan

- All existing 17 tests must continue to pass
- `test_advance_tick_when_not_started` — still asserts 400, no longer leaks state
- No new tests needed — these are fixes to existing behavior, not new features

## Self-Review

- [x] No placeholders or TODOs left in spec
- [x] Each fix has a clear problem statement and implementation
- [x] Scope appropriate for a single implementation plan
- [x] Follows existing patterns (imports, types, error handling)
- [x] Appropriate for hackathon — minimal changes, maximum impact
- [x] Changes limited to backend + minimal shared/simulation interface additions
