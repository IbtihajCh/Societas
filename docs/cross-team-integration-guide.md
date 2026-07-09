# SOCIETAS Cross-Team Integration Guide

**Date:** 2026-07-09  
**Author:** Simulation Engineer (AI agent)  
**Status:** Active — required reading before integrating with the simulation engine

---

## Purpose

The simulation engine is implemented and tested (492 tests, all passing). This document lists every task that other team members must complete to integrate their subsystems with the simulation. Each section is scoped to one role.

The simulation engine lives at `simulation/` and implements `shared/interfaces/i_simulation_engine.py`. All shared schemas, types, and constants live at `shared/`.

---

## 1. Backend Engineer Tasks

### 1.1 CRITICAL: `engine.start()` must be called after construction

The `SimulationEngine` no longer auto-initializes in `__init__`. A new `start()` method was added that creates the agent population, seeds the RNG, and optionally connects an AI router.

**File:** `backend/app/services/simulation_service.py` — `start_simulation()` method

**Current (broken):**
```python
self._engine = SimulationEngine(config=config)
return await self.get_status()
```

**Required:**
```python
from simulation.engine.mock_ai_router import MockAIRouter

self._engine = SimulationEngine(config=config)
self._engine.start(ai_router=MockAIRouter(seed=request.seed) if config.enable_ai_escalation else None)
return await self.get_status()
```

Without `start()`, calling `tick()` raises `RuntimeError("Simulation not started")`.

### 1.2 CRITICAL: Fix `agent_results` → `agent_actions` field name

**File:** `backend/app/services/simulation_service.py` — `advance_tick()` method, line 58

**Current (broken):**
```python
for action_result in result.agent_results:
```

**Required:**
```python
for action_result in result.agent_actions:
```

The `TickResult` schema (`shared/schemas/tick_result.py`) uses `agent_actions`, not `agent_results`.

### 1.3 CRITICAL: Fix `stop_simulation()` private attribute access

**File:** `backend/app/services/simulation_service.py` — `stop_simulation()` method, line 48

**Current (broken):**
```python
if hasattr(self._engine, "_is_running"):
    self._engine._is_running = False
```

**Required:**
```python
# Option A: Add a stop() method to SimulationEngine (preferred)
self._engine.stop()

# Option B: If no stop() method exists yet, at least use the public interface
# The engine already has is_running() — add a stop() method that sets _is_running = False
```

The simulation engine needs a `stop()` method added to `ISimulationEngine`. The Simulation Engineer can add this, or the Backend Engineer can request it.

### 1.4 CRITICAL: DI container loses engine between requests

**File:** `backend/app/dependencies/container.py`

**Problem:** Each `Depends(get_simulation_service)` call creates a new `SimulationService(engine=_engine, ...)`. The `_engine` global is set by `set_engine()` but `start_simulation()` creates a new engine on `self._engine` (instance attribute), which is lost when the next request creates a new service.

**Required fix:** After `start_simulation()` creates and starts the engine, it must call `set_engine()` to persist it globally:

```python
async def start_simulation(self, request: SimulationStartRequestDTO) -> SimulationStatusDTO:
    config = SimulationConfig(
        population_size=request.population_size,
        seed=request.seed,
    )
    self._engine = SimulationEngine(config=config)
    self._engine.start()
    # Persist the engine globally so subsequent requests can access it
    from backend.app.dependencies.container import set_engine
    set_engine(self._engine)
    return await self.get_status()
```

### 1.5 Wire WebSocket broadcasts into tick lifecycle

**File:** `backend/app/routers/simulation.py` or a new WebSocket router

**Required:** After each `advance_tick()` call, broadcast the `TickResult` to connected WebSocket clients. The frontend expects:
- `tick_completed` event with the `TickResult` data
- `agent_acted` events for each agent action

