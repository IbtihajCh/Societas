# Coding Standards

SOCIETAS follows strict coding standards to ensure consistency, explainability, and quality across all subsystems.

---

## Language Standards

### Python (Simulation, Backend)

- **Version:** Python 3.11+
- **Formatter:** `ruff format`
- **Linter:** `ruff check`
- **Type checker:** `mypy --strict`
- **Test runner:** `pytest`

**Conventions:**
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints everywhere (`def process(agent: Agent) -> Decision:`)
- Docstrings: Google style for public APIs, descriptive for complex logic
- No wildcard imports (`from module import *`)
- Prefer dataclasses or Pydantic models over plain dicts for structured data
- Abstract base classes for plugin-like subsystems

### TypeScript / JavaScript (Frontend)

- **Version:** TypeScript 5+
- **Formatter:** Prettier
- **Linter:** ESLint with `@typescript-eslint`
- **Test runner:** Vitest or Jest

**Conventions:**
- Strict TypeScript mode (`strict: true`)
- Functional components with hooks
- Named exports over default exports
- Co-located tests (`Component.test.tsx`)
- CSS Modules or Tailwind utility classes

---

## Simulation-Specific Standards

### Determinism

```python
# GOOD: Seeded RNG
rng = numpy.random.default_rng(seed=run_seed)
value = rng.uniform(0, 1)

# BAD: Unseeded RNG
value = random.random()
```

```python
# GOOD: Deterministic float comparison
if abs(a - b) < 1e-10:
    pass

# BAD: Platform-dependent float comparison
if a == b:
    pass
```

### Explainability

Every decision pipeline step must log:
- Input state (relevant portion)
- Computed scores
- Which path was taken (deterministic vs. escalated)
- Final decision and rationale

---

## AI / Prompt Standards

- Every prompt in `prompts/` must document its input and output schema
- Prompt outputs must be validated against the schema before use
- Never interpolate untrusted user input directly into prompts
- Version prompts in Git; changes require review

---

## Testing

### Coverage Requirements

| Subsystem | Minimum Coverage | Type |
|-----------|-----------------|------|
| Simulation | 90% branch | Unit + property |
| Backend | 80% line | Unit + integration |
| Frontend | 70% line | Component + story |
| Prompts | — | Schema validation |

### Test Structure

```
tests/
├── test_<module>/
│   ├── __init__.py
│   ├── test_<feature>.py
│   └── conftest.py
```

### What to Test

- All public functions and methods
- Edge cases (empty state, boundary values, error conditions)
- Deterministic reproducibility (same seed = same result)
- Escalation threshold behavior
- Prompt schema compliance

---

## File Organization

```
subsystem/
├── src/            # Source code
│   ├── __init__.py
│   ├── module_a.py
│   └── module_b.py
├── tests/          # Tests (mirrors src/ structure)
│   ├── test_module_a.py
│   └── test_module_b.py
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Linting

Before committing, run:

```bash
# Python
ruff check .
ruff format --check .
mypy .

# TypeScript / JavaScript
npm run lint
npm run typecheck
```

Or rely on pre-commit hooks (see [tools/](../../tools/README.md)).

---

## Related

- [Development Workflow](development-workflow.md)
- [Setup Guide](setup.md)
- [CONTRIBUTING — Testing Requirements](../../CONTRIBUTING.md#testing-requirements)
- [Tooling Config](../../tools/)
