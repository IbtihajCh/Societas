# SOCIETAS

<p align="center">
  <img src="frontend/public/societas_logo_v2.png" alt="SOCIETAS Logo" width="160" />
</p>

> **AI-Powered Governance & Society Simulation Platform**
>
> **AMD Hackathon 2026 — Track 3: Unicorn Pre-Screening**

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" />
  <img src="https://img.shields.io/badge/AMD-Hackathon-red.svg" alt="AMD Hackathon" />
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
</p>

SOCIETAS is a real-time, large-scale agent-based civilisation simulator that models how policy decisions cascade through an artificial society of autonomous individuals with realistic psychological, economic, and social behavior. 1000+ agents live, work, trade, marry, protest, commit crimes, and die on a toroidal grid — governed by a 17-step tick engine, 24 actions, 13 needs across 5 Maslow layers, and an optional 3-model LLM reasoning layer running on AMD MI300X GPUs.

---

## At a Glance

| 🌐 **1000+ Agents** | 🧠 **3-Model LLM** | 🎨 **Dark Dashboard** | ⚡ **24ms/tick** |
|:---:|:---:|:---:|:---:|
| Autonomous citizens with traits, needs, emotions, jobs | Gemma 4 E2B · 26B · 31B on AMD MI300X | Dune Imperial theme, 30×30 agent grid, 11 panels | Deterministic fallback when GPU unavailable |

---

## Quick Start

```bash
# Build and start
docker compose -f docker/docker-compose.yml -p societas up -d --build

# Verify
curl http://localhost:8000/api/v1/health       # {"status":"healthy"}

# Start simulation (100 agents, deterministic)
curl -X POST http://localhost:8000/api/v1/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"population_size":100,"seed":42,"enable_ai":false}'

# Run ticks
curl -X POST http://localhost:8000/api/v1/simulation/tick

# Open dashboard
open http://localhost:3000/dashboard
```

---

## AMD Resource Usage

SOCIETAS leverages **AMD MI300X GPUs** for three-tier LLM reasoning:

| Model | GPU | Purpose | Endpoint |
|-------|-----|---------|----------|
| **Gemma 4 E2B** | MI300X | Agent decision-making (~7–20 calls/tick) | Port 8001 |
| **Gemma 4 26B A4B** | MI300X | Moral reasoning, ethical dilemmas | Port 8002 |
| **Gemma 4 31B Dense** | MI300X | Policy translation, governance, explainability | Port 8000 |

**Batched inference**: Prompt-response payloads are batched (8 agents/request) and cached by `(model, prompt_hash)`, achieving **27× throughput improvement** on the 31B route. End-to-end tick latency with LLM: 2–4 seconds on AMD MI300X (down from 30–90 seconds unbatched).

