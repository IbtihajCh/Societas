# SOCIETAS

**AI-Powered Governance & Society Simulation Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![AMD Hackathon](https://img.shields.io/badge/AMD-Hackathon-red.svg)](https://lablab.ai)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

SOCIETAS is a real-time, explainable, large-scale governance simulator that models how policy decisions cascade through an artificial society of autonomous individuals with realistic psychological, economic, and social behavior.

Unlike traditional simulations, SOCIETAS combines rule-based Agent Based Modeling (ABM), cognitive psychology, behavioral economics, emergent social systems, Large Language Models (Gemma), and explainable AI into a single hybrid cognitive architecture.

---

## Core Philosophy

> **Deterministic systems should model reality. LLMs should model human reasoning.**

The simulation engine remains fully deterministic, explainable, and mathematically grounded. Gemma operates as a reasoning layer — not the simulation itself — augmenting deterministic decisions only when ambiguity exceeds a configurable threshold.

See [Architecture Overview](docs/references/architecture-overview.md) and [AI Philosophy](docs/references/glossary.md).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Layer 3 — Presentation                │
│  Dashboard · Charts · News Feed · Agent Stories · UI    │
├─────────────────────────────────────────────────────────┤
│                   Layer 2 — Cognitive Reasoning         │
│  Gemma LLM · Tie-Breaking · Policy Translation ·        │
│  Narrative Generation · Advisory                        │
├─────────────────────────────────────────────────────────┤
│                   Layer 1 — Deterministic Simulation    │
│  World · Agents · Economy · Needs · Psychology ·        │
│  Emotions · Policies · Environment · Crime · Tick       │
└─────────────────────────────────────────────────────────┘
```

Each layer is independently owned, tested, and deployable. See [docs/references/architecture-overview.md](docs/references/architecture-overview.md).

---

## Repository Structure

```
societas/
├── backend/          # FastAPI server, vLLM router, API layer
├── frontend/         # Dashboard, visualization, user interaction
├── simulation/       # Core deterministic simulation engine
├── docs/             # Project documentation, ADRs, guides
├── vault/            # Obsidian vault (version-controlled knowledge base)
├── prompts/          # AI prompts organized by purpose
├── scripts/          # Build, deploy, and utility scripts
├── presentation/     # Competition materials and slides
├── docker/           # Container definitions and orchestration
├── tests/            # Cross-cutting integration and E2E tests
├── tools/            # Developer tooling configuration
└── .github/          # Issue/PR templates, CI/CD, CODEOWNERS
```

Each directory includes a `README.md` explaining its purpose, ownership, and conventions.

---

## Team

| Role | Focus |
|------|-------|
| **Technical Lead** | Architecture, coordination, code review |
| **Simulation Engineer** | Deterministic engine, ABM, economy |
| **AI Systems Engineer** | Gemma integration, vLLM, prompt engineering |
| **Backend Engineer** | API server, data layer, model routing |
| **Frontend Engineer** | Dashboard, visualization, UX |
| **Infrastructure / DevOps** | Docker, CI/CD, deployment, monitoring |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/societas/societas.git
cd societas

# Run the setup script
# macOS / Linux
./scripts/setup.sh

# Windows
.\scripts\setup.ps1

# Start development environment
docker compose -f docker/docker-compose.yml up -d
```

See [docs/guides/setup.md](docs/guides/setup.md) for detailed setup instructions.

---

## Development Workflow

Every feature follows this pipeline:

**Research → Specification → Architecture → Planning → Implementation → Testing → Documentation → Review → Merge**

AI coding agents must follow the workflow defined in [docs/guides/development-workflow.md](docs/guides/development-workflow.md) and observe the rules in [docs/guides/ai-agent-rules.md](docs/guides/ai-agent-rules.md).

---

## Documentation

| Resource | Location |
|----------|----------|
| Architecture Decisions | [docs/adr/](docs/adr/) |
| Setup Guide | [docs/guides/setup.md](docs/guides/setup.md) |
| Coding Standards | [docs/guides/coding-standards.md](docs/guides/coding-standards.md) |
| Branching Strategy | [docs/guides/branching-strategy.md](docs/guides/branching-strategy.md) |
| Feature Specs | [vault/060-Features/](vault/060-Features/) |
| Sprint Planning | [vault/030-Sprints/](vault/030-Sprints/) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. All contributions must follow the established workflows, pass CI checks, and include documentation updates.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
