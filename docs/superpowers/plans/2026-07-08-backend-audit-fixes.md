# Backend Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 backend integration gaps identified in the tech lead audit — engine persistence, private access, API return shapes, test side effect, and WebSocket wiring.

**Architecture:** Each fix is independently testable. Fixes touch 5 files across 3 modules (shared, simulation, backend), with minimal interface additions and no breaking changes.

**Tech Stack:** Python 3.11+, FastAPI, aiosqlite, pytest, ISimulationEngine interface

## Global Constraints

- No breaking changes to existing DTOs or interfaces
- All 17 existing tests must continue to pass
- Follow existing patterns: docstrings, type hints, existing `__all__` exports
- Fixes must be independently verifiable (test per change where possible)

---

### Task 1: Add `stop()` Method to Engine Interface + Implementation

**Files:**
- Modify: `shared/interfaces/i_simulation_engine.py:28-38` — add abstract `stop()` method
- Modify: `simulation/engine/simulation_engine.py:66-68` — add `stop()` implementation
- Verify: `tests/unit/backend/test_api.py` — existing stop test still passes

**Interfaces:**
- Consumes: Existing `ISimulationEngine` abstract methods
- Produces: `ISimulationEngine.stop() -> None` (abstract), `SimulationEngine.stop() -> None` (sets `_is_running = False`)

- [ ] **Step 1: Add `stop()` abstract method to `ISimulationEngine`**

Add to `shared/interfaces/i_simulation_engine.py`, after `is_running()`:

```python
@abstractmethod
def stop(self) -> None:
    """
    Stop the simulation execution.
    
    Sets the running state to False. Does not reset
    or clear any simulation state.
    """
    ...
```

- [ ] **Step 2: Implement `stop()` in `SimulationEngine`**

Add to `simulation/engine/simulation_engine.py`, after `tick()` and before `reset()`:

```python
def stop(self) -> None:
    """
    Stop the simulation execution.
    """
    self._is_running = False
```

- [ ] **Step 3: Commit**

Run: `git add shared/interfaces/i_simulation_engine.py simulation/engine/simulation_engine.py`
Expected: no lint errors
Commit: `git commit -m "feat(engine): add stop() method to ISimulationEngine interface and implementation"`

---

### Task 2: Fix Engine Persistence + Return DTOs in Simulation Router

**Files:**
- Modify: `backend/app/routers/simulation.py:23-64` — 5 endpoint changes

**Interfaces:**
- Consumes: `set_engine()` from `backend.app.dependencies`, `service.get_engine()` from `SimulationService`, `SimulationStatusDTO`, `SimulationStateResponseDTO`
- Produces: `/start` returns `SimulationStatusDTO` with engine synced to global ref, `/stop/tick/reset` return proper DTOs

- [ ] **Step 1: Update `start_simulation` — sync engine to global ref**

```python
@router.post("/start", response_model=SimulationStatusDTO)
async def start_simulation(
    request: SimulationStartRequestDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    status = await service.start_simulation(request)
    engine = service.get_engine()
    if engine is not None:
        set_engine(engine)
    return status
```

- [ ] **Step 2: Update `stop_simulation` — return DTO**

```python
@router.post("/stop", response_model=SimulationStatusDTO)
async def stop_simulation(
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.stop_simulation()
```

- [ ] **Step 3: Update `advance_tick` — return DTO**

