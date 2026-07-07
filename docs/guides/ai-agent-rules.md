# AI Agent Rules

This document governs how AI coding agents operate within the SOCIETAS repository. All agents must follow these rules. Human contributors should enforce them during review.

---

## Core Principles

1. **Read before writing** — Always load the relevant context (Master Context, ADRs, READMEs, coding standards) before making any change
2. **Own your scope** — Work within your assigned subsystem unless explicitly authorized otherwise
3. **Document reasoning** — Every architectural decision must be recorded in an ADR or a vault note
4. **Never skip the workflow** — The development pipeline (research → spec → ... → merge) is mandatory
5. **Ask for help** — If uncertain about an architectural decision, escalate to the Technical Lead

---

## Allowed Operations

AI agents may autonomously:

- Read any file in the repository
- Create and modify files within their assigned subsystem
- Run linting and testing commands
- Create branches and push changes
- Open PRs (but never merge without human approval)
- Create ADRs for decisions within their subsystem
- Update vault notes for their work

AI agents may NOT autonomously:

- Modify files outside their assigned subsystem
- Skip any step in the development workflow
- Merge a PR (even their own)
- Modify CI/CD configuration
- Change CODEOWNERS or root configuration
- Delete or rename files owned by another team member
- Commit secrets, API keys, or credentials to the repository

---

## Context Loading Protocol

Before starting any task, an AI agent must load:

1. `Master Context` — Overall architecture and philosophy
2. `CONTRIBUTING.md` — Contribution rules
3. `Docs/adr/README.md` — Active ADR index
4. Subsystem `README.md` — Their assigned area
5. `Docs/guides/coding-standards.md` — Code conventions

For tasks involving LLM integration, also load:

6. `Prompts/README.md` — Prompt organization
7. Relevant prompt files from `prompts/`

---

## Decision Escalation

Escalate to the Technical Lead when:

- A decision affects multiple subsystems
- An ADR needs to be superseded
- The development workflow needs an exception
- Priority conflicts arise between features
- Performance requirements conflict with design principles

---

## Prompt Engineering Rules

1. Every prompt must have documented input and output schemas
2. Never interpolate raw user input directly into prompts
3. Always validate LLM output against the schema before use
4. Prompt changes require the same review process as code changes
5. Test prompts with edge cases (empty input, adversarial input, etc.)

---

## Commit Message Format

```
type(scope): description

Refs: #issue, ADR-NNN
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`
Scopes: `sim`, `ai`, `be`, `fe`, `infra`, `docs`, `vault`

---

## Related

- [Development Workflow](development-workflow.md)
- [Branching Strategy](branching-strategy.md)
- [Coding Standards](coding-standards.md)
- [CONTRIBUTING](../../CONTRIBUTING.md)
