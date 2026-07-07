# ADR-001: Record Architecture Decisions

**Status:** Accepted

**Date:** 2026-07-07

**Owner:** Technical Lead

**Supersedes:** None

---

## Context

The SOCIETAS project needs a consistent, auditable method for recording architectural decisions. Without a formal system, decisions are lost in conversation history, PR comments, or chat logs. New team members (especially AI agents) cannot reconstruct why the architecture is the way it is.

## Decision

We will use Architecture Decision Records (ADRs) as defined by Michael Nygard. Each ADR is a short document capturing:

1. **Context** — The forces at play (technical, business, or otherwise)
2. **Decision** — The chosen approach
3. **Consequences** — What becomes easier and harder as a result

### ADR Format

- Numbered sequentially (ADR-001, ADR-002, ...)
- Written in Markdown
- Stored in `docs/adr/`
- Template at `docs/adr/template.md`

### ADR Lifecycle

- **Proposed** — Initial draft, under review
- **Accepted** — Approved and active
- **Superseded by ADR-NNN** — Replaced by a newer decision
- **Deprecated** — No longer applicable, not replaced

### When to Write an ADR

Write an ADR when a decision:

- Affects the system architecture or subsystem boundaries
- Changes how the team works (tooling, workflows, standards)
- Introduces a new dependency or technology
- Has significant long-term consequences
- Could be revisited later and needs context

### When NOT to Write an ADR

- Routine implementation details within a subsystem
- Bug fixes (documented in the PR)
- Configuration changes (documented in the config file)

## Consequences

**Positive:**
- New team members and AI agents can rapidly understand architectural rationale
- Decisions are reviewable and revertible with clear history
- Prevents repeated debate on the same topics
- Creates a culture of intentional design

**Neutral:**
- Requires discipline to maintain ADRs alongside code changes
- ADRs must be reviewed as part of the PR process

**Negative:**
- Initial overhead to establish the habit
- Risk of ADRs becoming stale if not updated when decisions change

## Related

- [ADR Template](template.md)
- [ADR Index](README.md)
- [CONTRIBUTING](../../CONTRIBUTING.md)
