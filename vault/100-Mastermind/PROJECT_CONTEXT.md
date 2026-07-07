---
type: context
status: active
version: 1.1
tags: [context, architecture, team, governance]
canonical: true
---

# SOCIETAS — PROJECT CONTEXT

Version: 1.1
Status: Hackathon Build
Team Size: 6
Development Style: AI-First Development
Primary Coding Tool: OpenCode
Knowledge Base: Obsidian
Version Control: GitHub

> **This document is the canonical project context.**
> All team members and AI assistants must read this before starting any task.
> See also: [[NON_NEGOTIABLE_RULES]] — mandatory engineering rules.

---

# 1. PROJECT OVERVIEW

SOCIETAS is a real-time AI-assisted governance and society simulation platform.

The project aims to simulate a living society where thousands of autonomous agents interact with one another under government policies. Instead of relying entirely on Large Language Models, SOCIETAS follows a Hybrid AI Architecture where deterministic mathematical simulation is responsible for most decisions while an LLM assists only when additional reasoning is necessary.

The goal is to demonstrate that explainable hybrid intelligence is more efficient, scalable, and controllable than purely LLM-driven simulations.

This project is being built for a hackathon within approximately five days.

Therefore, architecture, modularity, maintainability, and demonstration quality are prioritized over feature completeness.

---

# 2. CORE PHILOSOPHY

The project follows these principles.

1. Deterministic first.

Every decision that can be solved mathematically should remain deterministic.

2. AI only when required.

The LLM should only participate when uncertainty exceeds predefined thresholds or when natural language reasoning is required.

3. Modular Architecture.

Every system should be replaceable without affecting unrelated modules.

4. Parallel Development.

All six developers should be capable of working simultaneously without blocking one another.

5. AI Assisted Development.

Every team member will use OpenCode or another AI coding tool.

The repository, documentation and prompts must therefore be structured for AI readability.

> **See also:** [SOCIETAS Master Context](../../docs/SOCIETAS_Master_Context.md) — detailed architecture philosophy, dual-process cognitive model, and AI responsibility matrix.

---

# 3. HIGH LEVEL SYSTEM

                    USER

                      │

              Policy Input

                      │

               Policy Translator
                     (AI)

                      │

               Structured Policy

                      │

             Simulation Engine

                      │

       ┌──────────────┼──────────────┐

 Economy        Psychology      Society

                      │

              Agent Decisions

                      │

      Rule Engine → AI Tie Break

                      │

             Updated World State

                      │

      Dashboard + News + Metrics

---

# 4. HYBRID AI ARCHITECTURE

Most agent behaviour should NEVER call an LLM.

Instead:

Needs

↓

Scores

↓

Rule Engine

↓

Action

Only if:

- multiple actions receive nearly identical scores
- uncertainty exceeds threshold
- narration is required
- explanation is requested

should an AI model be called.

The AI never replaces the simulation.

It augments it.

---

# 5. MAJOR SYSTEMS

Simulation Engine

AI Layer

Backend

Frontend

Documentation

Infrastructure

These systems must remain loosely coupled.

---

# 6. CORE FEATURES (Hackathon MVP)

The following MUST exist.

Simulation

• Agents

• Needs

• Employment

• Economy

• Crime

• Policies

• Psychology

• Tick Engine

AI

• Policy Translation

• Tie Breaking

• Persona Generation

• AI News Feed

• Spotlight Narration

Backend

• FastAPI

• REST APIs

• WebSockets

Frontend

• Dashboard

• Statistics

• Charts

• Timeline

• Policy Controls

Infrastructure

• Docker

• GitHub Actions

• Documentation

---

# 7. FUTURE FEATURES

The architecture must support these systems.

Families

Communities

Religion

Organizations

Advanced Lifecycle

Healthcare

Education

International Relations

Housing

Transportation

The implementation of these systems is optional during the hackathon.

However architecture should anticipate them.

---

# 8. TEAM STRUCTURE

Member 1

Technical Lead

Owns

Architecture

Documentation

GitHub

Obsidian

Integration

Reviews

Presentation

---

Member 2

Simulation Engineer

Owns

simulation/

Responsible for

Agents

World

Economy

Needs

Psychology

Crime

Policies

Lifecycle Architecture

---

Member 3

AI Systems Engineer

Owns

models/

backend/app/ai/

Responsible for

Gemma

vLLM

Prompts

Tie Breaking

Narration

Policy Translation

News Feed

Evaluation

---

Member 4

Backend Engineer

Owns

backend/

Responsible for

FastAPI

REST APIs

Database

WebSockets

Integration

Authentication

Logging

---

Member 5

Frontend Engineer

Owns

frontend/

Responsible for

Dashboard

Charts

Policy UI

Statistics

Timeline

News Feed

Responsive Design

---

Member 6

DevOps Engineer

Owns

Docker

CI/CD

Testing

README

Presentation

Deployment

Documentation

Architecture Diagrams

