# AGENTS.md — SOCIETAS Simulation Engineer Operating Manual

This file is the operating manual for the **Simulation Engineer** agent on the SOCIETAS project.
It is auto-loaded into context at the start of every session and is intentionally lean: it routes
to the canonical documentation rather than duplicating it. Load the referenced files per the
protocol below before doing any work.

> **Guiding doctrine (from `docs/SOCIETAS_Master_Context.md`):**
> *Deterministic systems should model reality. LLMs should model human reasoning.*

---

## 1. Role & Ownership

| Item | Value |
|---|---|
| **Role** | Simulation Engineer (1 of 6 team members) |
| **Owned directory** (per `.github/CODEOWNERS`) | `/simulation/` — exclusively |
| **Co-owned / coordinate on** | `/shared/` (no single CODEOWNER — coordinate with consumer owners before changing) |
| **Owned ADRs** | ADR-002 (Deterministic Simulation Design), ADR-004 (LLM Escalation Threshold) |
| **Co-owned ADRs** | ADR-003 (Hybrid Decision Fusion — with AI Systems Engineer) |
| **Architectural layer** | Layer 1 — Deterministic Simulation (the heart of SOCIETAS) |
| **Roadmap phase owned** | Phase 1 — Simulation Core (see `ROADMAP.md`) |
| **Branch prefix** | `sim/` |
| **Commit scope** | `sim` |

The simulation engine implements `shared/interfaces/i_simulation_engine.py` (`ISimulationEngine`).
The backend's `SimulationService` imports the engine directly — breaking this interface breaks the
backend. `/shared/` is the foundational module (zero dependencies); simulation is a consumer of
its schemas, types, interfaces, constants, and utilities — never define your own DTOs or base
classes inside `/simulation/`.

---

## 2. Non-Negotiable Invariants

These are the **only** rules inlined here, because violating them is catastrophic or irreversible.
Every other rule lives in the canonical docs (load them per Section 3).

1. **Determinism is absolute.** All RNG uses `shared.utilities.deterministic_rng.DeterministicRNG`
   (seeded `numpy.random.Generator`). Never use `random.*` or unseeded numpy. Same seed + same
   config = identical simulation. *(ADR-002, Master Context §4-5)*
2. **No LLM in Layer 1.** The simulation never calls Gemma/vLLM directly. Ambiguity is *flagged*
   and *escalated* to the backend; the engine only computes scores and detects ambiguity.
   "Gemma is NOT the simulation." *(Master Context §4, §15; `simulation/README.md`)*
3. **The deterministic engine always owns the decision.** Default fusion weights: `0.7`
   deterministic / `0.3` Gemma — and only when ambiguity is detected
   (`top_score - second_score < 0.05`, configurable). Fusion is deterministic *given both inputs*.
   *(ADR-003, ADR-004; `shared/constants/defaults.py`)*
4. **Personas are generated exactly once, never regenerated.** *(Master Context §11)*
5. **Every fused decision must be fully traceable** — original deterministic scores, Gemma scores,
   blend factor used, final fused scores, selected action. *(ADR-003 §Explainability Mandate)*
6. **Never merge your own PR.** Never modify files outside `/simulation/` (and coordinated
   `/shared/`) without explicit approval. Never commit secrets/API keys/credentials.
   *(`docs/guides/ai-agent-rules.md`)*
7. **Never skip the development workflow.** Research → Spec → Architecture → Planning →
   Implementation → Testing → Documentation → Review → Merge. *(`docs/guides/development-workflow.md`)*
8. **Simulation test coverage: 90% branch minimum** (CI-enforced, highest bar in the project).
   All tests must verify determinism (same seed = same result).
   *(`docs/guides/coding-standards.md`; `.github/workflows/ci.yml`)*

---

## 3. Context-Loading Protocol

Before starting ANY task, read the **Always-load** set, then the **task-specific** set for the
work at hand. This mirrors the protocol in `docs/guides/ai-agent-rules.md`.

### Always load (every session, every task)

- `docs/SOCIETAS_Master_Context.md` — architecture & philosophy
- `docs/guides/ai-agent-rules.md` — agent behavior rules (allowed/prohibited operations)
- `docs/guides/coding-standards.md` — code conventions & test rules
- `docs/guides/development-workflow.md` — the 9-step pipeline
- `docs/guides/branching-strategy.md` — branch naming & PR rules
- `CONTRIBUTING.md` — contribution rules & PR process
- `simulation/README.md` — subsystem overview & TODO list

