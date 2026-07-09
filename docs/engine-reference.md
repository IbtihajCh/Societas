# SOCIETAS Engine Reference — Concise Guide

**Version:** 1.0 (matches simulation engine v1.0)  
**Date:** 2026-07-09  
**Audience:** Backend, AI, Frontend, DevOps agents  
**Purpose:** Quick reference for integrating with the simulation engine  
**Full guide:** `docs/SOCIETAS_Simulation_Implementation_Guide.md` (3500+ lines)

---

## 1. Architecture in 30 Seconds

```
Layer 1: Deterministic Engine (Python/NumPy) → needs, emotions, economy, grid, death
Layer 2: AI (Gemma 4 via vLLM)             → E2B (brains), 26B A4B (moral), 31B (policy)
Layer 3: Presentation (Next.js)             → dashboard, agent grid, spotlight
```

- Everything in Layer 1 is **deterministic** via `DeterministicRNG` (seeded numpy)
- AI is optional — deterministic fallback is always available
- No GPU required for development — use `MockAIRouter` for AI simulation

---

## 2. Engine Interface (`ISimulationEngine`)

File: `shared/interfaces/i_simulation_engine.py`

| Method | Signature | What it does | When to call |
|---|---|---|---|
| `start()` | `(ai_router: Optional[MockAIRouter] = None) -> None` | Creates agents, seeds RNG, sets `_is_running = True` | Once after construction, before first `tick()` |
| `tick()` | `() -> TickResult` | Advances simulation by 1 tick (10-step loop) | After `start()`; raises `RuntimeError` otherwise |
| `reset()` | `(seed: Optional[int] = None) -> None` | Full state reset; must call `start()` again | Between simulations |
| `apply_policy()` | `(policy: Policy) -> None` | Applies a government policy (ImpactDeltas + weights) | Any time during simulation |
| `revoke_policy()` | `(policy_id: str) -> None` | Removes an active policy | Any time during simulation |
| `get_state()` | `() -> SimulationState` | Returns current world state (mutable ref) | After start/tick |
| `get_metrics()` | `() -> SimulationMetrics` | Aggregated simulation metrics | After any tick |
| `get_agent()` | `(agent_id: AgentId) -> Optional[AgentState]` | Single agent state | Any time |
| `get_agents()` | `() -> List[AgentState]` | All agents (alive + dead) | Any time |
| `get_current_tick()` | `() -> TickNumber` | Current tick counter | Any time |
| `is_running()` | `() -> bool` | Whether simulation is active | Any time |

**NOTE:** `start()` was added after v0.1 — the engine no longer auto-initializes in `__init__`. Backend must call `engine.start()` after construction.

---

## 3. `TickResult` Schema

File: `shared/schemas/tick_result.py`

| Field | Type | Description |
|---|---|---|
| `tick` | `TickNumber` | Tick number (int) |
| `agent_actions` | `List[AgentActionResult]` | Per-agent: agent_id, action, outcome, score_delta, metadata |
| `state_changes` | `Dict[str, float]` | Key world deltas: crime_rate, protest_intensity, unemployment_rate, avg_unlust, population |
| `events_generated` | `List[EventId]` | Event IDs from this tick (currently empty — events not wired) |
| `ambiguity_count` | `int` | Agents that hit moral dilemmas |
| `ai_calls` | `int` | LLM calls made this tick |
| `duration_ms` | `float` | Wall-clock duration in ms |
| `state_hash` | `str` | SHA-256 of deterministic state (for reproducibility checks) |

---

## 4. AgentState Key Fields

File: `shared/schemas/agent_state.py` — 40+ fields grouped by category.