**Implementation pattern:**
```python
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# In advance_tick endpoint:
result = await service.advance_tick()
await manager.broadcast({
    "type": "tick_completed",
    "tick": result.tick,
    "state_hash": result.state_hash,
    "agent_count": len(result.agent_actions),
    "ambiguity_count": result.ambiguity_count,
    "ai_calls": result.ai_calls,
    "state_changes": result.state_changes,
})
```

### 1.6 DTO field mapping audit

The `SimulationStateResponseDTO` currently maps these fields from `SimulationState`:
- `tick` ← `state.time_step` (FIXED — was `state.tick`)
- `economic_health` ← `state.economic_health` (top-level, FIXED)
- `social_cohesion` ← `state.social_cohesion` (top-level, FIXED)
- `public_order` ← `state.public_order` (top-level, FIXED)
- `innovation_index` ← `state.innovation_index` (top-level, FIXED)
- `unlust` ← `state.unlust` (top-level, FIXED)
- `morality` ← `state.morality` (top-level, FIXED)

**New fields available for frontend:**
- `state.food_availability` (0.0-1.0)
- `state.water_availability` (0.0-1.0)
- `state.crime_rate` (0.0-1.0)
- `state.protest_intensity` (0.0-1.0)
- `state.unemployment_rate` (0.0-1.0)
- `state.tax_rate` (0.0-1.0)
- `state.welfare_enabled` (bool)
- `state.welfare_amount` (float)

Consider adding these to the DTO for richer dashboard data.

---

## 2. AI Systems Engineer Tasks

### 2.1 Implement VLLMRouter

**Spec document:** `simulation/test_reports/vllm-integration-spec.md` — complete specification with 3-model setup, prompt schemas, batching strategy, and fallback config.

**Summary:**
- **E2B** (port 8001, 3 replicas, ~1GB each): agent brains — every agent gets a structured prompt, returns `{action, feeling, reason}` JSON
- **26B A4B** (port 8002, ~16.5GB, thinking mode): moral reasoning — handles ethical dilemmas with chain-of-thought
- **31B** (port 8003, ~20.3GB, thinking mode): governance advisor + policy translation

**Interface to implement:** `shared/interfaces/i_ai_router.py` — `IAIRouter` with these methods:
- `agent_decide(prompt, agent, world) -> dict` — E2B agent brain
- `agent_decide_batch(prompts, agents, world) -> list[dict]` — batched E2B calls
- `moral_reasoning(prompt, agent, world) -> dict` — 26B moral reasoning
- `moral_reasoning_batch(prompts, agents, world) -> list[dict]` — batched 26B
- `governance_advisory(world_state, active_policies) -> dict` — 31B advisor
- `translate_policy(policy_text, existing_weights, world) -> dict` — 31B policy translation
- `generate_news(events, state_deltas) -> dict` — 31B news generation
- `is_available() -> bool` — health check

**Key contract:** If any LLM call fails, return `None` (or empty dict). The simulation engine falls back to `deterministic_fallback()` automatically. The simulation MUST NOT crash if vLLM is unavailable.

**Mock for testing:** `simulation/engine/mock_ai_router.py` — `MockAIRouter` already implements the interface with trait-aware deterministic decisions. Use this for all testing without GPU.

### 2.2 Update prompt files

**Files to update:** `prompts/*.md`

The current prompt files use old trait names and schemas. Update them to match the new implementation:

- `prompts/tie-break.md` — Input should include: 13 needs, 7 traits, unlust, happiness, emotion, money, employed, job_type, nearby_counts, world state. Output: `{action, feeling, reason}` JSON.
- `prompts/policy-translation.md` — Input: policy text + existing PolicyWeights + world state. Output: `{impact_deltas: {poor: ImpactDelta, middle: ImpactDelta, rich: ImpactDelta}, weights: PolicyWeights, world_changes: {tax_rate?, welfare_on?, food_event?}, reasoning: string}`.
- `prompts/persona-generation.md` — Input: 7 traits (creativity, morality, anger_tendency, extraversion, ambition, resilience, dominance_urge) + gender + culture + wealth_class. Output: 1-2 sentence persona.
- `prompts/narrative-generation.md` — Input: tick events, state deltas, wealth-stratified metrics. Output: `{headline, body, category, importance}` JSON.

