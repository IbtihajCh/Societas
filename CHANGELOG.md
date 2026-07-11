# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Repository structure and folder hierarchy
- GitHub configuration (issue/PR templates, CODEOWNERS, CI/CD)
- Documentation system (ADRs, guides, templates, standards)
- Docker environment with multi-service orchestration
- Obsidian vault as version-controlled knowledge base
- Prompt management system organized by purpose
- Development workflow and branching strategy
- Coding standards and testing requirements
- AI agent operational rules
- Architecture Decision Record system
- Engineering operating system foundation
- **Simulation engine v1.0** — full deterministic society simulation core (4300 lines of Python, 500 tests)
  - Shared module extensions: 15 action types, 13 need types (5 Maslow layers), 5 emotional states, 3 wealth classes, 11 job types, Beta-distributed traits
  - Agent factory: 7 Beta-distributed traits per agent, socioeconomic initialization, job assignment
  - Needs system: 13 needs with exact decay rates, scarcity multiplier, crime pressure
  - Unlust engine: exact Freudian formula (5 weighted deficits), morality gate, Thanatos detection
  - Emotion engine: 5-state machine with hysteresis timers, happiness composite score, sleep reset, productivity modifiers
  - Decision architecture: E2B hybrid prompts, 5-condition moral dilemma detection, LLM response parsing, action validation, deterministic 3-level fallback
  - Action system: 14 actions (work, buy_food, rest, seek_job, beg, befriend, console, isolate, share, steal, harm_other, protest, complain, comply) with full state effects
  - Adler comparison engine: Maslow hierarchy score, upward/downward social comparison
  - Economy: 11 job types with salary ranges, wealth class derivation, rent/welfare/tax
  - Grid system: 20x20 toroidal grid, nearby agent detection, random walk movement
  - Policy system: dual model (ImpactDeltas per wealth class + PolicyWeights), keyword fallback for 8 policy types
  - Tick loop: 10-step cycle wiring all modules, staggered LLM evaluation (1/3 agents per tick)
  - Mock AI router: deterministic LLM mock for testing without GPU
  - Metrics: world-level + wealth-stratified metrics, SHA-256 state hash for determinism verification
  - 500 tests passing across 20 test files (60s full suite)
- ADR-005: Simulation Implementation Architecture (amends ADR-002/003/004)
- Implementation guide v2.0: 20 sections, all formulas, 6-phase build order, file manifest
- Root AGENTS.md: simulation engineer operating manual with loading protocol
- `SimulationEngine.tick()` wired to `run_tick()` — `start()`/`reset()` lifecycle methods, 18 real engine tests
- P1-P5 tuning: unlust threshold (0.5→0.7), weighted fallback (14 actions), death pathways (threshold 0.02 + job loss), wealth-class multipliers, MockAIRouter trait-aware variety
- 29 scenario tests with 6 detailed reports and meta-analysis
- Cross-team integration guide for backend/AI/frontend/devops
- Engine reference doc (concise guide for other teams)
- vLLM integration spec for AI Systems Engineer
- Development playbook (`simulation/development-playbook.md`)
- **v2 engine calibration** (2026-07-11) — 8-tweak campaign + Goldilocks search fixes default-config extinction
  - `simulation/PROGRESS_REPORT.md` — comprehensive 600-line report of v2 calibration work
  - `docs/guides/llm-integration-guide.md` — 1519-line guide for AI engineer (8 prompt templates, event integration, test fixtures, end-to-end tick worked example, 9-step first-action checklist)
  - `tests/unit/simulation/test_agent_registry.py` — 207-line new test file (was missing entirely; coverage was 0%)

### Changed

- `shared/constants/defaults.py` (v2 calibration, breaking): `ANGRY_UNLUST_THRESHOLD` 0.58→0.45, `DESPAIR_UNLUST_THRESHOLD` 0.82→0.55, `UNLUST_MORALITY_GATE` 0.58→0.38 (invariant: GATE < DESPAIR so zone 2 is reachable), `BIRTH_CHANCE_BASE` 0.0001→0.005 (Goldilocks), `ECONOMIC_HARDSHIP_DEATH_RATE` 0.003→0.001, `AGE_MORTALITY_ELDERLY` 0.002→0.001, `SLEEP_DECAY_RATE` 0.04→0.02, `FOOD_DECAY_RATE` 0.018→0.012, `WATER_DECAY_RATE` 0.014→0.008, `AGE_PROGRESSION_INTERVAL` 1→0.1