**Fallback mode**: When LLM endpoints are unavailable, the simulation runs entirely deterministically — all 24 actions, emotions, economy, and governance continue without interruption.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Frontend: Next.js 14 · Dune Imperial Dark Theme     │
│  Dashboard · Agents · Governance · Policies          │
├──────────────────────────────────────────────────────┤
│  Backend: FastAPI · Uvicorn · WebSocket · SQLite      │
│  Simulation Engine · Analytics · Governance · AI     │
├──────────────────────────────────────────────────────┤
│  LLM Layer: vLLM on AMD MI300X (3× Gemma 4)          │
│  E2B (8001) · 26B A4B (8002) · 31B Dense (8000)     │
└──────────────────────────────────────────────────────┘
```

**17-step tick loop**: Age progression → Marriage → Needs decay → Economy (welfare, rent, tax) → Emotions (5-state machine) → Purpose system → Social systems (reputation, gossip, gangs, riots) → Action selection (softmax priority queue across 24 actions) → Grid movement → Death (7 causes) → Birth → World metrics → State hash.

---

## Features

### Simulation Engine
- **1000+ agents** with 8 beta-distributed personality traits
- **13 needs** across 5 Maslow layers (physiological, safety, love, esteem, self-actualization)
- **24 actions**: work, seek_job, befriend, steal, protest, fraud, invest, buy_property, campaign, counsel, treat, hobby, and more
- **3-level decision priority queue**: critical survival → stability → softmax probabilistic choice
- **5-state emotion machine**: Neutral ⇄ Happy ⇄ Sad ⇄ Angry ⇄ Despair
- **Full lifecycle**: birth, aging (child → adult → elderly), marriage, disease, death (7 causes), inheritance

### Economy
- Progressive taxation (poor 0.5×, middle 1.0×, rich 1.5×)
- Welfare system, debt with interest, labor market with supply/demand salaries
- Property market (4 tiers: homeless → basic → standard → premium), rent, eviction
- GDP calculation with 95/5 EMA smoothing, inflation decay
- White-collar crime (fraud with detection probability), business ownership

### Social Systems
- Reputation tracking with decay and gossip propagation
- Communities (BFS clustering), inter-community tension and conflict
- Organized crime gangs (formation, extortion, fights)
- Rumor propagation through social networks
- Riot events triggered by protest intensity + food scarcity
- Political influence and campaigning

### Frontend Dashboard
- **Dark Dune Imperial theme** with Fraunces/Inter/IBM Plex Mono typography
- **30×30 agent grid**: each agent = colored circle (ring = wealth class, body = emotion state)
- **Smooth lerp animation**: agents visibly glide between grid positions
- **10 interactive panels**: Metrics & Gauges, Governance, Wealth Stratification, Entry Log, Model Log, Explain, Diagnostics, Environmental Events, Community Status, Self-Actualization
- **Custom panel builder**: create panels with any 3 of 30+ metrics, each with sparkline charts
- **LLM explainability**: Ask natural language questions about the simulation state
- **LLM fallback indicator**: visible badge when running in deterministic mode

### AI & LLM Integration
- 3-model routing: E2B (decisions), 26B (moral reasoning), 31B (governance/explain)
- Batched prompt requests with caching for 27× throughput
- Mock/deterministic fallback when GPU unavailable
- Explainability endpoint with natural language Q&A
- News generation (media engine with 7 categories, 15% fake news)

---

## Repository Structure

```
societas/
├── backend/          # FastAPI server, routers, services, dependencies
├── frontend/         # Next.js 14 dashboard, components, store
├── simulation/       # Core deterministic simulation engine
│   ├── agents/       # Agent state, decision engine, needs, memory
│   ├── engine/       # Tick loop, simulation engine
│   ├── world/        # Economy, metrics, governance
│   └── events/       # Event bus, media engine
├── shared/           # Shared types, DTOs, constants, schemas
├── docker/           # Dockerfiles, compose, .env
├── docs/             # ADRs, guides, reference architecture
├── tests/            # Integration and regression tests
├── prompts/          # AI prompt templates by purpose
├── models/           # LLM routing and configuration
└── scripts/          # Utility and build scripts
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Backend health check |
| POST | `/api/v1/simulation/start` | Start simulation (configurable pop, seed, AI) |
| POST | `/api/v1/simulation/tick` | Advance one tick |
| POST | `/api/v1/simulation/stop` | Stop simulation |
| GET | `/api/v1/simulation/state` | Full world state (50+ metrics) |
| GET | `/api/v1/agents` | Agent list with filters |
| GET | `/api/v1/agents/{id}` | Agent detail with traits, needs, memories |
| POST | `/api/v1/governance/apply` | Apply tax, welfare, food policies |
| GET/POST | `/api/v1/policies` | Create and list policies |
| POST | `/api/v1/explain` | LLM explainability (rule fallback) |
| GET | `/api/v1/ai/status` | LLM availability check |
| WS | `/ws` | Real-time event stream |

---

## Performance

| Scenario | Agents | Ticks | Time | Per Tick |
|----------|--------|-------|------|----------|
| Deterministic | 100 | 10 | 1.72s | ~24ms |
| Deterministic | 30 | 10 | 0.6s | ~4ms |
| Remote Inference Calls | 80 | 10 | 22–35s | 2,200–3,500ms |
| Hybrid LLM (on AMD MI300X) | 5,000 | 10 | 8–12s | 800–1,200ms |

---

## License

MIT. See [LICENSE](LICENSE).

---

**Built for AMD Hackathon 2026** · AMD MI300X · Gemma 4 · Next.js · FastAPI
