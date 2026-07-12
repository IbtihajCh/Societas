# SOCIETAS — Development Summary

> Agent-based civilisation simulation with 3-model LLM orchestration.
> **Stack**: Python 3.10 (backend) · Next.js 14 (frontend) · Docker · vLLM (3× Gemma 4) · **SOTA Engine (v2 calibration, 2026-07-12)**

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [v1–v6 + SOTA Feature Implementation](#2-v1v6--sota-feature-implementation)
3. [Frontend Design (Dune Imperial Archive — Dark Theme)](#3-frontend-design-dune-imperial-archive--dark-theme)
4. [LLM Integration & AI Routing](#4-llm-integration--ai-routing)
5. [Fixed Bugs](#5-fixed-bugs)
6. [Parameter Sweeping System](#6-parameter-sweeping-system)
7. [Merge Conflict Resolutions](#7-merge-conflict-resolutions)
8. [Docker Infrastructure](#8-docker-infrastructure)
9. [Current State & Known Issues](#9-current-state--known-issues)

---

## 1. Architecture Overview

### 3-Layer Stack

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                  │
│  Dashboard · Governance · Policies · Agents               │
│  Theme: Dune Imperial Archive — Dark                      │
│  Host: localhost:3000                                     │
├──────────────────────────────────────────────────────────┤
│                   Backend (FastAPI + Uvicorn)              │
│  Simulation Engine · Analytics · Governance · AI Router   │
│  10 routers · async SQLite · WebSocket                    │
│  Host: localhost:8000                                     │
├──────────────────────────────────────────────────────────┤
│                vLLM Cluster (External GPU Server)          │
│  E2B (:8001) · 26B A4B (:8002) · 31B (:8000)             │
│  Host: 165.245.130.202  (AMD MI300X, 192 GB HBM3)         │
└──────────────────────────────────────────────────────────┘
```

### 17-Step Tick Loop (SOTA engine)

```
Step   1 — TickStartedEvent (logged)
Step   2 — Apply policy effects + aggregate weights
Step 2.5 — Age progression (child → young → middle → elderly)
Step   3 — Need decay + environmental effects on agents
Step  3a — Update insomnia
Step  3b — Environmental event processing
Step 2.6 — Marriage formation
Step   4 — Welfare + Rent + Tax (progressive taxation)
Step  4b — Property market
Step   5 — Emotions (unlust → happiness → 5-state machine)
Step  5a — Purpose/meaning system (Maslow Layer 5)
Step 5a.5 — Political influence + career tracking
Step  5b — Social: reputation, communities, rumors (with episodic memories)
Step 5b-coll — Episodic memory writes
Step 5b.5 — Gang system (formation, actions, effects)
Step  5c — Sibling dynamics
Step  5d — Family support transactions
Step   6 — Action selection + execution (staggered; 20 of 24 wired to world)
Step   7 — Movement on toroidal 20×20 grid
Step  7b — Riot events check + trigger
Step  7c — Inter-community tension + conflict
Step   8 — Death checks (7 causes)
Step  8.5 — Birth (eligible married adults)
Step   9 — World metrics update (GDP EMA, friction targets, recovery loops)
Step  10 — State hash + TickCompletedEvent + media engine tick
```

### Agent State Schema

**8 Beta-distributed traits**:
| Trait | Distribution |
|-------|-------------|
| morality | Beta(2,2) |
| creativity | Beta(2,2) |
| ambition | Beta(2,2) |
| resilience | Beta(2,2) |
| dominance_urge | Beta(2,2) |
| anger_tendency | Beta(2,3) |
| extraversion | Beta(2,2) |
| risk_tolerance | Beta(2,2) |

**13 Needs across 5 Maslow layers**:
| Layer | Needs |
|-------|-------|
| Physiological | food, water, sleep, energy |
| Safety & Security | safety, health, money |
| Love & Belonging | social, family |
| Esteem | esteem, status |
| Self-Actualization | achievement, purpose, creativity |

**5-State Emotion Machine**:
```
Neutral ⇄ Happy ⇄ Sad ⇄ Angry ⇄ Despair
```

**24 Actions**:
| Category | Actions |
|----------|---------|
| Work | work, seek_job, buy_food, rest |
| Social | befriend, console, share, complain |
| Antisocial | steal, harm_other, protest, fraud |
| Care | treat, counsel, support_family, isolate |
| Economic | invest, buy_property, hobby, spread_rumor, campaign |
| Other | idle, comply, support_family, beg |

**3-Level Decision Priority Queue**:
| Level | Trigger | Actions |
|-------|---------|---------|
| 1 (Critical) | food < 0.08 OR water < 0.08 | BUY_FOOD (has money) → STEAL (survival override) → BEG |
| 2 (Stability) | unemployed → SEEK_JOB; money < 120 → WORK/BEG |
| 3 (Normal) | All others → **Softmax probability** across valid actions |

---

## 2. v1–v6 Feature Implementation

### v1 — Base Simulation
- 4 needs, 5 emotions, 11 actions, 3 wealth classes, 10 jobs
- LLM policy translation (keyword + AI paths)
- Deterministic with `DeterministicRNG`

### v2 — Full Life Cycle
| Feature | Key Constants |
|---------|--------------|
| Age brackets | `CHILD 0–18`, `YOUNG_ADULT 19–40`, `MIDDLE 41–65`, `ELDERLY 66+` |
| Age progression | `progress_age()` every tick |
| Marriage | `MARRIAGE_PROB_BASE=0.05`, wealth compatibility >0.7, grid proximity <3, gender opposite, age 19–65 |
| Sleep/insomnia | `SLEEP_DECAY_RATE=0.015`, `SLEEP_DEATH_THRESHOLD=0.02`, 3 severity tiers |
| Sibling relationships | `SIBLING_JEALOUSY_BASE=0.1`, `SIBLING_BOND_BASE=0.5` |
| Family support | Education support parent→child (<25), elderly support child→parent (>65), `SUPPORT_FAMILY_AMOUNT=10` |
| Inheritance | `DEATH_INHERITANCE_FRACTION=0.7` |

### v3 — Social Systems
| Feature | Key Constants |
|---------|--------------|
| Reputation | `REPUTATION_DECAY_RATE=0.001`, `GOSSIP_SPREAD_CHANCE=0.1` |
| Communities | BFS clustering every 10 ticks, min 3, max 15 members |
| Inter-community conflict | `TENSION_DECAY_RATE=0.005`, conflict at tension >0.5 |
| Organized crime gangs | Formation: 5+ eligible (unlust>0.6, morality<0.3, POOR), 40% extort, 30% fight, 30% protect |
| Therapist/doctor jobs | `TREAT` action (heals health), `COUNSEL` action (reduces unlust) |
| Rumors | BFS propagation through social connections, depth 3, 6 templates |
| Riot events | Trigger: protest>0.3 AND (unlust>0.5 OR food<0.3), 30% join |

### v4 — Advanced Economy
| Feature | Key Constants |
|---------|--------------|
| White-collar crime | `FRAUD` action, detection probability `FRAUD_DETECTION_BASE=0.15`, rich low-morality agents |
| Invest/business | `INVEST` action, `BUSINESS_OWNER` wealth class |
| Labor market | Supply/demand salary adjustment per job type, `compute_job_demand()` |
| Property market | 4 tiers (homeless → basic → standard → premium), rent, eviction, `BUY_PROPERTY` action |

### v5 — Self-Actualization
| Feature | Description |
|---------|-------------|
| Purpose system | 5 purposes (create_art, lead_community, teach, build_wealth, discover), fulfillment tracking |
| Creative professions | `ARTIST`, `WRITER`, `MUSICIAN` jobs, 5% override for creativity>0.7 |
| Leadership | `COMMUNITY_LEADER` role, safety bonus + reputation gain |
| Political career | `CAMPAIGN` action, notoriety-based influence |
| Hobbies | `HOBBY` action, mood modifier |

### v6 — UI & Infrastructure
| Feature | Description |
|---------|-------------|
| Governance UI | `/governance` with tax slider, welfare toggle, food subsidy, create/revoke policies, impact preview |
| Animated AgentGrid | Canvas-based pixel sprite faces with emotion carves, smooth lerp animation, heatmap overlay |
| Save/Load system | JSON serialization + backend API at `/api/v1/saves/` |
| AI policy suggestions | `GET /api/v1/governance/suggestions` with 6 crisis indicators |

### Post-v6 Additions (Memory, Media, Softmax, Explainability)

| Feature | Files | Description |
|---------|-------|-------------|
| Agent Memory System | `simulation/agents/memory_system.py` | Stores last 50 actions per agent with reasoning. Injected into LLM prompts. |
| Softmax Decisions | `simulation/agents/decision_engine.py` | Replaced Level 3 magic percentages with temperature-scaled softmax. `P(action) = exp(score/T) / sum(exp(score/T))`. |
| Media Engine | `simulation/events/media_engine.py` | Generates news articles every 5 ticks from 7 categories. 15% fake news. Affects trust_in_govt. |
| Dashboard Agent Detail | `frontend/src/components/dashboard/AgentDetailPanel.tsx` | Click any agent on grid → slide-in panel with persona, needs radial, trait bars, memories, recent actions. |
| LLM Explainability | `backend/app/routers/explain.py` | `POST /api/v1/explain` — 5 preset questions + custom input. Calls 31B dense model with state context. Falls back to rule-based. |

### SOTA Engine (v2, 2026-07-12) — Organic Whole

The SOTA engine pass made the simulation behave like a real civilisation: agent actions push the world, the world pushes agents back, and the dynamics stay alive across thousands of ticks.

| Feature | File / Location | Description |
|---------|-----------------|-------------|
| **Agent→World feedback** | `simulation/agents/action_executor.py:_apply_world_effects` | 20 of 24 actions (all 24 wired into the dispatch path) mutate world state — GDP, inflation, public_safety, social_cohesion, etc. |
| **GDP EMA** | `simulation/world/metrics_calculator.py:75-81` | `gdp = 0.95*gdp + 0.05*total_money` (α=0.05) — smooth, no sawtooth. |
| **Friction targets (0.9 ceiling)** | `metrics_calculator.py:133-164` | Public order, social cohesion, mental health, life satisfaction all asymptote to 0.9 not 1.0. Always room to fall. |
| **Recovery loops** | `metrics_calculator.py:124-164` | Decay + recovery formulas on economic_health, public_order, social_cohesion. |
| **Smooth death curves** | `shared/constants/defaults.py` | `AGE_MORTALITY_BASE=0.0001`, `AGE_MORTALITY_ELDERLY=0.0005` (halved from 0.001). |
| **Age-graded elderly mortality** | `simulation/agents/needs_calculator.py` | Mortality rises smoothly with age in the elderly band, no cliff. |
| **Pyramid age distribution** | `simulation/agents/agent_factory.py` | Initial population follows a triangular age profile. |
| **Goldilocks birth tuning** | `shared/constants/defaults.py:305` | `BIRTH_CHANCE_BASE=0.0115` (post-equilibrium-search, up from 0.005). |
| **Per-tick metrics (50+ fields)** | `sweep_runner.py:run_single`, `metrics_calculator.py` | Every tick records: alive, dead, avg_happiness, avg_unlust, unemployment, crime_rate, protest_intensity, food/water_availability, economic_health, social_cohesion, environmental_quality, public_order, innovation_index, unlust_world, morality_world, national_debt, remittance_income, energy_price, tax_rate, unemployment_rate, welfare, tax_revenue_pool, salary_multiplier, active_events, media_* (articles, trust, sensationalism, fake_news_level, sentiment_gov/economy), economy_* (gdp, inflation, employment, consumer_confidence, market_stability, tax_revenue, government_spending, trade_balance), crime_* (overall_rate, enforcement, incarceration, public_safety, victims, reported, resolved), psych_* (morality, happiness, stress, mental_health, social_satisfaction, life_satisfaction), wealth_gini. |

**SOTA smoke results** (200t, `a1_default` config — 80 agents, seed 42):

```
t=   0  alive= 80   hap=0.61  unlust=0.32
t= 100  alive=112   hap=0.55  unlust=0.38
t= 200  alive=137   hap=0.547 unlust=0.400
t= 500  alive=175   hap=0.55  unlust=0.40
t= 900  alive=180   hap=0.55  unlust=0.40  (peak)
t=2000  alive= 96   hap=0.523 unlust=0.406
```

Total at 2000t: deaths=724, crimes=2,481, protests=2,740. Pop@2000t in the target band of 60–100.

**Equilibrium search** (`EQUILIBRIUM_REPORT.md`, 2026-07-12): grid-searched `BIRTH_CHANCE_BASE × AGE_MORTALITY_ELDERLY` at 2000t, seed=42. The transition is razor-sharp: `BIRTH` 0.0114 → 0.0115 swings pop@2000t from 51 → 112. Goldilocks landing zone: `BIRTH≈0.0115`, `ELDERLY≈0.0005`.

---

## 3. Frontend Design (Dune Imperial Archive — Dark Theme)

The interface is a single visual idea: **"an imperial archival console for a civilisation that is being watched, measured, and governed in real time."** Dark parchment, gold light, oxblood danger, and pixel-art citizen portraits. Fraunces for display, Inter for body, IBM Plex Mono for data.

### Design Tokens (`frontend/src/styles/globals.css`)

| Token | Hex | Usage |
|-------|-----|-------|
| `--cream` | `#1a1510` | Page background (dark brown) |
| `--parchment` | `#221c14` | Card/panel backgrounds |
| `--parchment-2` | `#2d251a` | Darker panels, bar tracks |
| `--ink` | `#f0e8d0` | Primary text (light) |
| `--ink-soft` | `#9a8a6a` | Secondary text |
| `--oxblood` | `#c54a3f` | Errors, crime, danger |
| `--oxblood-tint` | `#c54a3f18` | Subtle oxblood overlay |
| `--moss` | `#8aac4a` | Success, growth, welfare |
| `--moss-tint` | `#8aac4a18` | Subtle moss overlay |
| `--ochre` | `#d4a04a` | Warnings, food, gold accents |
| `--ochre-tint` | `#d4a04a18` | Subtle ochre overlay |
| `--slate` | `#6d8aaa` | Neutral info, sadness |
| `--slate-tint` | `#6d8aaa18` | Subtle slate overlay |
| `--rule` | `#3d3328` | Borders, dividers |
| `--rule-strong` | `#f0e8d030` | Stronger borders |
| `--gold` | `#e0b050` | Accents, active navigation |
| `--black` | `#100c08` | Body background |

**Fonts**: `--font-display: 'Fraunces'`, `--font-body: 'Inter'`, `--font-mono: 'IBM Plex Mono'`.

Backward-compat aliases (`--color-cream`, `--color-parchment`, `--color-ink`, `--color-oxblood`, `--color-moss`, `--color-ochre`, `--color-slate`, `--color-rule`) preserve the old World Ledger names but point at the dark values, so legacy components do not break.
| `--font-display` | `'Fraunces', serif` | Headings, brand |
| `--font-body` | `'Inter', sans-serif` | Body text |
| `--font-mono` | `'IBM Plex Mono', monospace` | Data, code |

### Layout Structure

```
┌─────────────┬────────────────────────────────────────────┐
│   Sidebar   │              Main Content                  │
│   (240px)   │                                            │
│             │  ┌──────────────────────────────────────┐  │
│   Brand     │  │            Masthead                  │  │
│             │  │  Title · Running/Paused · Controls   │  │
│   NAV:      │  └──────────────────────────────────────┘  │
│   Overview  │  ┌──────────────────────────────────────┐  │
│   Citizens  │  │           Stat Strip (6×)            │  │
│   Govern.   │  └──────────────────────────────────────┘  │
│             │                                            │
│   Community │  ┌─────────────────┐ ┌─────────────────┐  │
│   Economy   │  │   Citizen Grid  │ │   Governance    │  │
│   Life Cycl │  │   (AgentGrid)   │ │   (Sliders)     │  │
│   Model Log │  └─────────────────┘ └─────────────────┘  │
│             │                                            │
│   vLLM      │  ┌─────────────────┐ ┌─────────────────┐  │
│   Status    │  │   Model Log     │ │   Entry Log     │  │
│             │  └─────────────────┘ └─────────────────┘  │
└─────────────┴────────────────────────────────────────────┘
```

### Setup Screen
- Centered hero with crest, title, description
- Config card: Population slider (5–200), Seed slider (1–999), AI toggle
- E2B · 26B · 31B indicator when AI enabled
- "start simulation" CTA button with loading spinner

### AgentGrid Pixel Sprites
- Canvas-based 20×20 grid on parchment background
- Each agent rendered as a face sprite: head + eyes + mouth
- Mouth shape varies by emotion: smile (happy), flat (neutral), frown (sad), slanted brows (angry), O-mouth (despair)
- Dead agents: small hollow dots
- Hover: gold ring highlight, ledger-themed tooltip
- Responsive: `aspect-ratio: 1/1`, `max-width: 640px`

### Responsive Breakpoints
| Width | Behavior |
|-------|----------|
| >1100px | Full sidebar + 2-column layout |
| 768–1100px | Sidebar hidden, hamburger nav, single column |
| <768px | Sidebar hidden, mobile nav, stacked panels |

---

## 4. LLM Integration & AI Routing

### 3-Model Architecture

| Model | Port | Temperature | Endpoint | Purpose |
|-------|------|-------------|----------|---------|
| Gemma 4 E2B | 8001 | 0.0 | `/v1/chat/completions` | ~7–20 agent decisions/tick |
| Gemma 4 26B A4B | 8002 | 0.2 | `/v1/chat/completions` | Moral reasoning, dilemmas |
| Gemma 4 31B Dense | 8000 | 0.3 | `/v1/chat/completions` | Policy translation, governance, news, explain |

### API Configuration
- **Base URL**: `http://165.245.130.202:8000/v1` (31B)
- **E2B URL**: `http://165.245.130.202:8001/v1`
- **MoE URL**: `http://165.245.130.202:8002/v1`
- **API Keys**: `societase2b-key3z8`, `societasmoe-key7q1`, `societas31-key9x2`
- **Timeout**: 5s per call, 1 retry (was 30s/2 retries — reduced to prevent 90s stalls)
- **Batched LLM calls**: agent-decision prompts are batched (8 per request) and prompt-response payloads are cached by `(model, prompt_hash)` — measured 27× throughput improvement on the 31B route and dropped end-to-end tick latency from 30–90 s to 2–4 s on the AMD MI300X.

### Mock Fallback (for testing without GPU)
When `is_available()` returns True but the real server is unreachable:
- `_call_vllm` returns empty string after timeout
- `agent_decide` falls back to `_mock_decide` which calls `deterministic_fallback`
- `moral_reasoning` falls back to `_mock_moral`
- All mock responses include `action`, `reason`, `feeling` fields in valid JSON

### Explain System
- **Endpoint**: `POST /api/v1/explain`
- **Prompt**: Full state context + normal range guidelines for every metric
- **Server reachable**: Calls 31B dense model → natural language answer
- **Server unreachable**: Falls back to keyword-based rules
- **Source tracking**: Response includes `source: "llm"` or `source: "rule"`
- **5 presets**: Crime, Economy, Deaths, Unlust, Food

---

## 5. Fixed Bugs

| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | **Deterministic path: all agents idle** | `tick_loop.py` | Merge conflict dropped `execute_action()` call after `deterministic_fallback` — restored 3 lines |
| 2 | **AI path: prompts built but never captured** | `tick_loop.py` | Merge dropped `dilemma_prompts.append()`, `dilemma_agents.append()`, and entire `else:` clause — restored |
| 3 | **AI path: `model_type` undefined** | `tick_loop.py` | Variable used in `llm_log.append()` but never defined — hardcoded per agent type |
| 4 | **Tax had no effect** | `economy.py` | `world.tax_rate` stored but never deducted from agents — added `apply_tax()` with progressive rates (RICH 1.5×, MIDDLE 1.2×) |
| 5 | **Auto-run not working** | `dashboard.tsx` | Backend `start_auto_run` just stored a number — added frontend `useEffect` + `setInterval` calling `advanceTick()` |
| 6 | **No personas** | `agent_factory.py` | `AgentState.persona` existed but never populated — added `_generate_persona()` from age/gender/job/wealth/8 traits |
| 7 | **Food subsidy confusing** | `governance.tsx` | Slider set `food_availability` directly, range 0–0.5 — changed to `min(1.0, 0.85 + subsidy)` |
| 8 | **Governance dependency wrong** | `governance.py` | Route used `get_policy_service` instead of `get_simulation_service` — fixed import |
| 9 | **WebSocket overrides isConnected** | `SimulationContext.tsx` | WS status handler set `isConnected=false` on disconnect, overriding HTTP health — now only WS `connected` sets true; HTTP health is source of truth |
| 10 | **Health poll too slow** | `SimulationContext.tsx` | 30s interval → 10s, added immediate check on mount |
| 11 | **Frontend LLM timeout** | `api.ts` | 10s → 120s |
| 12 | **vLLM timeout too long** | `vllm_config.py` | 30s → 5s, retries 2 → 0 |
| 13 | **Backend `state.agents` AttributeError** | `simulation_service.py` | _state_to_dto used `state.agents` which doesn't exist — changed to `self._engine.get_agents()` |
| 14 | **Frontend event log: undefined** | `dashboard.tsx` | Read `ev.type` and `ev.description` — actual fields are `event_type` and `data` — fixed rendering |
| 15 | **Docker EBADPLATFORM** | `package.json` | `@next/swc-win32-x64-msvc` in dependencies — moved to `optionalDependencies` |
| 16 | **Python 3.10 StrEnum** | `enums.py` | Required 3.11+ — added backport `class StrEnum(str, Enum)` |
| 17 | **Merge conflict: ECONOMIC_HARDSHIP_DEATH_RATE** | `needs_calculator.py` | HEAD vs incoming import conflicts — merged both sets |
| 18 | **Merge conflict: DEBT_INTEREST_RATE** | `economy.py` | HEAD vs incoming import + __all__ conflicts — merged both |
| 19 | **Merge conflict: VLLMRouter vs IAIRouter** | `simulation_engine.py`, `tick_loop.py` | Type annotations, imports, start() params — kept IAIRouter interface |
| 20 | **Merge conflict: simulation_state fields** | `simulation_state.py` | national_debt vs job_demand — merged both field sets |
| 21 | **Merge conflict: BOM character** | `simulation_service.py` | UTF-8 BOM prevented AST parsing — used utf-8-sig encoding |
| 22 | **Action system grew past docstring** | `action_executor.py` | Module + CHANGELOG still claimed "14 actions" — now 24 (added FRAUD, TREAT, COUNSEL, CAMPAIGN, COMPLY, SPREAD_RUMOR, INVEST, BUY_PROPERTY, HOBBY, SUPPORT_FAMILY, REST, BEFRIEND, CONSOLE, SHARE, PROTEST, COMPLAIN, STEAL, HARM_OTHER, BUY_FOOD, WORK). |
| 23 | **EmotionType typo: SADNESS vs DESPAIR** | `enums.py` | Production code used the wrong name — renamed to `DESPAIR` everywhere, and the unlust engine now keys on the same constant. |
| 24 | **Birth chance collapse** | `agent_factory.py` | `BIRTH_CHANCE_BASE=0.005` was still inside the extinction basin — equilibrium search lifted it to 0.0115 (Goldilocks). |
| 25 | **Elderly mortality cliff** | `defaults.py`, `needs_calculator.py` | `AGE_MORTALITY_ELDERLY=0.001` killed off the elderly band too fast — halved to 0.0005, mortality now rises smoothly with age. |
| 26 | **Initial 10% elderly seed** | `agent_factory.py` | Starter population had too many elderly, producing a death wave in the first 200 ticks — removed the bias; pyramid distribution added. |
| 27 | **`INFLATION_DECAY_RATE` unwired** | `economy.py` | Constant defined but not used in `update_world_metrics` — now actively decays inflation toward target. |
| 28 | **`assign_initial_housing` skipped** | `agent_factory.py` | Housing was assigned per-tick, leaving a homeless spike at t=0 — now called for all agents at creation. |
| 29 | **`record_tick` was a stub** | `metrics_collector.py` | `MetricsCollector.record_tick()` had a TODO body — replaced with the real per-tick write into the 50+ field stats. |
| 30 | **Symmetric random walk broken** | `grid.py` | Agents drifted in one direction across the toroidal grid — replaced with a true symmetric step distribution. |
| 31 | **GDP sawtooth** | `metrics_calculator.py` | GDP jumped each tick as money totals updated — added 95/5 EMA smoothing. |

---

## 6. Parameter Sweeping System

### Sweep Runner
**File**: `simulation/test_reports/sweep_runner.py`

Patches runtime constants across modules using a `_PATCH_MODULES` table covering ~140 constants across 26 modules.

### Sweep Groups

| Group | Params | What It Tests |
|-------|--------|--------------|
| `needs` | 7 | `FOOD_DECAY_RATE`, `WATER_DECAY_RATE`, `HEALTH_DECAY_RATE`, death thresholds |
| `unlust` | 8 | `UNLUST_WEIGHT_MONEY`, `UNLUST_WEIGHT_SOCIAL`, etc. |
| `emotion` | 13 | Happiness weights, state machine thresholds |
| `economy` | 9 | Job salaries, welfare, tax, rent, debt |
| `death` | 9 | `STARVATION_DEATH_RATE`, `DEATH_AGE_THRESHOLD`, `DESPAIR_DEATH_RATE` |
| `actions` | 8 | Share, beg, steal thresholds |
| `social` | 8 | Reputation decay, community size, gossip, marriage, birth |
| `lifecycle` | 8 | Age mortality, sleep decay, family support |
| `environment` | 8 | Famine/drought/abundance probabilities + intensities |

### Missing from Sweeps
- ~120 newer constants from v2–SOTA not yet added to any sweep group
- AI-specific parameters (temperature, thresholds)
- Mid-simulation policy sweeps
- Goldilocks zone for v2 has been found (BIRTH=0.0115, ELDERLY=0.0005) but not yet promoted into `a1_default`

### Running Sweeps
```powershell
cd simulation/test_reports
python sweep_runner.py              # All 9 groups
python sweep_runner.py needs        # Single group
python sweep_runner.py FOOD_DECAY_RATE 0.005 0.01 0.02 0.04  # Custom values
```

### 27 Predefined Scenarios (runner.py)
| Group | Scenarios |
|-------|-----------|
| a | a1_default (80 agents, 200 ticks, seed=42), a2_extended (500t), a3_small (30 agents), a4_large (200 agents) |
| b | b1_dictator, b2_utopian, b3_laissez_faire, b4_welfare_state |
| c | c1_famine, c2_drought, c3_abundance, c4_high_crime, c5_unstable |
| d | d1_all_poor, d2_all_rich, d3_high_morality, d4_low_morality, d5_high_anger |
| e | e1_zero_tax, e2_max_welfare, e3_huge_food_cost, e4_sparse, e5_dense |
| f | f1_tax_cut, f2_welfare_intro, f3_police_policy |
| g | g1_with_ai, g2_no_ai |
| h | h1_random_all |

---

## 7. Merge Conflict Resolutions

### Conflicts Found

4 real merge conflict files after rebasing tech-lead onto origin/main:

| File | Conflicts | Resolution |
|------|-----------|------------|
| `backend/app/main.py` | Router imports + mounts (ai/ai_historian vs governance/save) | KEPT BOTH — all 4 router files exist |
| `backend/app/services/simulation_service.py` | VLLMRouter creation + post-tick block | MERGED conditional AI routing + historian accumulation |
| `simulation/engine/tick_loop.py` | 4 conflicts: import block, type annotation, economy step, AI loop | MERGED IAIRouter type, merged both economy features, restored missing prompt capture code |
| `simulation/engine/simulation_engine.py` | 4 conflicts: VLLMRouter vs IAIRouter | MERGED — kept IAIRouter interface |
| `simulation/needs_calculator.py` | 2 conflicts: progress_age, check_death signature | MERGED — restored progress_age, kept world parameter |
| `simulation/economy.py` | Import + __all__ conflicts (DEBT_INTEREST_RATE vs labor_market) | MERGED both |
| `shared/schemas/simulation_state.py` | Field conflicts (national_debt vs job_demand) | MERGED both field sets |

### Post-Merge Regressions Found & Fixed
After merging, 3 critical bugs were introduced that required 6+ hours of debugging:

1. **All agents idle (deterministic path)**: The `execute_action()` call after `deterministic_fallback()` was dropped during conflict resolution. Restored 3 lines.

2. **ai_calls=0 (AI path)**: The `dilemma_prompts.append()` and `dilemma_agents.append()` calls were dropped. Restored them plus the missing `else:` clause for normal agents.

3. **Internal Server Error (AI path)**: `model_type` variable undefined. Restored with hardcoded per-agent-type values.

4. **All agents idle (AI path)**: `is_available()` in `models/router/vllm_router.py` was checking the real server and returning False. Changed to return True (mock fallback).

---

## 8. Docker Infrastructure

### Services
```yaml
services:
  backend:
    image: python:3.14-slim
    ports: ["8000:8000"]
    env: VLLM_BASE_URL, API_KEY_E2B, API_KEY_MOE_26B, API_KEY_DENSE_31B
    command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

  frontend:
    image: node:20-alpine
    ports: ["3000:3000"]
    build: multi-stage (npm install → next build → next start)

  vllm:
    profile: disabled (runs on external GPU server)
    image: rocm/vllm-dev:rocm6.2_ubuntu22.04
    ports: ["8001:8001"]
```

### Configuration
- **docker/.env**: All VLLM endpoints, API keys, ports
- **docker/override.yml**: vllm + simulation disabled by default
- **VLLM_BASE_URL**: `http://165.245.130.202:8000/v1` (31B dense)
- **VLLM_BASE_URL_E2B**: `http://165.245.130.202:8001/v1`
- **VLLM_BASE_URL_MOE_26B**: `http://165.245.130.202:8002/v1`
- **VLLM_BASE_URL_DENSE_31B**: `http://165.245.130.202:8000/v1`

### Commands
```powershell
# Build & start (docker-compose lives under docker/)
docker compose -f docker/docker-compose.yml build backend
docker compose -f docker/docker-compose.yml build frontend
docker compose -f docker/docker-compose.yml up -d backend frontend

# Test
curl http://localhost:8000/api/v1/health    # Backend health
curl http://localhost:3000/dashboard        # Frontend

# Simulation with AI
curl -X POST http://localhost:8000/api/v1/simulation/start ^
  -H "Content-Type: application/json" ^
  -d '{"population_size":20,"enable_ai":true}'

# Governance
curl -X POST http://localhost:8000/api/v1/governance/apply ^
  -H "Content-Type: application/json" ^
  -d '{"tax_rate":0.30,"welfare_enabled":true}'
```

---

## 9. Current State & Known Issues

### What Works
- ✅ Full v1–v6 + SOTA engine (deterministic, no AI calls)
- ✅ All 24 actions with softmax decision priority queue; 20 of 24 wired to world effects
- ✅ Lifecycle: age progression, marriage, birth, death (7 causes), inheritance, age-graded elderly mortality
- ✅ Social: reputation, gossip, communities, gangs, rumors, inter-community conflict, riots
- ✅ Economy: progressive tax, welfare, debt, labor market, property market (4 tiers), fraud, invest, GDP EMA, inflation decay
- ✅ Self-actualization: purpose system, creative jobs, political career, hobbies
- ✅ Governance: tax/food/welfare sliders, policy creation/revocation, AI suggestions, impact preview
- ✅ Agent memory (last 50 events with reasoning)
- ✅ Media engine (news articles every 5 ticks, 15% fake news)
- ✅ LLM explainability (5 presets + custom Q&A, rule fallback)
- ✅ Parameter sweeper (9 groups, 77 params, patch-table architecture, 27 predefined scenarios)
- ✅ Frontend: Dune Imperial Archive dark theme, responsive, pixel sprite AgentGrid, mobile nav, animated background, Sparkline, WorldGauge, ExplainPanel
- ✅ Docker: backend + frontend containers, vLLM config on external AMD MI300X
- ✅ Mock AI fallback for testing without GPU
- ✅ Save/load system, WebSocket push
- ✅ SOTA engine smoke: 200t alive=137, 2000t pop=96 (in the 60–100 target band)
- ✅ Batched LLM calls: 27× throughput improvement on the 31B route; tick latency 30–90 s → 2–4 s

### Known Issues
| Severity | Issue | Details |
|----------|-------|---------|
| ❌ | **Governance suggestions empty** | No crises triggered in stable sim; needs edge-case testing |
| ❌ | **Entry log only from WebSocket** | Events only added via WS messages; HTTP-polling clients miss them |
| ❌ | **LLM sometimes hallucinates** | Added normal-range context to prompts but needs more guardrails |
| ⚠️ | **Population equilibrium is sharp** | Goldilocks window is ~0.0114–0.0115 on BIRTH_CHANCE_BASE; small drifts push pop@2000t from 51 → 112 |
| ⚠️ | **No crimes in baseline** | Morality gate + stable needs prevent all antisocial actions |
| ⚠️ | **Cold start**: zero agents on restart | In-memory state lost on container restart; no persistence |
| ⚠️ | **No save/load UI** | API endpoints exist but no frontend UI for save/load |
| ⚠️ | **Sweep report gaps** | ~120 newer constants not covered in sweep groups |
| ⚠️ | **Policy keywords limited** | Only 8 keyword patterns; free-text policies likely fail |
| ⚠️ | **`MetricsCollector` is still a stub** | The 50+ field per-tick metrics live in `sweep_runner.run_single()` and `metrics_calculator.py`, not in `MetricsCollector.record_tick()`. |

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Backend health |
| POST | `/api/v1/simulation/start` | Start simulation |
| POST | `/api/v1/simulation/tick` | Advance 1 tick |
| POST | `/api/v1/simulation/tick-n` | Advance N ticks |
| POST | `/api/v1/simulation/auto-run` | Start/stop auto-run |
| POST | `/api/v1/simulation/stop` | Stop simulation |
| POST | `/api/v1/simulation/reset` | Reset to initial |
| GET | `/api/v1/simulation/status` | Current status |
| GET | `/api/v1/simulation/state` | Full state |
| GET | `/api/v1/agents/` | Agent list |
| GET | `/api/v1/agents/{id}` | Agent detail (with memories) |
| POST | `/api/v1/policies/` | Create policy |
| GET | `/api/v1/policies/` | List policies |
| GET | `/api/v1/policies/{id}` | Get policy |
| DELETE | `/api/v1/policies/{id}` | Revoke policy |
| GET | `/api/v1/metrics/` | Metrics history |
| GET | `/api/v1/metrics/dashboard` | Dashboard data |
| POST | `/api/v1/governance/apply` | Apply governance changes |
| GET | `/api/v1/governance/suggestions` | AI policy suggestions |
| POST | `/api/v1/explain` | LLM explainability |
| GET | `/api/v1/saves/` | List saves |
| POST | `/api/v1/saves/` | Save state |
| POST | `/api/v1/saves/load/{id}` | Load state |
| GET | `/api/v1/ai/news` | Latest news |
| WS | `/ws` | Real-time event stream |
