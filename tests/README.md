# Tests

**Owner:** All Developers

## Purpose

Comprehensive test suite for the SOCIETAS simulation. Ensures correctness, determinism, and performance across all modules.

## Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── simulation/
│   │   ├── test_engine.py        # Simulation engine tests
│   │   └── test_agents.py        # Agent behavior tests
│   ├── models/
│   │   └── test_ai_router.py     # AI router tests
│   └── backend/
│       └── test_api.py           # API endpoint tests
├── integration/
│   └── test_cross_module.py      # Cross-module integration tests
├── performance/
│   └── test_benchmarks.py        # Performance benchmarks
├── fixtures/
│   └── prompts/
│       └── expected_outputs.json # Expected prompt outputs
└── mock_data/
    ├── sample_agents.json        # Sample agent data
    ├── sample_world_state.json   # Sample world state
    └── sample_policies.json      # Sample policies
```

## Coverage Requirements

- **Simulation:** 90% branch coverage
- **Backend:** 80% line coverage
- **Frontend:** 70% line coverage
- **Prompts:** Schema validation for all outputs

## Running Tests

### All Tests

```bash
./scripts/test.sh
```

### Unit Tests Only

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Performance Tests

```bash
pytest tests/performance/
```

### With Coverage

```bash
pytest --cov=simulation --cov=backend --cov=models tests/
```

## Fixtures

Shared fixtures are defined in `conftest.py`:

- `sample_agent_traits` - 8-dimension trait vector
- `sample_agent_state` - Complete agent state
- `sample_simulation_state` - World state
- `sample_policy` - Government policy
- `load_fixture` - Fixture loader function
- `load_mock_data` - Mock data loader function

## Mock Data

Mock data files in `mock_data/` provide realistic test data:

- `sample_agents.json` - 2 agents with different traits
- `sample_world_state.json` - Tick 100 world state
- `sample_policies.json` - 3 policies (economic, criminal, health)

## Prompt Fixtures

`fixtures/prompts/expected_outputs.json` contains expected outputs for each prompt type:

- `persona-generation` - Persona from traits
- `policy-translation` - Weights from policy
- `tie-break` - Decision from ambiguous state
- `narrative-generation` - News from events

## Writing Tests

### Unit Test Template

```python
def test_feature_name(self, sample_data):
    """Test description."""
    # Arrange
    # TODO: Setup
    
    # Act
    # TODO: Execute
    
    # Assert
    # TODO: Verify
    pass
```

### Integration Test Template

```python
def test_integration_scenario(self):
    """Test cross-module interaction."""
    # TODO: Setup multiple modules
    # TODO: Execute cross-module operation
    # TODO: Verify integration
    pass
```

## Determinism Tests

All simulation tests must verify determinism:

```python
def test_deterministic_behavior(self):
    """Test same seed produces identical results."""
    result1 = run_simulation(seed=42)
    result2 = run_simulation(seed=42)
    assert result1 == result2
```

## Related

- [Coding Standards](../docs/guides/coding-standards.md)
- [CI Workflows](../.github/workflows/ci.yml)
- [Scripts](../scripts/README.md)
