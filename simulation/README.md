# Simulation — Deterministic Engine

**Owner:** Simulation Engineer

The core of SOCIETAS. This is a fully deterministic, explainable agent-based modeling engine. No LLM involvement. Every computation is reproducible and mathematically grounded.

## Responsibilities

- World simulation and environment state
- Agent state management (needs, psychology, emotions, morality)
- Economy system (resources, employment, wealth distribution)
- Decision scoring pipeline (action utility calculation)
- Ambiguity detection and escalation threshold
- Policy application and effect propagation
- Crime and enforcement subsystem
- Tick update and scheduling
- Data export for analysis and replay

## Design Principles

1. **Deterministic** — same seed + same input = same output, always
2. **Explainable** — every decision can be traced to its inputs
3. **Performant** — capable of simulating 10,000+ agents in real-time
4. **Modular** — subsystems are independently replaceable and testable
5. **No LLM** — Gemma never enters this directory

## Conventions

- Engine entry point: `engine/`
- Agents in `agents/`
- Economy in `economy/`
- Psychology in `psychology/`
- Policies in `policies/`
- Tests mirror source structure (`tests/test_engine/`, etc.)
- >90% branch coverage required

## Related

- [ADR-002: Deterministic Simulation Design](../docs/adr/ADR-002-deterministic-simulation-design.md)
- [Coding Standards](../docs/guides/coding-standards.md)
- [Master Context §4-6](../docs/SOCIETAS_Master_Context.md)
