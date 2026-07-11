# SOCIETAS — Simulation Engineer Reference

Commit: `545b6d9` (tech-lead branch)
Date: 2026-07-11

---

## What This Commit Contains

### 1. is_available() returns True (models/router/vllm_router.py)
- `is_available()` no longer performs a real server check — it always returns `True`
- This allows the AI decision path to execute even when the external vLLM server is unreachable
- When the server is unreachable, `_call_vllm` returns `FALLBACK_RESPONSE` (a JSON string with `action: "work"`, `reason: "vllm fallback"`, `feeling: "neutral"`)
- The fallback is returned after timeout+retry logic

### 2. Timeout reduced 30s → 5s (models/router/vllm_config.py)
- `timeout_seconds: 30` → `5`
- `max_retries: 2` → `0`
- Each failed LLM call now takes ~5 seconds instead of ~90 seconds (3 × 30s with retries)

### 3. Enum serialization fixed (shared/types/enums.py)
- `EmploymentStatus` changed from `Enum(auto())` → `StrEnum` with lowercase string values
- `PolicyCategory` changed from `Enum(auto())` → `StrEnum` with lowercase string values
- Frontend `types/api.ts` updated to match

### 4. AgentDetailDTO.recent_actions populated (shared/dto/agent_dto.py, backend/app/services/agent_service.py)
- `recent_actions` field added to `AgentDetailDTO`
- `_agent_to_detail()` now collects up to 10 recent actions from `agent.memories`
- Handles both dict-like and object-like memory entries

### 5. 3 critical AI bugs fixed (simulation/engine/tick_loop.py)
- AI prompt collection now actually appends to `normal_prompts`/`dilemma_prompts` (was always empty)
- `model_type` variable defined before batch loops (was causing NameError → 500)
- LLM log capture added for moral reasoning dilemma agents

### 6. Explain endpoint dead fields fixed (backend/app/routers/explain.py)
- `avg_wealth` → `economic_health`
- `avg_unlust` → `unlust`

### 7. Governance response fixed
- Now returns full `state_dto` alongside `{status, changes}`

---

## Best-of-Both-Worlds Merge (commit c52ddf7)

### Calibration from PR #20 (sim/v2-engine-calibration)

| Change | File | What |
|--------|------|------|
| Health death dice roll (50%) | `needs_calculator.py:211` | `rng.random() < 0.5` before health death |
| Sleep death dice roll (30%) | `needs_calculator.py:215` | `rng.random() < 0.3` before insomnia death |
| Health decay per tick | `needs_calculator.py:160` | `-0.001` every tick |
| Existential death | `needs_calculator.py:224-226` | Death at `purpose_fulfillment < 0.1` |
| Wealth thresholds | `needs_calculator.py:305-311` | POOR < 500, MIDDLE < 5000 |
| INFLATION_DECAY_RATE | `defaults.py:120`, `economy.py:104-105` | Inflation decays each tick |
| Agent sorting | `tick_loop.py:140` | `living_agents.sort(key=lambda a: a.id)` |

### Features preserved from tech-lead

| Feature | File | What |
|---------|------|------|
| Softmax decisions | `decision_engine.py` | Temperature-scaled probability instead of weighted random |
| Memory system | `memory_system.py`, `tick_loop.py` | `collect_tick_memories()` called every tick |
| Media engine | `media_engine.py`, `tick_loop.py` | `process_media_tick()` generates news every 5 ticks |
| Family support | `action_executor.py`, `tick_loop.py` | `_do_support_family()` action |
| Full 24 actions in AI prompts | `decision_engine.py` | All v2-v6 actions available to LLM |
| Deterministic path fix | `tick_loop.py:411` | `execute_action()` was missing — now called |

---

## Architecture: How It All Fits Together

### The 12-Step Tick Loop (simulation/engine/tick_loop.py)

```
Step 1:  Policy effects + aggregate weights
Step 2:  Age progression
Step 3:  Need decay (+ environmental effect multipliers)
Step 3b: Environmental events (famine/drought/abundance)
Step 4:  Welfare + rent + tax + apply_debt_interest
Step 4b: Property market
Step 5:  Emotions → purpose → political influence
Step 5b: Reputation → rumors → communities → gangs → sibling dynamics → family support
Step 6:  Action selection (AI or deterministic, staggered 1/3 per tick)
Step 7:  Movement on grid
Step 8:  Death checks (age/health/starvation/despair/sleep)
Step 9:  Birth (eligible married adults)
Step 10: Metrics + state hash
Step 11: Media engine (news generation every 5 ticks)
Step X:  Memory collection (every tick, stored per agent)
```