| Category | Fields |
|---|---|
| **Identity** | `id: AgentId`, `persona: str`, `gender: Gender`, `culture: Culture`, `born_tick: TickNumber`, `age: int`, `is_alive: bool` |
| **Traits** (8, Beta-distributed) | `morality`, `creativity`, `ambition`, `resilience`, `dominance_urge`, `anger_tendency`, `extraversion`, `risk_tolerance` (all `float 0-1`) |
| **Needs** (13) | Food, Water, Sleep, SexualTension, Safety, FinancialSecurity, Shelter, SocialConnection, FamilyBond, RomanticBond, SelfEsteem, Reputation, InferiorityGap (all `float 0-1`, lower = more urgent) |
| **Emotions** | `primary: EmotionType` (HAPPY/NORMAL/SAD/ANGRY/DESPAIR), `happiness_score: float`, `emotion_timer: int` |
| **Resources** | `money: float`, `base_salary: float`, `employed: bool`, `education: EducationLevel`, `property: bool`, `health: float`, `job_type: JobType` |
| **Social** | `social_connections: List[AgentId]`, `spouse: Optional[AgentId]`, `enemies: List[AgentId]`, `community_id: Optional[str]` |
| **Decision** | `last_action: ActionType`, `last_reasoning: str`, `decision_scores: AgentDecisionScores` (top_action, top_score, second_score, `is_ambiguous()`) |
| **Grid** | `grid_x: GridCoordinate`, `grid_y: GridCoordinate` (20×20 toroidal, both 0-19) |
| **Tracking** | `unlust: float`, `good_acts: int`, `crimes_committed: int`, `notoriety: float`, `trust_in_govt: float`, `protest_count: int` |

---

## 5. SimulationState (World)

File: `shared/schemas/simulation_state.py`

| Field | Type | Default | Description |
|---|---|---|---|
| `time_step` | `TickNumber` | 0 | Current tick |
| `population` | `int` | 0 | Number of agents |
| `economic_health` | `float` | 0.5 | 0-1 scale |
| `social_cohesion` | `float` | 0.5 | 0-1 scale |
| `public_order` | `float` | 0.5 | 0-1 scale |
| `innovation_index` | `float` | 0.5 | 0-1 scale |
| `food_availability` | `float` | 0.85 | Impacts food cost |
| `water_availability` | `float` | 0.90 | Impacts need decay |
| `crime_rate` | `float` | 0.05 | Fraction of agents committing crime |
| `protest_intensity` | `float` | 0.0 | Societal unrest level |
| `unemployment_rate` | `float` | 0.10 | Fraction unemployed |
| `tax_rate` | `float` | 0.15 | Income tax fraction |
| `welfare_enabled` | `bool` | False | Welfare system active |
| `welfare_amount` | `float` | 8.0 | Per-tick welfare payment |
| `economy` | `EconomyState` | — | GDP, market_stability, etc. |
| `crime` | `CrimeState` | — | Detailed crime metrics |

---

## 6. The 10-Step Tick Loop

File: `simulation/engine/tick_loop.py` — function `run_tick()`

```python
def run_tick(tick_number, agents, world, rng, policies=None, ai_router=None) -> TickResult
```

| Step | What happens | Key function |
|---|---|---|
| 1 | Publish TickStartedEvent (logged, not wired to bus) | — |
| 2 | Apply active policy effects (ImpactDeltas per wealth class) | `apply_all_policies()` |
| 3 | Decay all 13 needs (scarcity-modified rates) | `decay_needs()` |
| 4 | Process economy: welfare payments, rent, salary | `process_economy_tick()` |
| 5 | Update emotions: unlust → happiness → sleep reset → state machine | `compute_unlust()`, `compute_happiness()`, `update_emotion()` |
| 6 | **Action selection + execution** (staggered, see §7) | `decision_engine.*`, `execute_action()` |
| 7 | Movement on 20×20 toroidal grid | `move_agent()` |
| 8 | Death check (food/water/health/despair) | `check_death()` |
| 9 | Update world metrics (crime rate, protest, etc.) | `update_world_metrics()` |
| 10 | Compute SHA-256 state hash → TickResult | `compute_state_hash()` |

---

## 7. How AI Integration Works

