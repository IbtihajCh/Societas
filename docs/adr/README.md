# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for SOCIETAS.

## What is an ADR?

An Architecture Decision Record documents a significant architectural decision, including the context, the decision itself, and its consequences. ADRs provide a historical record of why the project is structured the way it is.

## ADR Workflow

```
Proposal → Review → Accepted → (optional) Superseded/Deprecated
```

1. **Proposal** — Create a new ADR from `template.md`. Number sequentially.
2. **Review** — Share with the team for feedback. At least one subsystem owner must approve.
3. **Accepted** — Update status to `Accepted`. The decision is now canonical.
4. **Superseded** — If a later ADR replaces this one, update status to `Superseded by ADR-NNN`.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted |
| [ADR-002](ADR-002-deterministic-simulation-design.md) | Deterministic Simulation Design | Proposed |
| [ADR-003](ADR-003-hybrid-decision-fusion.md) | Hybrid Decision Fusion | Proposed |
| [ADR-004](ADR-004-escalation-threshold.md) | LLM Escalation Threshold | Proposed |

## Template

Use [template.md](template.md) for new ADRs.

## Related

- [Development Workflow](../guides/development-workflow.md)
- [Architecture Overview](../references/architecture-overview.md)
- [Vault — Decisions](../../vault/020-Decisions/)