### LLM Integration (models/router/vllm_router.py)

When `is_available()` returns `True` and `enable_ai=True`:

| Model | Port | Temp | Purpose |
|-------|------|------|---------|
| Gemma 4 E2B | 8001 | 0.0 | Agent decisions (action + reasoning) |
| Gemma 4 26B A4B | 8002 | 0.2 | Moral reasoning |
| Gemma 4 31B | 8000 | 0.3 | Policy translation + governance advisory |

Config from environment vars (docker-compose.yml):
```
VLLM_BASE_URL_E2B=http://129.212.187.34:8001/v1
VLLM_BASE_URL_MOE_26B=http://129.212.187.34:8002/v1
VLLM_BASE_URL_DENSE_31B=http://129.212.187.34:8000/v1
API_KEY_E2B=societase2b-key3z8
API_KEY_MOE_26B=societasmoe-key7q1
API_KEY_DENSE_31B=societas31-key9x2
```

### Decision Priority Queue (simulation/agents/decision_engine.py)

- **Level 1 (Critical Survival)**: food/water < 0.08 → BUY_FOOD / STEAL / BEG
- **Level 2 (Stability)**: not employed → SEEK_JOB, money < 120 → WORK / BEG
- **Level 3 (Weighted Softmax)**: P(action) = exp(score/T) / Σexp(scores/T)