### Staggered Scheduling
Only 1/3 of agents re-evaluate per tick: `agent.id % 3 == tick_number % 3`.  
Non-scheduled agents repeat their `last_action`.

### Decision Flow (per scheduled agent)

```
agent state + world + nearby_counts
        │
        ▼
  ┌─ AI router available? ─┐
  │         │               │
  │        Yes              No
  │         │               │
  │    ┌────┴────┐          │
  │  Moral       │          │
  │  Dilemma?    │          │
  │  (5 checks)  │          │
  │    │         │          │
  │   Yes        No         │
  │    │         │          │
  │  26B A4B   E2B          │
  │    │         │          │
  │    └────┬────┘          │
  │         │               │
  │    Parse response       │
  │    │           │        │
  │  Valid?   Invalid/      │
  │           unparseable   │
  │    │           │        │
  │  Execute  deterministic │
  │           fallback      │
  └─────────────────────────┘
        │
        ▼
  AgentActionResult
```

### Moral Dilemma Conditions
Any of these triggers escalation to 26B A4B (thinking mode):
1. Food need < 0.15 AND agent has low money
2. Morality > 0.5 AND severe need deprivation
3. Unlust > 0.5 AND low trust in government
4. Multiple needs critically low
5. Emotional state is DESPAIR

### Deterministic Fallback (3-level priority)
1. **Critical survival** (food/water < 0.08): buy_food, steal, or beg
2. **Employment**: seek_job if unemployed
3. **Weighted selection** across 14 actions based on needs + traits

### MockAIRouter
File: `simulation/engine/mock_ai_router.py`

Returns deterministic JSON in same format as real Gemma: `{"action":"...","feeling":"...","reason":"..."}`  
Uses agent personality (extraversion, morality, anger, ambition) for weighted selection — more realistic than pure fallback.  
**Use for all testing without GPU.**

---

## 8. IAIRouter Interface (for AI Team)

File: `shared/interfaces/i_ai_router.py` — 6 abstract methods (original interface)

The **VLLMRouter** must implement these **8 methods** (extended for the engine):

| Method | Returns | Model | Purpose |
|---|---|---|---|
| `agent_decide(prompt, agent, world)` | `dict` (action, feeling, reason) | E2B | Agent brain — structured prompt → action |
| `agent_decide_batch(states[])` | `list[dict]` | E2B | Batched agent decisions |
| `moral_reasoning(prompt, agent, world)` | `dict` (action, reasoning, feeling) | 26B A4B | Moral dilemma resolution |
| `moral_reasoning_batch(states[])` | `list[dict]` | 26B A4B | Batched moral reasoning |
| `governance_advisory(world, policies)` | `dict` (assessment, recommendation, watch_items) | 31B | Policy advisor |
| `translate_policy(text, weights, world)` | `dict` (ImpactDeltas, PolicyWeights, changes) | 31B | Policy text → game mechanics |
| `generate_news(events, state_deltas)` | `dict` (headline, body, category) | 31B | News narration |
| `is_available()` | `bool` | — | Health check |

**Contract:** Return `None`/empty on failure. Engine handles fallback gracefully.  
**Spec:** `simulation/vllm-integration-spec.md` (was `simulation/test_reports/vllm-integration-spec.md`)  
**Mock:** `simulation/engine/mock_ai_router.py` — already implements the interface for testing.

---

## 9. Policy System

### Dual Model

**ImpactDeltas** — per-tick effects per wealth class (poor/middle/rich):
```python
@dataclass
class ImpactDelta:
    food_availability: float = 0.0    # delta per tick
    water_availability: float = 0.0
    crime_rate: float = 0.0
    unemployment_rate: float = 0.0
    public_order: float = 0.0
    happiness: float = 0.0
    money_delta: float = 0.0          # direct money transfer
```

**PolicyWeights** — modifies agent utility function:
```python
@dataclass
class PolicyWeights:
    action_weights: Dict[ActionType, float]  # per-action utility modifiers
    need_weights: Dict[NeedType, float]      # per-need priority modifiers
```

