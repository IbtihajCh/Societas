# SOCIETAS Roadmap

> **Status:** Pre-development — Engineering OS phase
>
> **Last updated:** 2026-07-07
>
> See also: [CHANGELOG](CHANGELOG.md), [Architecture Decisions](docs/adr/), [Feature Specifications](vault/060-Features/)

---

## Phase 0 — Engineering Operating System (Current)

**Goal:** Establish the full engineering environment before writing any simulation code.

- [x] Architecture decisions (Master Context v2.0)
- [x] Competition strategy (AMD + Gemma dual-track)
- [ ] Repository structure and folder hierarchy
- [ ] GitHub configuration (templates, CI/CD, CODEOWNERS)
- [ ] Documentation system (ADRs, guides, standards)
- [ ] Docker environment and local dev setup
- [ ] Obsidian vault structure
- [ ] Prompt organization and management
- [ ] Team onboarding documentation

**Owner:** Technical Lead

---

## Phase 1 — Simulation Core

**Goal:** Build the deterministic simulation engine.

Priority order from [Master Context §13](docs/SOCIETAS_Master_Context.md):

- [ ] Agent state management (needs, psychology, emotions)
- [ ] World simulation and environment
- [ ] Economy system (resources, employment, wealth)
- [ ] Decision scoring pipeline
- [ ] Ambiguity detection and escalation threshold
- [ ] Hybrid decision fusion framework
- [ ] Action execution engine
- [ ] Tick update and scheduling
- [ ] Crime and enforcement subsystem
- [ ] Simulation-level testing suite

**Owner:** Simulation Engineer

---

## Phase 2 — AI Integration

**Goal:** Integrate Gemma as the cognitive reasoning layer.

- [ ] vLLM deployment and FastAPI router
- [ ] Tie-break schema and escalation handler
- [ ] Policy translation pipeline
- [ ] Persona generation (one-time per agent)
- [ ] Narrative generation (news feed)
- [ ] Spotlight narration
- [ ] Governance advisor (stretch goal)
- [ ] Prompt validation framework
- [ ] Batch inference optimization

**Owner:** AI Systems Engineer

---

## Phase 3 — Presentation Layer

**Goal:** Build the dashboard and user interaction layer.

- [ ] Real-time simulation dashboard
- [ ] Agent state visualization
- [ ] Economic charts and metrics
- [ ] News feed UI
- [ ] Agent story viewer
- [ ] Policy configuration interface
- [ ] Policy impact reports
- [ ] User interaction controls

**Owner:** Frontend Engineer

---

## Phase 4 — Backend & API

**Goal:** Connect all layers through a robust API.

- [ ] FastAPI application structure
- [ ] REST API for simulation control
- [ ] WebSocket for real-time updates
- [ ] Data persistence and storage
- [ ] Model routing and queue management
- [ ] Authentication (if needed for demo)
- [ ] API documentation (OpenAPI)
- [ ] Integration tests

**Owner:** Backend Engineer

---

## Phase 5 — Integration & Demo Preparation

**Goal:** Deliver a working demo for the competition.

- [ ] End-to-end integration testing
- [ ] Performance profiling and optimization
- [ ] AMD hardware verification
- [ ] Gemma model validation
- [ ] Demo scenario creation
- [ ] Presentation materials
- [ ] Competition submission

**Owner:** All

---

## Post-Hackathon — Future Directions

- [ ] Hybrid narrative override system
- [ ] Communities and social groups
- [ ] Family structures and inheritance
- [ ] Political parties and elections
- [ ] Religion and belief systems
- [ ] Organized crime networks
- [ ] International relations and trade
- [ ] Real-time multiplayer policy sandbox

---

## Feature Priority Matrix

| Feature | Phase | Priority | Depends On |
|---------|-------|----------|------------|
| Simulation Engine | 1 | Must Ship | — |
| Dashboard | 3 | Must Ship | Simulation |
| Policy Translation | 2 | Must Ship | AI Integration |
| News Feed | 2 | Must Ship | Simulation |
| Spotlight Narration | 2 | High | Simulation |
| Governance Advisor | 2 | Stretch | AI Integration |
| Communities | Post | Future | Simulation |

---

## Timeline

See [Sprint Plans](vault/030-Sprints/) for current sprint details and [Meeting Notes](vault/040-Meetings/) for weekly progress.
