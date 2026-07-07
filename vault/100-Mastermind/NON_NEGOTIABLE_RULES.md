---
type: rules
status: active
version: 1.1
priority: highest
tags: [rules, governance, mandatory, engineering]
canonical: true
---

# NON_NEGOTIABLE_RULES

> **SOCIETAS Engineering Rules**
>
> **Version:** 1.1 | **Priority:** Highest
>
> This document defines the mandatory engineering rules for every developer, AI coding assistant, and automation tool working on SOCIETAS.
>
> These rules override convenience, assumptions, and personal preferences. If any action conflicts with this document, **follow this document.**
>
> **Read alongside:** [[PROJECT_CONTEXT]] — canonical project context.

---

# 1. Single Source of Truth

The following documents are the authoritative sources for the project:

| Document | Location |
|----------|----------|
| Project Context | [[PROJECT_CONTEXT]] (`vault/100-Mastermind/PROJECT_CONTEXT.md`) |
| Architecture | [architecture-overview](../../docs/references/architecture-overview.md) + [[010-Architecture/README]] |
| API Contracts | [openapi.yaml](../../contracts/api/openapi.yaml) + [contracts/schemas/](../../contracts/schemas/) |
| Team & Roles | [[000-Index/README]] (Role Quick-Start) + [[PROJECT_CONTEXT]] §8 |
| Tasks & Sprints | [[030-Sprints/README]] (Sprint Board) |
| ADRs | [docs/adr/](../../docs/adr/) + [[020-Decisions/README]] |
| Prompts | [prompts/](../../prompts/) + [[070-Prompts/README]] |

Never create conflicting documentation. If documentation becomes outdated, update it instead of creating duplicates.

---

# 2. Stay Inside Your Boundary

Every engineer owns one subsystem.

Never modify another subsystem unless:

- explicitly assigned
- fixing a confirmed bug
- performing approved integration
- requested during code review

Example:

Simulation Engineer

✅ simulation/

❌ frontend/

❌ backend/

---

Backend Engineer

✅ backend/

❌ simulation/

❌ frontend/

---

Frontend Engineer

✅ frontend/

❌ backend/

❌ simulation/

---

# 3. Never Break Existing Interfaces

Before changing

- API responses
- function signatures
- schemas
- shared models

Verify that other systems will continue working.

If a breaking change is required:

1. Document it.
2. Notify the team.
3. Update [openapi.yaml](../../contracts/api/openapi.yaml).
4. Update all dependent systems.

---

# 4. Mock Before Blocking

Never wait for another developer.

If another subsystem is incomplete:

Create

- mock APIs
- mock JSON
- mock services
- mock data

Continue development.

Replace mocks only during integration.

---

# 5. Never Invent APIs

Every API must exist inside [contracts/api/openapi.yaml](../../contracts/api/openapi.yaml).

If it is missing, add it there first. Then implement it. Never invent endpoints while coding.

---

# 6. Documentation Is Part of Development

Code is not complete until documentation is updated.

| Change | Update |
|--------|--------|
| Architecture | [architecture-overview](../../docs/references/architecture-overview.md) + [[010-Architecture/README]] |
| API | [openapi.yaml](../../contracts/api/openapi.yaml) + [contracts/](../../contracts/) |
| Feature | [[060-Features/README]] (feature spec) |
| Prompt | [[070-Prompts/README]] + `prompts/` |
| Task | [[030-Sprints/README]] (sprint board) |
| Decision | [docs/adr/](../../docs/adr/) + [[020-Decisions/README]] |

---

# 7. Small Pull Requests

Large PRs create conflicts.

Preferred size

100–400 lines

Maximum

~800 lines

One feature

↓

One PR

---

# 8. Never Commit Directly To Main

Allowed branch prefixes: `sim/`, `ai/`, `be/`, `fe/`, `infra/`, `docs/`, `fix/`

Never push directly to `main`.

> **See:** [branching-strategy](../../docs/guides/branching-strategy.md) — canonical branch naming and merge process.

---

# 9. Every Feature Must Follow This Lifecycle

```
Idea → Specification → Implementation → Testing → Documentation → Pull Request → Review → Merge
```

Do not skip steps.

> **See:** [development-workflow](../../docs/guides/development-workflow.md) — detailed 9-step pipeline.

---

# 10. Keep Code Modular

Prefer

Small modules

Reusable components

Loose coupling

High cohesion

Avoid

Large files

Deep nesting

Global state

Circular imports

---

