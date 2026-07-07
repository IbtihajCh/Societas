# Decision Log

This folder mirrors `docs/adr/` for Obsidian browsing. Each ADR is a note here with [[wikilinks]] and frontmatter for Dataview queries.

## Active ADRs

| ADR | Title | Status |
|-----|-------|--------|
| `ADR-001` | Record Architecture Decisions | ✓ Accepted |
| `ADR-002` | Deterministic Simulation Design | ✓ Accepted |
| `ADR-003` | Hybrid Decision Fusion (Gemma + Rules) | ✓ Accepted |
| `ADR-004` | LLM Escalation Threshold Configuration | ✓ Accepted |

## Conventions

- ADR frontmatter: `type: adr`, `status: proposed/accepted/deprecated/superseded`
- Linking: `[ADR-002](ADR-002-deterministic-simulation-design.md)` in vault, `[ADR-002](../docs/adr/ADR-002-deterministic-simulation-design.md)` in repo docs
- Status changes: superseding ADR links to superseded one

## Related

- `docs/adr/` — [Canonical ADR source](../docs/adr/README.md)
- `docs/adr/template.md` — [ADR template](../docs/adr/template.md)