### Policy Flow
```
User text → translate_policy() → {ImpactDeltas + PolicyWeights} → apply each tick
```

Fallback policies (8 built-in) use keyword matching: `shared/constants/policy_fallback.py`

---

## 10. Configuration

All values in `shared/constants/defaults.py` and `shared/constants/simulation_constants.py`.  
Everything tweakable — no hardcoded values in engine.

| Category | Key constants | File |
|---|---|---|
| **Simulation** | `DEFAULT_POPULATION_SIZE=1000`, `DEFAULT_SIMULATION_SEED=42`, `GRID_SIZE=20` | `defaults.py` |
| **Needs decay** | 10 decay rates (e.g., `FOOD_DECAY_RATE=0.018`, `WATER_DECAY_RATE=0.014`) | `defaults.py` |
| **Unlust** | 5 weights (`UNLUST_FOOD_WEIGHT=0.28`, ...), `UNLUST_MORALITY_GATE=0.58` | `defaults.py` |
| **Emotion** | `HAPPY_THRESHOLD=0.65`, `SAD_THRESHOLD=0.35`, 3 timers (2-4 ticks) | `defaults.py` |
| **Economy** | 11 salary ranges, `BASE_FOOD_COST=10`, `DEFAULT_TAX_RATE=0.15`, welfare | `defaults.py` |
| **Death** | `FOOD_DEATH_THRESHOLD=0.02`, `WATER_DEATH_THRESHOLD=0.02`, `DESPAIR_MORTALITY_RATE=0.004` | `defaults.py` |
| **Traits** | Beta distribution params, wealth class distribution, education by wealth | `simulation_constants.py` |

`SimulationConfig` (in `simulation/engine/config.py`):
```python
@dataclass
class SimulationConfig:
    population_size: int = 1000
    seed: Optional[int] = 42
    tick_rate_ms: int = 1000
    max_ticks: int = 10000
    agent_lifespan_ticks: int = 5000
    initial_wealth: float = 100.0
    ambiguity_threshold: float = 0.05
    enable_ai_escalation: bool = True
    log_level: str = "INFO"
```

---

## 11. How to Run

### Create engine and run ticks
```python
from simulation.engine.config import SimulationConfig
from simulation.engine.simulation_engine import SimulationEngine

engine = SimulationEngine(config=SimulationConfig(population_size=80, seed=42))
engine.start()

for _ in range(10):
    result = engine.tick()
    print(f"Tick {result.tick}: hash={result.state_hash[:16]}...")
```

### With MockAIRouter (AI simulation without GPU)
```python
from simulation.engine.mock_ai_router import MockAIRouter

engine = SimulationEngine(SimulationConfig(population_size=80, seed=42))
router = MockAIRouter()
engine.start(ai_router=router)

result = engine.tick()
print(f"AI calls: {result.ai_calls}, Ambiguity: {result.ambiguity_count}")
```

### Apply a policy
```python
from shared.schemas.policy import Policy, GovernmentPolicy

policy = GovernmentPolicy(
    policy_id="welfare_001",
    name="Universal Basic Welfare",
    description="Provide basic income support",
    impact_deltas={...},  # ImpactDeltas per wealth class
)
engine.apply_policy(policy)
```

### Get metrics
```python
metrics = engine.get_metrics()
state = engine.get_state()
agent = engine.get_agent(AgentId("42"))
```

### Run tests
```bash
pytest tests/unit/simulation/ -v --tb=short
pytest tests/unit/shared/ -v --tb=short
pytest --cov --cov-branch --cov-fail-under=90  # CI gate: 90% branch coverage
```

---

## 12. What Each Team Needs to Do

Detailed in `docs/cross-team-integration-guide.md`. Summary:

