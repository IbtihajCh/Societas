# Simulation Engine

Core deterministic agent-based modeling engine for SOCIETAS. Manages agent psychology, economic systems, needs fulfillment, and policy effects.

## Key Files

- `engine/simulation_engine.py` — `ISimulationEngine` implementation
- `engine/tick_loop.py` — 10-step tick cycle orchestration
- `agents/agent.py` — Agent class with traits and state
- `agents/decision_engine.py` — E2B hybrid prompts + deterministic fallback
- `world/world_state.py` — World state and economy management
- `policies/policy_engine.py` — Policy application and impact calculation

## How to Run

```python
from simulation.engine.simulation_engine import SimulationEngine
from simulation.engine.config import SimulationConfig

engine = SimulationEngine(SimulationConfig(population_size=80, seed=42))
engine.start()
result = engine.tick()
```

## How to Test

```bash
pytest tests/unit/simulation/ -v
```

## Dependencies

- Python 3.11+, numpy
- `shared/` schemas and constants