---

# 9. PARALLEL DEVELOPMENT STRATEGY

No developer should wait for another.

Every subsystem must expose interfaces.

Example.

Frontend uses mock APIs.

Backend uses mock simulation.

Simulation ignores frontend.

AI works using predefined JSON schemas.

Everything is integrated later.

---

# 10. MOCK API STRATEGY

Mock APIs exist solely to allow parallel development.

Example

GET /simulation/state

Response

{
  "population":1000,
  "employment":82,
  "crime":6,
  "economy":73,
  "tick":154
}

Initially Backend returns this manually.

Later

Backend simply calls

simulation.get_state()

No frontend changes required.

---

# 11. REPOSITORY STRUCTURE

```
SOCIETAS/
├── backend/          # FastAPI REST + WebSocket server
├── frontend/         # Next.js dashboard and UI
├── simulation/       # Deterministic simulation engine
├── models/           # AI layer (router, prompts, tie-break, narration)
├── shared/           # Cross-module schemas, DTOs, interfaces, types
├── contracts/        # OpenAPI spec, JSON schemas, examples
├── tests/            # Unit, integration, performance tests
├── tools/            # Mock APIs and development tools
├── docs/             # Architecture references, ADRs, guides
├── vault/            # Obsidian knowledge base (this folder)
├── prompts/          # Canonical AI prompt files
├── .github/          # CI/CD workflows, issue templates, CODEOWNERS
├── docker/           # Dockerfiles and docker-compose
├── scripts/          # Setup, lint, test, clean scripts
└── README.md
```

> **See also:** [Architecture Overview](../../docs/references/architecture-overview.md) — canonical architecture reference with data flow and decision pipeline.

---

# 12. OBSIDIAN STRUCTURE

The vault serves as the project's knowledge base. Every major decision must be documented.

| Folder | Purpose | Owner |
|--------|---------|-------|
| `000-Index/` | Map of Content (MOC) — entry point for navigation | All |
| `010-Architecture/` | System architecture notes, diagrams, models | Technical Lead |
| `020-Decisions/` | ADR mirror — linked from `docs/adr/` | Technical Lead |
| `030-Sprints/` | Sprint planning, retrospectives, velocity tracking | All |
| `040-Meetings/` | Meeting notes organized by date | All |
| `050-Research/` | External research, papers, benchmarks | AI Systems Engineer |
| `060-Features/` | Feature specifications (one note per feature) | All |
| `070-Prompts/` | Prompt library — maps to `prompts/` source of truth | AI Systems Engineer |
| `080-Infrastructure/` | Infrastructure notes, deployment records | DevOps Engineer |
| `090-Reference/` | External references, templates, attachments | All |
| `100-Mastermind/` | Project context, engineering rules, skeleton spec, audit | All |

**Conventions:**
- Naming: `YYYY-MM-DD-title.md` for dated notes, `kebab-case-title.md` for evergreen notes
- Links: Use `[[wikilinks]]` within vault, `[label](path)` for repo cross-references
- Properties: Every note has YAML frontmatter with `type`, `status`, `tags`
- Folder prefixes (`000-`, `010-`, etc.) enforce consistent ordering in the graph view

> **See also:** [Vault README](../README.md) — vault structure and conventions.

---

# 13. DEVELOPMENT WORKFLOW

Every feature follows:

```
Research → Specification → Implementation → Testing → Documentation → Review → Merge
```

> **See also:** [[NON_NEGOTIABLE_RULES]] §9 — mandatory feature lifecycle.
> **Detailed guide:** [development-workflow](../../docs/guides/development-workflow.md)

---

# 14. GIT WORKFLOW

Never commit directly to `main`. Every feature gets its own branch using subsystem prefixes:

| Prefix | Subsystem | Example |
|--------|-----------|---------|
| `sim/` | Simulation | `sim/needs-scoring` |
| `ai/` | AI / Gemma | `ai/persona-generation` |
| `be/` | Backend API | `be/simulation-control-api` |
| `fe/` | Frontend | `fe/real-time-dashboard` |
| `infra/` | Infrastructure | `infra/ci-workflow` |
| `docs/` | Documentation | `docs/api-reference` |
| `fix/` | Bug fixes | `fix/tick-overflow` |

Every completed task becomes a Pull Request. At least one review before merge.

> **See also:** [[NON_NEGOTIABLE_RULES]] §8 — never commit to main.
> **Detailed guide:** [branching-strategy](../../docs/guides/branching-strategy.md) — canonical branch naming and merge process.

---

# 15. DOCUMENTATION RULES

Whenever code changes, update documentation:

| Change | Update |
|--------|--------|
| Architecture | [architecture-overview](../../docs/references/architecture-overview.md) + [[010-Architecture/README\|Architecture Notes]] |
| APIs | [openapi.yaml](../../contracts/api/openapi.yaml) + [contracts/](../../contracts/) |
| Prompts | [[070-Prompts/README\|Prompt Library]] + `prompts/` |
| Features | [[060-Features/README\|Feature Specs]] |
| Tasks | [[030-Sprints/README\|Sprint Board]] |
| Decisions | [ADR](../../docs/adr/) + [[020-Decisions/README\|Decision Log]] |

