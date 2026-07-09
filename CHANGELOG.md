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
- **Simulation engine v1.0** — full deterministic society simulation core (4167 lines of Python, 475 tests)
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
  - 475 tests passing across 20 test files (14.99s full suite)
- ADR-005: Simulation Implementation Architecture (amends ADR-002/003/004)
- Implementation guide v2.0: 20 sections, all formulas, 6-phase build order, file manifest
- Root AGENTS.md: simulation engineer operating manual with loading protocol

### Changed

- `shared/` schemas and enums extended with Project Guide-aligned fields (ActionType, NeedType, EmotionType, WealthClass, AgentState, SimulationState)
- `shared/utilities/deterministic_rng.py`: added `beta()`, `weighted_choice()`, `integers()` methods
- `shared/constants/defaults.py`: added 50+ simulation constants
- ADR-002/003/004 amended by ADR-005 for E2B hybrid architecture
- `pyproject.toml`: added `pythonpath = ["."]` for pytest path resolution
- `simulation/README.md`: updated with v1 scope and build order

### Deprecated

### Removed

- CI push triggers on `main` (temporarily disabled — skeleton phase)
  - `.github/workflows/ci.yml`: removed push trigger, PR-only now
  - `.github/workflows/docker.yml`: removed push trigger, PR-only now
  - **Re-enable when:** implementation reaches Phase 1 (working simulation + backend code)

### Fixed

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
