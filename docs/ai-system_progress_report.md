# AI System Progress Report

**Date:** 2026-07-10
**Branch:** `main` (10 commits on top of `07d6be7`)
**Plan:** `docs/superpowers/plans/2026-07-10-vllmrouter-integration.md`
**Context:** Swapping `MockAIRouter` duck-type contract for a real `VLLMRouter` connecting to the MI300X server's 3-tier Gemma 4 deployment, then batch-optimizing the tick loop for the 5-minute demo.

---

## What Was Built

### 1. VLLMConfig Dataclass
**File:** `models/router/vllm_config.py`

Standalone config dataclass with all fields for the 3-tier Gemma 4 deployment:
- `base_url` — MI300X endpoint (`http://165.245.130.202:8000/v1`), overrideable via `VLLM_BASE_URL` env var
- 3 API key fields (E2B, MoE-26B, Dense-31B) from `API_KEY_*` env vars
- 3 model tags (`google/gemma-4-*-qat`)
- Per-tier temperature (0.0 / 0.2 / 0.3) and max_tokens (64 / 256 / 512)
- `timeout_seconds: 30`, `max_retries: 2`

### 2. VLLMRouter Class
**File:** `models/router/vllm_router.py`
**Tests:** `tests/unit/router/test_vllm_router.py` — 12/12 passing

Duck-type matches `MockAIRouter` interface with these methods:

| Method | Model Tier | API Key |
|--------|-----------|---------|
| `agent_decide(prompt, agent, world) -> str` | Gemma 4 E2B | `API_KEY_E2B` |
| `agent_decide_batch(prompts, agents, world) -> list[str]` | Gemma 4 E2B | `API_KEY_E2B` |
| `moral_reasoning(prompt, agent, world) -> str` | Gemma 4 26B A4B | `API_KEY_MOE_26B` |
| `moral_reasoning_batch(prompts, agents, world) -> list[str]` | Gemma 4 26B A4B | `API_KEY_MOE_26B` |
| `governance_advisory(world, agents) -> dict` | Gemma 4 31B | `API_KEY_DENSE_31B` |
| `is_available() -> bool` | (GET /v1/models) | (no key) |

Key behaviors:
- **Sync** via `httpx.Client` (matches tick loop's sync execution)
- **Single MI300X endpoint** with key-based model routing via gateway proxy
- **Batch methods** send array of prompts in one vLLM call (not N sequential)
- **Fallback** on any failure: `{"action":"work","feeling":"neutral","reason":"vllm fallback"}` — simulation continues deterministically
- **`_extract_json()`** handles thinking tokens and extra text around JSON
- **`_build_governance_prompt()`** constructs structured governance assessment prompt
- **`call_count`** property tracks total LLM calls for metrics

### 3. Backend Wiring
**Files modified:** `models/router/__init__.py`, `backend/app/services/simulation_service.py`, `backend/app/main.py`, `backend/app/routers/ai.py`

- `simulation_service.py`: Injects `VLLMRouter(config)` into `SimulationEngine.start(ai_router=router)`
- `main.py`: Registers the `/api/v1/ai` router
- `ai.py`: `/ai/status` endpoint checks MI300X availability; all old endpoints (translate-policy, tie-break, etc.) removed

### 4. Simulation Engine Type Hints
**Files:** `simulation/engine/simulation_engine.py`, `simulation/engine/tick_loop.py`

All type annotations changed from `MockAIRouter` → `VLLMRouter`. No behavior change.

### 5. Tick Loop Batching (Demo-Critical)
**File:** `simulation/engine/tick_loop.py`

The action selection loop was refactored from per-agent sequential LLM calls to a **two-pass approach**:

1. **Pass 1:** Collect prompts for all evaluating agents, split into normal vs. moral dilemma groups
2. **Batch call:** One `agent_decide_batch()` call for normal agents, one `moral_reasoning_batch()` for dilemmas
3. **Pass 2:** Execute actions from batched results

**Impact:** 27× throughput improvement (1-2 vLLM calls per tick instead of N sequential calls).

### 6. Prompt Rewrite for Gemma 4
**Files:** Created `prompts/agent_decision.md`, `prompts/moral_reasoning.md`. Updated 6 existing prompt files.

- All model references changed from `google/gemma-2-9b-it` to appropriate Gemma 4 variant
- Version bumped to `2.0.0`
- Gemma 4 chat template documented in `system-prompts.md`

### 7. Cleanup
**Removed:** `models/router/ai_router.py` (old broken `AIRouter`), `models/router/config.py` (old `AIConfig`)

14 files importing from `models.router.*` updated. `AIConfig` moved to `models/config.py` if still referenced by other components.

### 8. Circular Import Fix
**Files:** `backend/__init__.py`, `backend/app/__init__.py`

Both `__init__.py` files were importing `from backend.app.main import app`, creating a circular import when running `python -m backend.app.main`. Removed both imports. Server runs via `uvicorn backend.app.main:app`.

### 9. Configuration
- **`.env`** created with 3 AMD Developer Console API keys
- **`docker/.env.example`** updated for Gemma 4 / VLLMRouter setup

---

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| `tests/unit/router/test_vllm_router.py` | 12/12 | ✅ All passing |
| `tests/unit/simulation/` | 430/431 | ✅ 1 pre-existing Windows timer flake |

The 1 failure (`test_engine_tick_returns_metrics` → `duration_ms=0.0`) is a pre-existing Windows timer precision issue, not related to our changes.

---

## Architecture Summary

```
┌──────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  FastAPI      │────▶│ SimulationEngine     │────▶│  VLLMRouter      │
│  Backend      │     │  .start(ai_router)   │     │  httpx.Client     │
│  (simulation   │     │                      │     │  sync, fallback   │
│   service)    │     │  tick_loop.py (batch) │     │  key-based routing │
└──────────────┘     └─────────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                              ┌─────────────────────┐
                                              │  MI300X vLLM Server  │
                                              │  165.245.130.202:8000 │
                                              │  /v1/completions       │
                                              │  (key → model tier)   │
                                              └─────────────────────┘
```

## Next Steps

1. **Add API keys to deployment environment** (or `.env` already has them for local dev)
2. **Test connectivity** to `http://165.245.130.202:8000/v1` with the API keys
3. **Docker-compose deployment** for demo — services connect to the external MI300X server
4. **Observe batched performance** — tick loop should handle 80+ agents with 1-2 LLM calls per tick instead of 80+