Documentation is part of the project.

> **See also:** [[NON_NEGOTIABLE_RULES]] §6 — documentation is part of development.

---

# 16. AI DEVELOPMENT RULES

AI should never modify unrelated folders.

Every AI assistant must load context before generating code:

1. [[PROJECT_CONTEXT]] — this document
2. [Architecture Overview](../../docs/references/architecture-overview.md)
3. [OpenAPI Contracts](../../contracts/api/openapi.yaml)
4. [Role Guide](../000-Index/README.md) — role quick-start
5. Current Task — from [[030-Sprints/README|Sprint Board]]

AI must explain major architectural changes before implementing them.
AI must produce maintainable code.
AI must avoid unnecessary dependencies.
AI must document complex logic.

> **See also:** [[NON_NEGOTIABLE_RULES]] §11-13 — AI assistant rules, context loading, and never-guess policy.
> **Detailed guide:** [ai-agent-rules](../../docs/guides/ai-agent-rules.md) — AI agent prompt governance.

---

# 17. CODING PRINCIPLES

- Readable code over clever code
- Prefer composition over inheritance
- Small reusable modules
- Strict typing
- Consistent naming
- Write documentation while implementing
- Avoid premature optimization

> **See also:** [[NON_NEGOTIABLE_RULES]] §15 — code style rules.
> **Detailed guide:** [coding-standards](../../docs/guides/coding-standards.md) — Python (ruff/mypy/pytest) and TypeScript (strict) standards with coverage requirements.

---

# 18. HACKATHON PRIORITIES

| Priority | Goal |
|----------|------|
| 1 | Working Demo |
| 2 | Stable Architecture |
| 3 | Clean UI |
| 4 | AI Features |
| 5 | Documentation |

Perfect code is NOT required. A convincing demonstration IS required.

> **See also:** [[NON_NEGOTIABLE_RULES]] §23 — hackathon mindset and trade-off guidance.

---

# 19. EXPECTED DELIVERABLES

Working software

GitHub repository

Obsidian knowledge base

README

Presentation

Architecture diagrams

API documentation

Demo

---

# 20. DOCUMENT INDEX

This section maps the originally planned standalone documents to their actual locations in the repository and vault.

| Planned Document | Actual Location | Status |
|-------------------|-----------------|--------|
| `ARCHITECTURE.md` | [docs/references/architecture-overview.md](../../docs/references/architecture-overview.md) + [[010-Architecture/README]] | ✓ Exists |
| `API_CONTRACTS.md` | [contracts/api/openapi.yaml](../../contracts/api/openapi.yaml) + [contracts/schemas/](../../contracts/schemas/) | ✓ Exists |
| `TEAM.md` | [[000-Index/README]] (Role Quick-Start) + §8 above | ✓ Exists |
| `TASKS.md` | [[030-Sprints/README]] (Sprint Board) | ✓ Exists |
| Feature Specifications | [[060-Features/README]] | ✓ Exists |
| Role Guides | [[000-Index/README]] (Role Quick-Start table) | ✓ Exists |
| Obsidian Templates | [docs/templates/](../../docs/templates/) | ✓ Exists |
| GitHub Issue Templates | [.github/ISSUE_TEMPLATE/](../../.github/ISSUE_TEMPLATE/) | ✓ Exists |
| Pull Request Template | [.github/PULL_REQUEST_TEMPLATE.md](../../.github/PULL_REQUEST_TEMPLATE.md) | ✓ Exists |
| Coding Standards | [docs/guides/coding-standards.md](../../docs/guides/coding-standards.md) | ✓ Exists |
| Documentation Standards | [docs/guides/development-workflow.md](../../docs/guides/development-workflow.md) | ✓ Exists |
| AI Prompt Templates | [prompts/](../../prompts/) + [[070-Prompts/README]] | ✓ Exists |
| Sprint Plan | [[030-Sprints/README]] (Sprint-001) | ✓ Exists |

All documents are AI-readable, modular, and version-controlled.

---

## See Also

- [[NON_NEGOTIABLE_RULES]] — mandatory engineering rules (read alongside this document)
- [[PROJECT_IMPLEMENTATION_AUDIT]] — repository state assessment (pre-skeleton)
- [[IMPLEMENTATION_SKELETON_PROMPT]] — implementation skeleton specification (executed)
- [Architecture Overview](../../docs/references/architecture-overview.md) — canonical architecture reference
- [SOCIETAS Master Context](../../docs/SOCIETAS_Master_Context.md) — detailed philosophy and AI responsibility matrix
- [Project Roadmap](../../ROADMAP.md) — phased development plan
- [Vault README](../README.md) — vault structure and conventions