# API Contracts

Canonical OpenAPI spec, JSON schemas, and examples ensuring consistency across frontend, backend, and simulation.

## Key Files

- `api/openapi.yaml` — OpenAPI 3.0 REST specification
- `schemas/` — `agent_state.json`, `simulation_state.json`, `policy.json`, `decision_request.json`, `decision_response.json`, `news_event.json`
- `examples/` — Valid instance data for each schema

## How to Use

**Backend validation:**
```python
import jsonschema, json
schema = json.load(open("contracts/schemas/agent_state.json"))
jsonschema.validate(instance=data, schema=schema)
```

**Frontend type generation:**
```bash
npx json-schema-to-typescript -i contracts/schemas/*.json -o src/types/contracts/
```

## Dependencies

- jsonschema (Python)
- json-schema-to-typescript (Node, optional)
