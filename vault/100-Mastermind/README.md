---
type: moc
status: active
tags: [mastermind, context, rules, governance]
---

# Project Mastermind

Project governance layer — context, engineering rules, implementation skeleton spec, and audit report. These documents are the **canonical reference** for all team members and AI assistants.

## Contents

| File | Type | Status | Description |
|------|------|--------|-------------|
| `PROJECT_CONTEXT.md` | context | ✓ Active | Canonical project context: overview, philosophy, architecture, team structure, priorities |
| `NON_NEGOTIABLE_RULES.md` | rules | ✓ Active | 24 mandatory engineering rules for all developers and AI assistants |
| `IMPLEMENTATION_SKELETON_PROMPT.md` | prompt | ✓ Executed | Specification for the implementation skeleton (skeleton already created) |
| `PROJECT_IMPLEMENTATION_AUDIT.md` | audit | Pre-skeleton | Repository state assessment before skeleton creation |

## Conventions

- These files are the **single source of truth** for project context and rules
- All other vault notes and repo docs should cross-reference these, not duplicate
- Changes to context or rules require team notification (see [[NON_NEGOTIABLE_RULES]] §3)
- YAML frontmatter required on all files: `type`, `status`, `tags`, `canonical: true`

## Reading Order

1. **[[PROJECT_CONTEXT]]** — read first, establishes full context
2. **[[NON_NEGOTIABLE_RULES]]** — read second, mandatory rules
3. **[[PROJECT_IMPLEMENTATION_AUDIT]]** — reference for current state
4. **[[IMPLEMENTATION_SKELETON_PROMPT]]** — reference for skeleton spec

## Related

- [[000-Index/README]] — vault Map of Content (start here)
- [[010-Architecture/README]] — architecture notes
- [[020-Decisions/README]] — decision log (ADRs)
- [[070-Prompts/README]] — prompt library
- [Architecture Overview](../../docs/references/architecture-overview.md) — canonical architecture reference
- [SOCIETAS Master Context](../../docs/SOCIETAS_Master_Context.md) — detailed philosophy and AI responsibility matrix
- [Vault README](../README.md) — vault structure and conventions