| Team | Task | Priority |
|---|---|---|
| **Backend** | Call `engine.start()` after construction | CRITICAL |
| **Backend** | Fix `agent_results` → `agent_actions` in `advance_tick()` | CRITICAL |
| **Backend** | Fix `stop_simulation()` — use public `stop()` method | CRITICAL |
| **Backend** | Persist engine globally (DI container loses it between requests) | CRITICAL |
| **Backend** | Wire WebSocket broadcasts into tick lifecycle | Required |
| **Backend** | Audit DTO field mapping (new fields available) | Recommended |
| **AI** | Implement `VLLMRouter` (8 methods, 3 models) | Required |
| **AI** | Update prompt files to match new schemas | Required |
| **AI** | Add Fireworks AI fallback when no GPU | Recommended |
| **Frontend** | Align TypeScript types with new DTO fields | Required |
| **Frontend** | Handle WebSocket events (`tick_completed`, `agent_acted`) | Required |
| **Frontend** | Build dashboard panels with wealth-stratified metrics | Recommended |
| **DevOps** | Fix Dockerfiles to include `/shared/` | CRITICAL |
| **DevOps** | Multi-model vLLM compose (3 containers, sequential launch) | Required |
| **DevOps** | Ensure PYTHONPATH resolves `shared.*` imports | Required |

---

## 13. File Map

```
simulation/
├── agents/
│   ├── agent.py              # IAgent interface implementation
│   ├── agent_registry.py     # Agent storage/lookup
│   ├── agent_factory.py      # create_initial_population() — Beta-distributed traits
│   ├── needs_calculator.py   # 13-need decay, death checks, job loss
│   ├── unlust_engine.py      # Freudian Unlust formula
│   ├── emotion_engine.py     # 5-state emotion machine (HAPPY→NORMAL→SAD→ANGRY→DESPAIR)
│   ├── decision_engine.py    # Prompts, parsing, validation, fallback
│   ├── action_executor.py    # 14 actions (work, steal, befriend, protest...)
│   └── adler_engine.py       # Adlerian social comparison (inferiority/superiority)
├── world/
│   ├── world_state.py        # WorldStateManager — holds SimulationState
│   ├── grid.py               # 20×20 toroidal grid
│   ├── economy.py            # Rent, welfare, salary, food cost
│   └── metrics_calculator.py # World metrics + SHA-256 state hash
├── policies/
│   ├── policy_engine.py      # Policy storage, apply/revoke
│   ├── policy_effects.py     # Apply ImpactDeltas each tick
│   └── policy_fallback.py    # 8 keyword-based fallback policies
├── engine/
│   ├── config.py             # SimulationConfig dataclass
│   ├── simulation_engine.py  # ISimulationEngine implementation (237 lines)
│   ├── mock_ai_router.py     # Deterministic trait-aware AI mock (299 lines)
│   └── tick_loop.py          # 10-step run_tick() (198 lines)
├── events/
│   └── event_bus.py          # Synchronous pub/sub event bus
├── metrics/
│   └── metrics_collector.py  # Tick-level metric aggregation
├── scheduler/
│   └── tick_scheduler.py     # Agent execution ordering
├── test_reports/             # 30+ scenario JSON + runner
└── vllm-integration-spec.md  # Full vLLM spec for AI Engineer
```

---

## 14. Test Suite

| Command | What it covers |
|---|---|
| `pytest tests/unit/simulation/ -v` | 475+ simulation unit tests |
| `pytest tests/unit/shared/ -v` | Shared schema/interface tests |
| `pytest --cov --cov-branch --cov-fail-under=90` | CI gate: 90% branch coverage |
| `python simulation/test_reports/runner.py a1_default` | Run a full scenario and generate report |

**Key test files:** `tests/unit/simulation/test_engine.py`, `test_agents.py`, `test_needs.py`, `test_emotion.py`, `test_economy.py`, `test_policies.py`

**Determinism tests:** Verify `same seed + same config = identical state_hash` across runs.

---

*For implementation formulas, parameters, and detailed design, see `docs/SOCIETAS_Simulation_Implementation_Guide.md`.*
