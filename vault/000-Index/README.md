# Map of Content — SOCIETAS Vault

Use this as your starting point for navigating the vault.

## Start Here

Every team member and AI assistant must read these before starting any task:

- [[PROJECT_CONTEXT]] — canonical project context, architecture, team structure, priorities
- [[NON_NEGOTIABLE_RULES]] — mandatory engineering rules (overrides all preferences)

## Quick Links

- [Architecture Overview](../010-Architecture/README.md) — Three-layer design
- [ADRs (Decision Log)](../020-Decisions/README.md) — Every architecture decision
- [Current Sprint](../030-Sprints/README.md) — Active sprint board
- [Feature Specs](../060-Features/README.md) — Specifications by priority
- [Prompt Library](../070-Prompts/README.md) — All system prompts
- [Project Mastermind](../100-Mastermind/README.md) — Context, rules, skeleton spec, audit

## Role Quick‑Start

| Role | First Note |
|------|-----------|
| Technical Lead (Tech Lead) | [[PROJECT_CONTEXT]] §8 + `010-Architecture/system-overview.md` |
| Simulation Engineer (Sim) | [[PROJECT_CONTEXT]] §8 + `010-Architecture/deterministic-engine.md` |
| AI Systems Engineer (AI) | [[PROJECT_CONTEXT]] §8 + `070-Prompts/` → pick a domain |
| Backend Engineer (Backend) | [[PROJECT_CONTEXT]] §8 + `010-Architecture/api-design.md` |
| Frontend Engineer (Frontend) | [[PROJECT_CONTEXT]] §8 + `060-Features/dashboard-spec.md` |
| DevOps Engineer (DevOps) | [[PROJECT_CONTEXT]] §8 + `080-Infrastructure/deployment.md` |

## Priority Features (Must Ship)

- [[Simulation Engine]] — deterministic core, RuleEngine, WorldModel
- [[Interactive Dashboard]] — real-time visualization
- [[Policy System]] — agent-based rule creation
- [[News Feed]] — narrative generation pipeline

## Tags

`#context` `#rules` `#architecture` `#decision` `#sprint` `#feature` `#prompt` `#research` `#infrastructure`
