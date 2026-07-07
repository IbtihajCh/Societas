# Mock Implementations

**Owner:** Infrastructure / DevOps Engineer

## Purpose

Mock implementations of core interfaces for parallel development. Enables frontend and other teams to develop against realistic fake data without waiting for real implementations.

## Available Mocks

| Mock | Interface | Usage |
|------|-----------|-------|
| `MockSimulationEngine` | `ISimulationEngine` | Frontend development |
| `MockAIRouter` | `IAIRouter` | Simulation development without vLLM |
| `mock_api_server.py` | Full REST API | Frontend development |

## Usage

### Mock API Server

Run the mock API server for frontend development:

```bash
uvicorn tools.mocks.mock_api_server:app --port 8000
```

This provides all SOCIETAS API endpoints with realistic fake data.

### Mock Engine in Tests

```python
from tools.mocks import MockSimulationEngine

engine = MockSimulationEngine()
state = engine.get_state()  # Returns mock data
```

### Mock AI Router in Tests

```python
from tools.mocks import MockAIRouter

router = MockAIRouter()
persona = await router.generate_persona(traits)  # Returns mock persona
```

## Endpoints

The mock API server implements all endpoints from `contracts/api/openapi.yaml`:

- `GET /api/v1/health` - Health check
- `GET /api/v1/simulation/status` - Simulation status
- `POST /api/v1/simulation/start` - Start simulation
- `POST /api/v1/simulation/stop` - Stop simulation
- `POST /api/v1/simulation/tick` - Advance tick
- `GET /api/v1/simulation/state` - World state
- `POST /api/v1/simulation/reset` - Reset simulation
- `GET /api/v1/policies` - List policies
- `POST /api/v1/policies` - Create policy
- `GET /api/v1/policies/{id}` - Get policy
- `DELETE /api/v1/policies/{id}` - Revoke policy
- `GET /api/v1/metrics` - Get metrics
- `GET /api/v1/metrics/dashboard` - Dashboard data
- `GET /api/v1/agents` - List agents
- `GET /api/v1/agents/{id}` - Get agent
- `GET /api/v1/agents/{id}/history` - Agent history
- `WS /ws` - WebSocket connection

## Future Work

- Load mock data from `contracts/examples/` for more realistic responses
- Add configurable latency simulation
- Add error simulation (500 responses, timeouts)
- Add scenario presets (happy society, crisis, etc.)
