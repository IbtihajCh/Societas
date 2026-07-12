# Test Suite

Comprehensive tests ensuring simulation determinism, API correctness, and cross-module integration.

## Key Files

- `unit/simulation/` — Engine and agent behavior tests
- `unit/backend/` — FastAPI router and service tests
- `unit/models/` — AI router tests
- `integration/` — Cross-module integration tests
- `performance/` — Benchmarks
- `fixtures/` — Shared pytest fixtures and mock data

## How to Run

**All tests:**
```bash
./scripts/test.sh
```

**With coverage:**
```bash
pytest --cov=simulation --cov=backend --cov=models tests/
```

## Dependencies

- pytest, pytest-cov
- httpx (backend tests)