### 2.3 Fireworks AI fallback

When vLLM is unavailable (no GPU, model loading), route to Fireworks AI API:
- Base URL: `https://api.fireworks.ai/inference/v1`
- Models: `accounts/fireworks/models/gemma-4-e2b-it`, `accounts/fireworks/models/gemma-4-26b-a4b-it`, `accounts/fireworks/models/gemma-4-31b-it`
- API key from environment variable `FIREWORKS_API_KEY`

---

## 3. Frontend Engineer Tasks

### 3.1 DTO field alignment

The simulation now exposes richer data. Update frontend types to match `shared/dto/`:

**AgentDetailDTO** new fields available:
- `agent.gender` (string: "male"/"female")
- `agent.culture` (string: "a"/"b"/"c")
- `agent.unlust` (float 0-1)
- `agent.wealth_class` (string: "poor"/"middle"/"rich")
- `agent.employed` (bool)
- `agent.job_type` (string)
- `agent.education` (int 0/1/2)
- `agent.protest_count` (int)
- `agent.trust_in_govt` (float 0-1)
- `agent.good_acts` (int)
- `agent.crimes_committed` (int)

**SimulationStateResponseDTO** new fields (if backend adds them):
- `food_availability`, `water_availability`, `crime_rate`, `protest_intensity`
- `unemployment_rate`, `tax_rate`, `welfare_enabled`, `welfare_amount`

### 3.2 WebSocket event handling

The frontend should connect to `ws://backend:8000/ws` and handle:
- `tick_completed` — update dashboard with new state
- `agent_acted` — update agent grid (optional, can batch)

### 3.3 Dashboard panels

The simulation produces these metrics per tick:
- `avg_happiness` (0-1)
- `avg_unlust` (0-1)
- `crime_rate` (0-1)
- `protest_intensity` (0-1)
- `unemployment_rate` (0-1)
- `alive_count` (int)
- `food_availability` (0-1)
- `emotion_proportions` (dict: happy/normal/sad/angry/despair → count)
- `action_frequencies` (dict: action_type → count)

Wealth-stratified metrics are also available (per poor/middle/rich class).

---

## 4. DevOps / Infrastructure Tasks

### 4.1 CRITICAL: Dockerfiles must include `/shared/`

**Problem:** Both `docker/simulation.Dockerfile` and `docker/backend.Dockerfile` copy only their own directory. Every file in the project imports from `shared.*`, so the containers crash at import time.

**Fix for `docker/simulation.Dockerfile`:**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY simulation/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY shared/ /app/shared/
COPY simulation/ /app/simulation/

CMD ["python", "-m", "simulation.engine.main"]
```

**Fix for `docker/backend.Dockerfile`:**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY shared/ /app/shared/
COPY backend/ /app/backend/
COPY simulation/ /app/simulation/
COPY prompts/ /app/prompts/

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Docker Compose: multi-model vLLM

The current `docker-compose.yml` has a single vLLM container. For the 3-model setup, replace with 3 containers:

```yaml
vllm-e2b:
  build:
    context: ..
    file: docker/vllm.Dockerfile
  container_name: societas-vllm-e2b
  ports:
    - "8001:8001"
  environment:
    - MODEL_NAME=gemma-4-e2b-it-qat
    - GPU_MEMORY_UTILIZATION=0.05
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]

vllm-26b:
  build:
    context: ..
    file: docker/vllm.Dockerfile
  container_name: societas-vllm-26b
  ports:
    - "8002:8002"
  environment:
    - MODEL_NAME=gemma-4-26b-a4b-it-qat
    - GPU_MEMORY_UTILIZATION=0.10
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]