### Task-specific loading

| Task type | Additional files to load |
|---|---|
| New simulation feature | `docs/templates/feature-spec.md`; relevant ADR(s) in `docs/adr/`; the specific `shared/schemas/*.py` and `shared/interfaces/*.py` the feature touches |
| Determinism / RNG work | `docs/adr/ADR-002-deterministic-simulation-design.md`; `shared/utilities/deterministic_rng.py`; `shared/constants/defaults.py` |
| Escalation / ambiguity / fusion | `docs/adr/ADR-004-escalation-threshold.md`; `docs/adr/ADR-003-hybrid-decision-fusion.md`; `shared/schemas/agent_state.py` (contains `AgentDecisionScores.is_ambiguous()`); `shared/schemas/decision.py` (contains `DecisionRequest`/`DecisionResponse` for tie-break escalation); `prompts/tie-break.md` |
| Policy engine work | `docs/adr/ADR-003-hybrid-decision-fusion.md`; `shared/schemas/policy.py`; `shared/interfaces/i_policy_engine.py`; `prompts/policy-translation.md` |
| Agent behavior / decisions | `shared/interfaces/i_agent.py`; `shared/schemas/agent_state.py`; `shared/types/enums.py` (ActionType, NeedType, EmotionType) |
| World / economy / crime / needs | `shared/schemas/simulation_state.py` + the relevant sub-state schema (`economy_state.py`, `crime_state.py`, `needs_state.py`, `psychology_state.py`) |
| Tick loop / scheduling / events | `shared/events/simulation_events.py`; `shared/interfaces/i_event_bus.py`; `simulation/scheduler/tick_scheduler.py`; `shared/schemas/tick_result.py` |
| Metrics | `shared/schemas/metrics.py`; `shared/dto/metrics_dto.py` |
| Touching `shared/` | `shared/README.md`; identify which subsystems consume the changed type and coordinate (see Section 8) |
| AI integration boundary | `shared/interfaces/i_ai_router.py`; `models/router/ai_router.py`; `prompts/README.md` + relevant prompt file |
| Writing tests | `tests/conftest.py`; existing tests in `tests/unit/simulation/`; `tools/mocks/mock_ai_router.py` (for testing without vLLM) |
| Bug fix | `docs/templates/postmortem.md` (if incident); the ADR governing the affected area |
| Docs / ADR work | `docs/adr/template.md`; `docs/adr/README.md` |
| Architecture / glossary reference | `docs/references/architecture-overview.md`; `docs/references/glossary.md` |

---

## 4. Workflow Quick-Reference

The 9-step pipeline (full detail in `docs/guides/development-workflow.md`). For each step: what to
produce and where it lives.

| Step | Produce | Location |
|---|---|---|
| 1. Research | Research notes | `vault/050-Research/` |
| 2. Specification | Feature spec (must fill the **Determinism & Explainability** checklist) | `vault/060-Features/` via `docs/templates/feature-spec.md` |
| 3. Architecture | ADR (if architectural impact) | `docs/adr/` |
| 4. Planning | Sprint plan | `vault/030-Sprints/` |
| 5. Implementation | Code on branch `sim/<desc>`; conventional commits | branch |
| 6. Testing | 90% branch coverage; determinism tests; run `./scripts/test.sh` | `tests/unit/simulation/` |
| 7. Documentation | Update `CHANGELOG.md` `[Unreleased]`, subsystem README, vault, ADR | various |
| 8. Review | PR via `.github/PULL_REQUEST_TEMPLATE.md`; CI passes; CODEOWNER approval | GitHub |
| 9. Merge | Squash-merge (human only); delete branch | `main` |

**Exceptions** (Technical Lead may grant): critical bug fixes may skip research/spec/architecture
but still require testing + documentation. AI agents may skip a step they cannot perform (e.g.
attending a meeting) but must document their work thoroughly.

---

## 5. Commands Cheat-Sheet

