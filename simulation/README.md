# Simulation Module

**Owner:** Simulation Engineer

## Purpose

Core deterministic simulation engine for SOCIETAS. Implements agent-based modeling with psychological traits, economic systems, needs fulfillment, and policy application.

## Status: Implemented (v1.0)

**500 tests passing.** All 6 phases complete (plus P1-P5 tuning + engine integration). See [implementation-summary.md](../docs/implementation-summary.md) for full details.

## Responsibilities

- Manage autonomous agents with decision-making capabilities
- Simulate economic systems (employment, wealth, markets)
- Track agent needs and psychological states
- Apply government policies and calculate effects
- Execute deterministic tick-based simulation
- Collect and aggregate simulation metrics
- Publish events for other subsystems

## Dependencies

- `shared/` - Shared schemas, types, and interfaces
- `numpy` - Deterministic random number generation

## Module Structure

```
simulation/
├── agents/
│   ├── agent.py              # Agent class (IAgent interface)
│   ├── agent_registry.py     # Agent storage and lookup
│   ├── agent_factory.py      # Agent creation with Beta traits
│   ├── needs_calculator.py   # 13-need decay system
│   ├── unlust_engine.py      # Freudian Unlust formula
│   ├── emotion_engine.py     # 5-state emotion machine
│   ├── decision_engine.py    # E2B hybrid prompts + fallback
│   ├── action_executor.py    # 14 action implementations
│   └── adler_engine.py       # Adlerian social comparison
├── world/
│   ├── world_state.py        # World state management
│   ├── grid.py               # 20×20 toroidal grid
│   ├── economy.py            # Rent, welfare, money flow
│   └── metrics_calculator.py # World metrics + state hash
├── policies/
│   ├── policy_engine.py      # IPolicyEngine interface
│   ├── policy_effects.py     # ImpactDelta application
│   └── policy_fallback.py    # Keyword-based translation
├── engine/
│   ├── config.py             # SimulationConfig
│   ├── simulation_engine.py  # ISimulationEngine — tick() delegates to run_tick(), start() initializes agents
│   ├── mock_ai_router.py     # Deterministic LLM mock (trait-aware decisions)
│   └── tick_loop.py          # 10-step tick cycle wiring all modules
├── events/
│   └── event_bus.py          # Synchronous event bus
├── metrics/
│   └── metrics_collector.py  # Tick-level metric collection
├── scheduler/
│   └── tick_scheduler.py     # Agent execution ordering
└── README.md
```

## Public Interfaces

### SimulationEngine
- `tick()` - Advance simulation by one tick
- `reset()` - Reset to initial state
- `apply_policy()` - Apply a government policy
- `get_state()` - Get current world state
- `get_metrics()` - Get simulation metrics
- `get_agent()` - Get specific agent state
- `get_agents()` - Get all agents

### run_tick (tick_loop.py)
- `run_tick(tick_number, agents, world, rng, policies, ai_router) -> TickResult`
- Executes the full 10-step tick cycle
- Optional `ai_router` for LLM integration (use `MockAIRouter` for testing)

### Key Functions (importable from sub-modules)
- `agent_factory.create_initial_population(n, rng)` — create N agents
- `needs_calculator.decay_needs(agent, world, rng)` — decay all 13 needs
- `unlust_engine.compute_unlust(agent)` — compute Freudian Unlust
- `emotion_engine.update_emotion(agent, rng)` — update emotion state machine
- `decision_engine.deterministic_fallback(agent, world, rng)` — fallback action selection
- `action_executor.execute_action(agent, action, world, all_agents, rng)` — execute any action
- `metrics_calculator.compute_state_hash(world, agents)` — SHA-256 state hash

## Architecture: E2B Hybrid

The simulation engine implements the E2B Hybrid architecture (ADR-005):
- **Deterministic engine**: physics, needs, emotions, economy — all deterministic via `DeterministicRNG`
- **Gemma 4 E2B** (planned): agent brain — receives structured prompt, returns action
- **Gemma 4 26B A4B** (planned, thinking mode): moral reasoning for ethical dilemmas
- **Gemma 4 31B** (planned, thinking mode): governance advisor + policy translation
- **Deterministic fallback**: 3-level priority queue when LLM unavailable
- **Staggered scheduling**: 1/3 of agents re-evaluate per tick (agent_id % 3)

## Configuration

All values are **tweakable** via constants in `shared/constants/defaults.py` and `shared/constants/simulation_constants.py`:
- Simulation: seed, population size, grid size, tick rate
- Agents: trait distributions (Beta params), wealth class distribution
- Needs: 10 decay rates, scarcity multiplier
- Unlust: 5 weights, morality gate, Thanatos threshold
- Emotions: 5 thresholds, 3 timers, resilience effect
- Economy: 11 salary ranges, tax rate, welfare, food cost, rent
- Policy: 8 fallback keyword policies with per-class deltas
- Death: 3 thresholds, despair mortality rate

No hardcoded values — all from config. See the constants files for the full list.

## Quick Start

```python
from simulation.engine.simulation_engine import SimulationEngine
from simulation.engine.config import SimulationConfig
from simulation.engine.mock_ai_router import MockAIRouter

engine = SimulationEngine(SimulationConfig(population_size=80, seed=42))
engine.start(ai_router=MockAIRouter(seed=42))
result = engine.tick()
```

See [docs/engine-reference.md](../docs/engine-reference.md) for detailed usage from other teams (backend, AI, frontend).
