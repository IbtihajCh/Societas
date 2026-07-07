# Feature Specification: [Title]

**Status:** Draft | Approved | Implemented | Obsolete

**Owner:** [Role]

**Date:** YYYY-MM-DD

**Related ADR:** [ADR-NNN](../adr/ADR-NNN-title.md)

---

## Summary

One-paragraph description of the feature. What does it do? Why does SOCIETAS need it?

---

## Motivation

Why is this feature necessary? What problem does it solve? Reference the [roadmap](../../ROADMAP.md) priority if applicable.

---

## Acceptance Criteria

```gherkin
Scenario: [Title]
  Given [precondition]
  When [action]
  Then [expected outcome]
```

- [ ] Criterion 1 (must be testable)
- [ ] Criterion 2
- [ ] Criterion 3

---

## Design

### Data Flow

```
[Input] → [Component A] → [Component B] → [Output]
```

### Interfaces

**Input:**
```json
{
    "field": "description"
}
```

**Output:**
```json
{
    "result": "description"
}
```

### State Changes

Describe any new state variables, database tables, or configuration parameters.

---

## Dependencies

- [ADR-NNN](../adr/ADR-NNN-title.md) — This feature depends on this decision
- `subsystem/` — This feature requires changes in this subsystem
- Feature X — This feature requires Feature X to be completed first

---

## Determinism & Explainability

- [ ] This feature is deterministic (simulation engine)
- [ ] This feature includes an explainability trace
- [ ] This feature uses LLM (document which prompt)

---

## Testing Plan

- Unit tests for core logic
- Integration tests for subsystem boundaries
- Determinism tests (for simulation features)
- Prompt validation tests (for AI features)

---

## Open Questions

- Question 1
- Question 2

---

## Related

- [Feature Vault](../../vault/060-Features/)
- [Sprint Plan](../../vault/030-Sprints/)