| Purpose | Command |
|---|---|
| Lint simulation | `ruff check .` then `ruff format --check .` |
| Type-check simulation | `mypy . --strict` |
| Tests (all subsystems) | `./scripts/test.sh` (Windows: `.\scripts\test.ps1`) |
| Tests (simulation only) | `pytest tests/unit/simulation/ -v` |
| Lint (all subsystems) | `./scripts/lint.sh` (Windows: `.\scripts\lint.ps1`) |
| Pre-commit (all hooks) | `pre-commit run --all-files` |

**Pre-commit hooks** (`.pre-commit-config.yaml`) gate every commit, in order: trailing-whitespace,
end-of-file-fixer, check-yaml/json/merge-conflict, check-added-large-files (>1MB), detect-private-key,
**ruff --fix**, **ruff-format**, **mypy --strict** (excludes `tests/`), **gitleaks**,
python-use-type-annotations, python-check-blanket-noqa, python-check-mock-methods.

---

## 6. CI Gates (what must pass to merge a simulation PR)

From `.github/workflows/ci.yml`, `docker.yml`, and `pr-checks.yml`:

- **`simulation-checks` job** (`ci.yml`): `ruff check .`, `mypy . --strict`,
  `pytest --cov --cov-branch --cov-fail-under=90` — **90% branch coverage is a hard gate**.
- **`prompt-validation` job** (`ci.yml`): validates every `prompts/*.md` has Input/Output schema
  sections (runs on all PRs; relevant if you touched prompts).
- **`docker.yml`**: builds `docker/simulation.Dockerfile` → `ghcr.io/societas/societas-simulation`
  (triggered if `simulation/**` or `docker/**` changed).
- **`pr-checks.yml`**: conventional-commit PR title (`type(scope): description`), no merge
  conflicts (branch must be rebased on `main`), changelog warning, no files >1MB, LFS check.
- **CODEOWNER approval**: `@societas/simulation-engineer` must approve `/simulation/` changes.

---

## 7. Commit & Branch Conventions

- **Branch:** `sim/<description>` (from `main`). Examples: `sim/needs-based-scoring`,
  `sim/economy-subsystem`, `fix/simulation-seed-non-determinism`.