vllm-31b:
  build:
    context: ..
    file: docker/vllm.Dockerfile
  container_name: societas-vllm-31b
  ports:
    - "8003:8003"
  environment:
    - MODEL_NAME=gemma-4-31b-it-qat
    - GPU_MEMORY_UTILIZATION=0.15
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

**IMPORTANT:** Launch vLLM containers SEQUENTIALLY (not in parallel). The `gpu_memory_utilization` percentage is calculated on FREE VRAM, not total. If launched simultaneously, the first container grabs all VRAM.

### 4.3 Python path configuration

The project uses `pyproject.toml` with `pythonpath = ['.']` for pytest. For Docker, ensure the working directory is the project root (`/app/`) so `shared.*` and `simulation.*` imports resolve correctly.

---

## 5. Technical Lead Tasks

### 5.1 Branch merge decision

The `sim/implementation-v2` branch contains:
- 8 commits (6 implementation phases + P1-P5 fixes + docs)
- 492 tests passing (simulation + shared)
- 505/506 tests with backend (1 pre-existing test isolation issue)
- ~10,000 lines of new code across 50+ files

Review checklist:
- [ ] 90% branch coverage (CI gate — run `pytest --cov --cov-branch --cov-fail-under=90`)
- [ ] `ruff check .` passes
- [ ] `mypy . --strict` passes (may have pre-existing import resolution issues without `pip install -e .`)
- [ ] All determinism tests pass (same seed = same state_hash)
- [ ] No files modified outside `/simulation/` and `/shared/` (except backend fixes in `simulation_service.py` and `agent_dto.py`)

### 5.2 Cross-team coordination

- Backend Engineer needs `engine.start()` and `engine.stop()` methods (start() implemented, stop() needs adding to interface)
- AI Systems Engineer needs the vLLM spec at `simulation/test_reports/vllm-integration-spec.md`
- Frontend Engineer needs updated DTO fields (see Section 3.1)
- DevOps needs updated Dockerfiles (see Section 4.1)

---

## 6. Known Issues (Not Blocks)

| Issue | Severity | Owner | Status |
|---|---|---|---|
| 0 crimes in test scenarios | Low (tuning) | Simulation Eng | Needs parameter tuning |
| Wealth effects minimal (all-poor ≈ all-rich) | Low (tuning) | Simulation Eng | Needs salary multiplier increase |
| Protests only with MockAI, not deterministic fallback | Low (tuning) | Simulation Eng | Needs unlust threshold adjustment |
| Backend `test_list_policies_empty` fails in full suite | Low (pre-existing) | Backend Eng | DB pollution between tests |
| `pip install -e .` doesn't work (no build-system) | Low (infra) | Tech Lead | Add `[build-system]` to pyproject.toml |
| LSP import resolution errors | Cosmetic | Infra | Fixed by `pip install -e .` |

---

## 7. How to Run the Simulation

### Local (no GPU, mock AI)
```bash
# Create venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install numpy pytest pytest-cov

# Run tests
python -m pytest tests/unit/simulation/ tests/unit/shared/ -v

# Run a scenario
python simulation/test_reports/runner.py a1_default
```

### With backend (no GPU)
```bash
pip install fastapi httpx aiosqlite uvicorn
uvicorn backend.app.main:app --reload
# POST /simulation/start with {"population_size": 80, "seed": 42}
# POST /simulation/tick
```

### With vLLM (GPU required)
See `simulation/test_reports/vllm-integration-spec.md` for full setup.

---

## Related Documents

- `AGENTS.md` — Simulation Engineer operating manual
- `docs/SOCIETAS_Simulation_Implementation_Guide.md` — v2.0 comprehensive implementation guide
- `docs/adr/ADR-005-simulation-implementation-architecture.md` — architecture decisions
- `simulation/test_reports/vllm-integration-spec.md` — vLLM integration spec for AI Engineer
- `simulation/development-playbook.md` — patterns and pitfalls from development
- `docs/progress-report-simulation.md` — live progress tracker
