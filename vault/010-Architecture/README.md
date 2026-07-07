# Architecture Notes

This folder contains detailed architecture documentation, diagrams, and design discussions that inform the ADRs in `docs/adr/`.

## Contents

| Note | Status | Description |
|------|--------|-------------|
| `system-overview.md` | ✓ Approved | Three-layer architecture (Deterministic → Cognitive → Presentation) |
| `deterministic-engine.md` | ✓ Approved | RuleEngine, WorldModel, Scheduler design |
| `dual-process-model.md` | ✓ Approved | System 1 (fast) / System 2 (LLM) interaction |
| `decision-pipeline.md` | ✓ Approved | RuleEngine → UtilityScorer → AmbiguityCheck → Escalation |
| `api-design.md` | Draft | REST + WebSocket API contracts |
| `data-model.md` | Draft | Entity schemas, state, persistence |
| `vllm-integration.md` | Draft | vLLM FastAPI router, model config |

## Related

- `docs/adr/` — [Formal decisions](../adr/README.md) derived from these notes
- `docs/references/architecture-overview.md` — [Canonical architecture reference](../docs/references/architecture-overview.md)
- `vault/020-Decisions/` — [Decision log](../020-Decisions/README.md)