Softmax scores are modulated by:
- Traits (extraversion → social actions, anger → aggressive actions)
- Employment status → WORK weight
- Emotion state
- Unlust level
- Invalid actions filtered out first

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/simulation/start` | Start simulation |
| POST | `/api/v1/simulation/tick` | Advance 1 tick |
| POST | `/api/v1/simulation/tick-n` | Advance N ticks |
| GET | `/api/v1/simulation/status` | Get status |
| GET | `/api/v1/simulation/state` | Get full state |
| POST | `/api/v1/simulation/start_auto_run` | Auto-run N ticks |
| POST | `/api/v1/simulation/stop_auto_run` | Stop auto-run |
| GET | `/api/v1/agents/` | List agents |
| GET | `/api/v1/agents/{id}` | Agent detail (includes memories + recent_actions) |
| POST | `/api/v1/policies/` | Create policy |
| GET | `/api/v1/policies/` | List policies |
| DELETE | `/api/v1/policies/{id}` | Revoke policy |
| POST | `/api/v1/governance/apply` | Apply tax/welfare/food changes |
| GET | `/api/v1/governance/suggestions` | Get suggested policies |
| POST | `/api/v1/explain` | Natural language Q&A about simulation state |
| GET | `/api/v1/metrics/` | Historical metrics |
| GET | `/api/v1/metrics/dashboard` | Full dashboard data |
| GET | `/api/v1/saves/` | List saves |
| POST | `/api/v1/saves/save` | Save current state |
| POST | `/api/v1/saves/load/{id}` | Load a save |
| WS | `/ws` | WebSocket for real-time events |

---

## Key Constants (shared/constants/defaults.py)

### Death
| Constant | Value | What |
|----------|-------|------|
| `STARVATION_DEATH_THRESHOLD` | 0.02 | Hunger below this = death |
| `DEHYDRATION_DEATH_THRESHOLD` | 0.02 | Thirst below this = death |
| `HEALTH_DEATH_THRESHOLD` | 0.05 | Health below this = death (50% dice roll) |
| `DESPAIR_DEATH_THRESHOLD` | 0.02 | Happiness below this = death |
| `SLEEP_DEATH_THRESHOLD` | 0.05 | Insomnia severity above this = death (30% dice roll) |
| `AGE_MORTALITY_BASE` | 0.003 | Base per-tick mortality for elderly |
| `AGE_MORTALITY_ELDERLY` | 0.015 | Elderly mortality rate |
| `EXISTENTIAL_DEATH_CHANCE` | 0.02 | Purpose < 0.1 triggers this |

### Economy
| Constant | Value | What |
|----------|-------|------|
| `WELFARE_AMOUNT` | 8.0 | Base welfare payment |
| `RENT_POOR` | 5.0 | Rent for poor tier |
| `RENT_MIDDLE` | 15.0 | Rent for middle tier |
| `RENT_RICH` | 30.0 | Rent for rich tier |
| `DEBT_INTEREST_RATE` | 0.05 | Per-tick debt interest |
| `INFLATION_DECAY_RATE` | 0.001 | Per-tick inflation rate decay |
| `SCARCITY_BASE` | 0.02 | Need decay baseline |

### Social
| Constant | Value | What |
|----------|-------|------|
| `REPUTATION_DECAY_RATE` | 0.001 | Per-tick reputation decay |
| `GOSSIP_SPREAD_CHANCE` | 0.1 | Chance gossip spreads to connection |
| `COMMUNITY_RECLUSTER_INTERVAL` | 10 | Recluster communities every N ticks |
| `COMMUNITY_MIN_SIZE` | 3 | Minimum community size |
| `COMMUNITY_MAX_SIZE` | 15 | Maximum community size |
| `EXPLOITATION_THRESHOLD` | 0.6 | Tension threshold for exploitation |
| `CONFLICT_THRESHOLD` | 0.5 | Tension threshold for conflict |
| `GANG_FORMATION_ELIGIBLE` | 5 | Agents needed to form a gang |
| `GANG_FORMATION_PROB` | 0.15 | Probability of gang formation |
| `RIOT_PROTEST_THRESHOLD` | 0.3 | Protest intensity for riot |
| `RIOT_UNLUST_THRESHOLD` | 0.5 | Unlust threshold for riot |

### Environment
| Constant | Value | What |
|----------|-------|------|
| `ENV_FAMINE_PROB` | 0.15 | Per-tick famine probability |
| `ENV_DROUGHT_PROB` | 0.15 | Per-tick drought probability |
| `ENV_ABUNDANCE_PROB` | 0.10 | Per-tick abundance probability |
| `ENV_MILD_PROB` | 0.25 | Per-tick mild shortage probability |
| `ENV_FAMINE_FOOD` | 0.15 | Food availability during famine |
| `ENV_DROUGHT_WATER` | 0.15 | Water availability during drought |

### Lifecycle
| Constant | Value | What |
|----------|-------|------|
| `CHILD_MIN_AGE` | 0 | Child bracket start |
| `CHILD_MAX_AGE` | 18 | Child bracket end |
| `YOUNG_ADULT_MIN_AGE` | 19 | Young adult bracket start |
| `YOUNG_ADULT_MAX_AGE` | 40 | Young adult bracket end |
| `MIDDLE_AGE_MIN_AGE` | 41 | Middle age bracket start |
| `MIDDLE_AGE_MAX_AGE` | 65 | Middle age bracket end |
| `ELDERLY_AGE_MIN` | 66 | Elderly bracket start |
| `MARRIAGE_MIN_AGE` | 19 | Minimum marriage age |
| `MARRIAGE_MAX_AGE` | 65 | Maximum marriage age |
| `BIRTH_CHANCE_BASE` | 0.002 | Per-tick birth probability |

---

## Docker Setup

```powershell
cd C:\Hackathons\AMD-v2\docker

# Build
docker compose build backend   # Python 3.14-slim, 34 packages
docker compose build frontend  # Node 20-alpine, 680 packages

# Run
docker compose up -d backend frontend
# Backend: http://localhost:8000
# Frontend: http://localhost:3000

# Test
curl -s http://localhost:8000/api/v1/health
# → {"status":"healthy","service":"societas-backend"}
```

---

## Known Issues (not blocking)

| Issue | Severity | Details |
|-------|----------|---------|
| `impact_deltas` never populated on PolicyResponseDTO | 🟢 Low | Declared in DTO, never written by service |
| `getAgentHistory` is a stub | 🟢 Low | Always returns empty `history: []` |
| LSP errors in editor | 🟢 Low | All are PYTHONPATH resolution false positives |
| Frontend warnings (containerRef) | 🟢 Low | `react-hooks/exhaustive-deps` — harmless |
| `resources` typing mismatch | 🟢 Low | Declared as `Dict[str, float]` but contains enums |
