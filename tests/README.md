# Tests — Cross-Cutting Tests

**Owner:** All

Contains integration, end-to-end, and cross-subsystem tests that span multiple components. Each subsystem also maintains its own unit tests in its directory.

## Structure

```
tests/
├── integration/     # Cross-subsystem integration tests
├── e2e/             # Full-stack end-to-end tests
├── prompts/         # Prompt validation tests
└── conftest.py      # Shared test fixtures
```

## Running Tests

```bash
# Full test suite
./scripts/test.sh

# Specific category
pytest tests/integration/
pytest tests/e2e/
pytest tests/prompts/
```

## Coverage Requirements

- Simulation: >90% branch coverage
- Backend: >80% line coverage
- Frontend: Component tests for all interactive elements
- Prompts: Validation tests for all prompt schemas

## Related

- [Coding Standards — Testing](../docs/guides/coding-standards.md#testing)
- [CONTRIBUTING — Testing Requirements](../CONTRIBUTING.md#testing-requirements)