- `shared/` schemas and enums extended with Project Guide-aligned fields (ActionType, NeedType, EmotionType, WealthClass, AgentState, SimulationState)
- `shared/utilities/deterministic_rng.py`: added `beta()`, `weighted_choice()`, `integers()` methods
- `shared/constants/defaults.py`: added 50+ simulation constants
- ADR-002/003/004 amended by ADR-005 for E2B hybrid architecture (status: Proposed → Accepted)
- `shared/dto/agent_dto.py`: `WealthClass.WORKING` → `WealthClass.MIDDLE` (2 occurrences)
- `backend/app/services/simulation_service.py`: Fixed `state.tick` → `state.time_step`, nested attrs → top-level fields
- ADR-005: Status changed from Proposed to Accepted
- `simulation/README.md`: updated with 500 tests, Quick Start code example, engine integration docs
- `docs/progress-report-simulation.md`: updated to 500 tests, added audit trail entries
- `docs/implementation-summary.md`: updated to 500 tests, 9 commits, engine integration docs
- `pyproject.toml`: added `pythonpath = ["."]` for pytest path resolution
- `simulation/README.md`: updated with v1 scope and build order

### Deprecated

### Removed

- CI push triggers on `main` (temporarily disabled — skeleton phase)
  - `.github/workflows/ci.yml`: removed push trigger, PR-only now
  - `.github/workflows/docker.yml`: removed push trigger, PR-only now
  - **Re-enable when:** implementation reaches Phase 1 (working simulation + backend code)

### Fixed

- **v2 engine critical bugs** (2026-07-11)
  - `simulation/agents/decision_engine.py:396` — `EmotionType.SADNESS` → `EmotionType.SAD` (typo crashed moral-dilemma path; entire `DESPAIR` emotion unreachable)
  - `simulation/agents/decision_engine.py:339-351` — 11 dead actions added to `deterministic_fallback` base_scores (fraud, treat, counsel, campaign, comply, spread_rumor, support_family, invest, buy_property, hobby, idle)
  - `simulation/engine/tick_loop.py:142` — order-independence sort (`living_agents.sort(key=lambda a: a.id)`) so same seed = same result regardless of input order
  - `simulation/agents/lifecycle.py:115,117` — ambitious birth_chance bonus 0.2→0.0002 + happiness bonus 0.001→0.0001 (was causing 200+ births per 200-tick run; population exploded 80→234)
  - `simulation/agents/needs_calculator.py` — wired all 8 death pathways (FOOD, WATER, HEALTH with rng prob, SLEEP with rng prob, DESPAIR, EXISTENTIAL via purpose_fulfillment, AGE, ECONOMIC); added passive health decay 0.001/tick in `decay_needs()`
  - `simulation/world/economy.py` — `INFLATION_DECAY_RATE` now wired into `process_economy_tick` via `world.economy.inflation_rate` (was a dead constant)
  - `simulation/agents/action_executor.py` — `SLEEP_REPLENISH_RATE` removed from `decay_needs` (replenishment only via REST action; prevents auto-sleep rise)
  - `simulation/agents/agent_factory.py:273-282` — removed 10% elderly starter population (combined with `AGE_PROGRESSION_INTERVAL=1` caused 80% deaths by tick 200)
  - `simulation/test_reports/sweep_runner.py` — `assign_initial_housing()` called for all agents after `create_initial_population` (property market was effectively dead)
  - `simulation/agents/memory_system.py:17` — added missing `from typing import Optional` import
  - `prompts/agent_decision.md`, `prompts/moral_reasoning.md` — action enum updated to full 25 actions (was 15)

### Security

---

## [0.1.0] — 2026-07-07

### Added

- Project initialization
- Master Context & Architecture Decisions v2.0
- Competition strategy (AMD + Gemma dual-track)
- Three-layer system architecture design
- Dual-process cognitive architecture (System 1 / System 2)
- Escalation threshold and hybrid decision fusion design
- AI responsibility matrix and model routing design
- Feature prioritization
- Team role definitions

[Unreleased]: https://github.com/societas/societas/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/societas/societas/releases/tag/v0.1.0