```python
@router.post("/tick", response_model=SimulationStateResponseDTO)
async def advance_tick(
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        return await service.advance_tick()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 4: Update `reset_simulation` — return DTO**

```python
@router.post("/reset", response_model=SimulationStatusDTO)
async def reset_simulation(
    seed: Optional[int] = None,
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.reset_simulation(seed)
```

- [ ] **Step 5: Add import for `set_engine`**

Add to existing imports at top of file:
```python
from backend.app.dependencies import get_simulation_service, set_engine
```

- [ ] **Step 6: Run tests to verify**

Run: `pytest tests/unit/backend/test_api.py -v`
Expected: All 17 tests pass. `test_start_simulation` now returns `SimulationStatusDTO` with `tick`, `is_running`, etc.

- [ ] **Step 7: Commit**

Run: `git add backend/app/routers/simulation.py`
Commit: `git commit -m "fix(be): persist engine to global ref after start, return DTOs from all simulation endpoints"`

---

### Task 3: Use `stop()` Method in `SimulationService`

**Files:**
- Modify: `backend/app/services/simulation_service.py:46-50` — replace `_is_running` private access

**Interfaces:**
- Consumes: `ISimulationEngine.stop()` from Task 1
- Produces: `SimulationService.stop_simulation()` uses public API

- [ ] **Step 1: Replace private access with public `stop()`**

Current:
```python
async def stop_simulation(self) -> SimulationStatusDTO:
    if self._engine is not None:
        if hasattr(self._engine, "_is_running"):
            self._engine._is_running = False
    return await self.get_status()
```

Replace with:
```python
async def stop_simulation(self) -> SimulationStatusDTO:
    if self._engine is not None:
        self._engine.stop()
    return await self.get_status()
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/unit/backend/test_api.py -v`
Expected: All 17 tests pass, especially `test_stop_simulation`

- [ ] **Step 3: Commit**

Run: `git add backend/app/services/simulation_service.py`
Commit: `git commit -m "fix(be): use engine.stop() public API instead of accessing private _is_running"`

---

### Task 4: Add WebSocket Broadcast to Tick Lifecycle

**Files:**
- Modify: `backend/app/services/simulation_service.py:52-65` — add broadcast calls in `advance_tick`

**Interfaces:**
- Consumes: `ws_manager` from `backend.app.main`, `TickResult.agent_results`
- Produces: Broadcast `tick_completed` + `agent_acted` events after each tick

- [ ] **Step 1: Add import and broadcast calls**

Add import at top of file:
```python
from backend.app.main import ws_manager
```

In `advance_tick()`, after saving the snapshot:
```python
async def advance_tick(self) -> SimulationStateResponseDTO:
    if self._engine is None:
        raise RuntimeError("Simulation not started")
    result = await asyncio.to_thread(self._engine.tick)
    state = self._engine.get_state()
    await self._repository.save_snapshot(result.tick, state)

    await ws_manager.broadcast({
        "type": "tick_completed",
        "tick": result.tick,
        "population": state.population,
    })

    for action_result in result.agent_results:
        if action_result is not None:
            await ws_manager.broadcast({
                "type": "agent_acted",
                "agent_id": str(action_result.agent_id),
                "action": str(action_result.action),
            })
            await self._repository.save_tick_record(
                tick=result.tick,
                event_type="agent_acted",
                data={"agent_id": str(action_result.agent_id), "action": str(action_result.action)},
            )
    return self._state_to_dto(state)
```

- [ ] **Step 2: Run tests to verify**

Run: `pytest tests/unit/backend/test_api.py -v`
Expected: All 17 tests pass. Mock engine's `tick()` returns `TickResult` — no actual WebSocket connects in unit tests.

- [ ] **Step 3: Commit**

Run: `git add backend/app/services/simulation_service.py`
Commit: `git commit -m "feat(be): broadcast tick_completed and agent_acted events via WebSocket after each tick"`

---

### Task 5: Fix Test Global Side Effect

**Files:**
- Modify: `tests/unit/backend/test_api.py:52-56` — save/restore engine ref

**Interfaces:**
- Consumes: `get_engine()`, `set_engine()` from `backend.app.dependencies`
- Produces: Isolated test — no state leaks to other tests

- [ ] **Step 1: Wrap `test_advance_tick_when_not_started` with save/restore**

Current:
```python
def test_advance_tick_when_not_started(self, client):
    set_engine(None)
    response = client.post("/api/v1/simulation/tick")
    assert response.status_code == 400
```

Replace with:
```python
def test_advance_tick_when_not_started(self, client, mock_engine):
    from backend.app.dependencies import get_engine
    prev = get_engine()
    set_engine(None)
    try:
        response = client.post("/api/v1/simulation/tick")
        assert response.status_code == 400
    finally:
        set_engine(prev)
```

- [ ] **Step 2: Run tests to verify**

Run: `pytest tests/unit/backend/test_api.py -v`
Expected: All 17 tests pass. Test order independence verified.

- [ ] **Step 3: Commit**

Run: `git add tests/unit/backend/test_api.py`
Commit: `git commit -m "fix(be): save/restore engine ref in advance_tick test to prevent state leakage"`

---

## Self-Review

- [ ] **Spec coverage:** All 5 backend audit issues are covered by Tasks 1-5. Each task maps to exactly one fix.
- [ ] **Placeholder scan:** No TBD, TODO, or incomplete references.
- [ ] **Type consistency:** `ISimulationEngine.stop() -> None` used consistently across Tasks 1 and 3. `ws_manager` referenced correctly from `backend.app.main` in Task 4.