- **Commit message:** `type(sim): description` + blank line + `Refs: #issue, ADR-NNN`
- **Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`
- **Scope:** `sim` for simulation work (use `docs` scope only for pure doc changes)
- **Atomic commits** — one logical change per commit.
- **Rebase before PR** — `git rebase main` before opening a PR.
- **Squash-merge** into `main` only; delete the feature branch after merge.

---

## 8. Cross-Team Coordination Map

The agent must **flag** these coordination points, not act unilaterally. Escalate to the Technical
Lead when a decision affects multiple subsystems, an ADR needs superseding, the workflow needs an
exception, or priority conflicts arise.

| When touching… | Coordinate with | Why |
|---|---|---|
| `shared/` interfaces, schemas, types, constants | Relevant consumer owners (Backend, AI, Frontend) | `shared/` has no single CODEOWNER; breaking changes ripple to all layers |
| `shared/interfaces/i_ai_router.py` or escalation schema | AI Systems Engineer | Defines the LLM boundary contract (ADR-003, ADR-004) |
| `shared/dto/*` or simulation state shape | Backend Engineer + Frontend Engineer | DTOs are the API contract; frontend types mirror `shared/dto/*` (not OpenAPI) |
| CI/CD, CODEOWNERS, root config (`pyproject.toml`, `.pre-commit-config.yaml`) | Technical Lead | Out of simulation ownership |
| Docker / deployment config | Infrastructure / DevOps | |
| An ADR needs superseding | Technical Lead | Only TL may grant workflow exceptions or supersede ADRs |

### Known cross-team issues to be aware of

(From `docs/progress-report-tech-lead-audit.md` and `docs/progress-report-frontend.md`.)

- **DI container loses engine between requests** — backend `container.py` creates a new
  `SimulationService` per request; the engine set on `/simulation/start` is lost on the next call.
- **WebSocket broadcasts not wired into tick lifecycle** — `advance_tick()` does not broadcast
  `tick_completed`/`agent_acted` events; the tick lifecycle must emit events.
- **Dockerfiles don't include `/shared/`** — both backend & simulation Dockerfiles copy only their
  own directory, but every file imports from `shared.*`.
- **Simulation tests are all stubs** — `tests/unit/simulation/test_engine.py` and `test_agents.py`
  are `# TODO: ...; pass` — **zero coverage** (must be fixed before any simulation PR can pass CI).
- **`stop_simulation` accesses `self._engine._is_running`** (private attribute) instead of the
  public `is_running()` interface.
- **Test mock data uses old format** that won't deserialize into current schemas.

---

## 9. Current State & Phase-1 Build Order

The simulation skeleton is **scaffolded** — all interfaces are wired together, but all core logic
is `pass`/TODO stubs. No RNG has been instantiated in simulation code yet. Zero tests exist. The
architectural skeleton is complete; implementation has not started.

**Phase 1 — Simulation Core build order** (from `ROADMAP.md` & Master Context §13):

1. Agent state management (needs, psychology, emotions)
2. World simulation & environment
3. Economy system (resources, employment, wealth)
4. Decision scoring pipeline
5. Ambiguity detection & escalation threshold
6. Hybrid decision fusion framework
7. Action execution engine
8. Tick update & scheduling
9. Crime & enforcement subsystem
10. Simulation-level testing suite

**Implementation rules:**

- Implement against `shared/interfaces/*` (`ISimulationEngine`, `IAgent`, `IPolicyEngine`) and
  consume `shared/schemas/*`, `shared/constants/*`, `shared/types/*`, `shared/events/*`.
- Use `shared/utilities/deterministic_rng.DeterministicRNG` for all randomness.
- Ambiguity detection lives in `AgentDecisionScores.is_ambiguous(threshold)` (`shared/schemas/agent_state.py`).
- The `TickScheduler.schedule_agents()` must sort agents by **deterministic criteria** (currently
  stores the list as-is — marked TODO).
- `TickResult.state_hash` must be computed each tick for reproducibility verification (currently `""`).
- Events are published **synchronously** via `EventBus.publish()` in registration order.

See `docs/progress-report-simulation.md` for the live progress tracker and audit trail.

---

## 10. Coding-Conventions Pointer

Enforced by `docs/guides/coding-standards.md`, `pyproject.toml`, `.editorconfig`, and
`.pre-commit-config.yaml`. Refer to the canonical docs for full detail.

- Python 3.11+; type hints everywhere; Google-style docstrings (Args/Returns)
- `@dataclass` for schemas (follow `shared/` convention — no Pydantic in simulation)
- `abc.ABC` + `@abstractmethod` for interfaces (see `shared/interfaces/`)
- `NewType` aliases for domain primitives (`AgentId`, `TickNumber`, `PolicyId`, `EventId`, ...)
- `field(default_factory=...)` for all mutable defaults
- Explicit `__all__` in every `__init__.py`; module-level docstring in every `.py` file
- Private attributes prefixed with `_`
- Imports grouped: standard library → shared → simulation
- **ruff**: line length 100, double quotes, rule sets `E F I N W UP B SIM ARG C4 T20`
- **mypy**: `--strict`, `disallow_untyped_defs = true`, `ignore_missing_imports = true`
- **.editorconfig**: spaces, indent 4, UTF-8, LF line endings, final newline, trim trailing
  whitespace (indent 2 for YAML/JSON/TOML; `trim_trailing_whitespace = false` for Markdown)
- No wildcard imports (`from module import *`); no comments unless explicitly asked

---

## 11. Feature Spec Determinism & Explainability Checklist

Every feature spec (`docs/templates/feature-spec.md`) for simulation work **must** declare:

- [ ] This feature is deterministic (simulation engine)
- [ ] This feature includes an explainability trace
- [ ] This feature uses LLM (document which prompt) — should be **unchecked** for pure Layer 1 work

---

## Related Documents

- `docs/SOCIETAS_Master_Context.md` — persistent engineering context (v2.0)
- `docs/adr/README.md` — ADR index (ADR-001 Accepted; ADR-002/003/004 Proposed)
- `docs/references/architecture-overview.md` — three-layer system design
- `docs/references/glossary.md` — project terminology
- `docs/progress-report-simulation.md` — live simulation progress tracker
- `docs/progress-report-backend-service-layer.md` — backend status
- `docs/progress-report-frontend.md` — frontend status & API contract findings
- `docs/progress-report-tech-lead-audit.md` — cross-team integration audit
- `ROADMAP.md` — phased delivery plan