# 11. AI Is An Assistant, Not An Architect

AI may

- write code
- explain code
- generate documentation
- generate tests
- suggest improvements

AI may NOT

- redesign architecture
- rename major systems
- change APIs
- remove folders
- change ownership

without approval.

---

# 12. AI Must Read Context First

Before generating code, AI MUST read:

1. [[PROJECT_CONTEXT]] — project context
2. [architecture-overview](../../docs/references/architecture-overview.md) — architecture
3. [openapi.yaml](../../contracts/api/openapi.yaml) — API contracts
4. [[000-Index/README]] — role guide
5. [[030-Sprints/README]] — current task

Never generate code without context.

---

# 13. Never Guess

If information is missing

DO NOT

Invent

Assume

Estimate

Guess

Instead

Leave TODO

Ask

Document uncertainty

---

# 14. Explain Complex Decisions

Whenever implementing

Algorithms

Simulation

AI logic

Policies

Psychology

Write comments explaining

Why

not only

What

---

# 15. Code Style

- Readable, consistent, typed, modular, documented
- Avoid: magic numbers, unused code, dead files, duplicated logic

> **See:** [coding-standards](../../docs/guides/coding-standards.md) — Python (ruff/mypy/pytest) and TypeScript (strict) with coverage requirements.

---

# 16. Testing Is Mandatory

Every completed feature should include

- Unit tests where practical
- Manual verification
- Edge case consideration

Never merge untested code intentionally.

---

# 17. Preserve Project Vision

Do not simplify architecture because it is easier.

Do not add unnecessary complexity because it is interesting.

Every decision must support

SOCIETAS

as

A Hybrid AI Governance Simulation Platform.

---

# 18. Performance First

The simulation should remain deterministic and efficient.

Avoid unnecessary

- LLM calls
- database queries
- API requests
- expensive computations

Cache where appropriate.

Batch where appropriate.

---

# 19. Keep AI Usage Efficient

LLMs should only be used for

- Policy translation
- Tie-breaking
- Persona generation
- Narration
- News generation
- Explanations

Never use an LLM when deterministic logic can solve the task.

---

# 20. Daily Workflow

Every developer should:

1. Pull latest changes.
2. Read assigned tasks.
3. Read updated documentation.
4. Load AI context.
5. Implement assigned work.
6. Test changes.
7. Update documentation.
8. Commit frequently.
9. Open Pull Request.
10. Resolve review comments.

---

# 21. Communication Rules

Before asking a question, check:

- [[PROJECT_CONTEXT]] — project context
- [architecture-overview](../../docs/references/architecture-overview.md) — architecture
- [openapi.yaml](../../contracts/api/openapi.yaml) — API contracts
- [[000-Index/README]] — your role guide

If the answer is not documented, ask immediately. Do not waste time guessing.

---

# 22. Definition of Done

A task is considered complete only if:

✅ Feature works.

✅ Code builds.

✅ Tests pass.

✅ Documentation updated.

✅ No linting errors.

✅ Pull Request opened.

✅ Review completed.

Only then is the task finished.

---

# 23. Hackathon Mindset

Remember the objective.

The goal is NOT

Perfect code.

The goal is NOT

Hundreds of features.

The goal IS

A stable, convincing, polished demonstration of the SOCIETAS vision.

When making trade-offs:

Working Demo

>

Architecture

>

Performance

>

Extra Features

---

# 24. Final Principle

Every contributor—human or AI—should leave the repository in a better state than they found it.

If you improve something:

- document it
- explain it
- keep it modular
- avoid breaking existing work

Build for the team, not just your task.

---

**"Move fast, but never create problems for the next developer."**

---

## See Also

- [[PROJECT_CONTEXT]] — canonical project context (read alongside this document)
- [[PROJECT_IMPLEMENTATION_AUDIT]] — repository state assessment (pre-skeleton)
- [[IMPLEMENTATION_SKELETON_PROMPT]] — implementation skeleton specification (executed)
- [Architecture Overview](../../docs/references/architecture-overview.md) — canonical architecture reference
- [Development Workflow](../../docs/guides/development-workflow.md) — detailed 9-step pipeline
- [Branching Strategy](../../docs/guides/branching-strategy.md) — branch naming and merge process
- [Coding Standards](../../docs/guides/coding-standards.md) — language-specific standards and coverage
- [AI Agent Rules](../../docs/guides/ai-agent-rules.md) — AI agent prompt governance
- [Vault README](../README.md) — vault structure and conventions