# Shared Schemas & Types

Canonical types, schemas, interfaces, and constants used across all SOCIETAS subsystems.

## Key Files

- `schemas/` — `AgentState`, `SimulationState`, `Policy`, `TickResult`
- `dto/` — Python DTOs and TypeScript type mirrors
- `interfaces/` — `ISimulationEngine`, `IAgent`, `IPolicyEngine`, `IAIRouter`
- `constants/` — Simulation defaults, thresholds, Beta trait parameters
- `utilities/deterministic_rng.py` — Seeded `numpy.random.Generator` wrapper

## How to Use

Import directly from `shared/` in any subsystem:

```python
from shared.schemas import AgentState, SimulationState
from shared.interfaces import ISimulationEngine
```

## Dependencies

- None (foundational module)
- Consumed by: `simulation/`, `backend/`, `frontend/`, `models/`
