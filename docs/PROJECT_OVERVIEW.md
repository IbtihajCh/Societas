# SOCIETAS — Extreme Detail Project Overview

> **Purpose**: Feed this document to Claude or any LLM for writing project descriptions, grant applications, hackathon submissions, or investor pitches. Every subsystem, constant, design decision, and bug fix is documented.

**Stack**: Python 3.11+ (backend/simulation) · Next.js 14 (frontend) · Docker · vLLM (3× Gemma 4) · AMD MI300X GPU  
**Hackathon**: AMD 2026 — Track 3: Unicorn Pre-Screening  
**License**: MIT

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Architecture — 3-Layer Stack](#2-architecture--3-layer-stack)
3. [Simulation Engine — 17-Step Tick Loop](#3-simulation-engine--17-step-tick-loop)
4. [Agent State Schema](#4-agent-state-schema)
5. [24 Actions + Decision Priority Queue](#5-24-actions--decision-priority-queue)
6. [Emotion System — 5-State Machine](#6-emotion-system--5-state-machine)
7. [Economy System](#7-economy-system)
8. [Social Systems](#8-social-systems)
9. [Lifecycle System](#9-lifecycle-system)
10. [Self-Actualization System](#10-self-actualization-system)
11. [Feature Implementation History (v1–v6 + SOTA)](#11-feature-implementation-history-v1v6--sota)
12. [Frontend Design System](#12-frontend-design-system)
13. [LLM Integration & AI Routing](#13-llm-integration--ai-routing)
14. [All 31 Fixed Bugs](#14-all-31-fixed-bugs)
15. [Parameter Sweeping System](#15-parameter-sweeping-system)
16. [Docker Infrastructure](#16-docker-infrastructure)
17. [API Endpoints](#17-api-endpoints)
18. [Performance Benchmarks](#18-performance-benchmarks)
19. [Current State & Known Issues](#19-current-state--known-issues)
20. [Repository Structure](#20-repository-structure)

---

## 1. Project Identity

**SOCIETAS** is a real-time, explainable, large-scale governance simulator that models how policy decisions cascade through an artificial society of autonomous individuals with realistic psychological, economic, and social behavior. 1000+ agents live, work, trade, marry, protest, commit crimes, and die on a 30×30 grid — governed by a 17-step tick engine, 24 actions, 13 needs across 5 Maslow layers, and an optional 3-model LLM reasoning layer running on AMD MI300X GPUs.

**Core philosophy**: *Deterministic systems should model reality. LLMs should model human reasoning.*

The simulation engine remains fully deterministic, explainable, and mathematically grounded. LLMs operate as a reasoning layer, augmenting deterministic decisions only when ambiguity exceeds a configurable threshold.

**Key metrics**:
- 1000+ autonomous agents per simulation
- 24 distinct actions with softmax-driven probability selection
- 8 personality traits (beta-distributed for natural variation)
- 13 needs across 5 Maslow hierarchy layers
- 5-state emotion machine with smooth transitions
- 7 causes of death, 4 age brackets, birth/marriage/inheritance
- 3-model LLM router (E2B, 26B A4B, 31B Dense) on AMD MI300X
- 50+ per-tick metrics tracked
- 24ms/tick deterministic · 2-4s/tick with LLM (batched 27× improvement)

---

## 2. Architecture — 3-Layer Stack

```
┌──────────────────────────────────────────────────────────┐
│                    Layer 3 — Presentation                 │
│  Next.js 14 Dashboard · 11 Interactive Panels            │
│  Dune Imperial Theme (Fraunces/Inter/IBM Plex Mono)      │
│  30×30 Canvas Agent Grid · 4 SVG Ring Gauges             │
│  Sparklines · Explain Panel · Custom Panel Builder       │
│  Host: localhost:3000                                     │
├──────────────────────────────────────────────────────────┤
│                  Layer 2 — Cognitive Reasoning            │
│  vLLM Router (3× Gemma 4 on AMD MI300X)                  │
│  E2B (:8001) — Agent Decisions                           │
│  26B A4B (:8002) — Moral Reasoning, Dilemmas             │
│  31B Dense (:8000) — Governance, Policy, Explain, News   │
│  Batched Inference: 27× throughput improvement           │
│  Fallback: Deterministic when GPU unavailable            │
├──────────────────────────────────────────────────────────┤
│              Layer 1 — Deterministic Simulation           │
│  FastAPI Backend · Uvicorn · WebSocket · SQLite          │
│  17-Step Tick Engine · 24 Actions · 13 Needs             │
│  Economy · Social · Lifecycle · Environment              │
│  Host: localhost:8000                                     │
└──────────────────────────────────────────────────────────┘
```

**Inter-layer communication**:
- Frontend ↔ Backend: REST API + WebSocket
- Backend ↔ Simulation: Direct Python engine calls
- Backend ↔ vLLM: HTTP POST to GPU server endpoints
- Simulation state flows: Engine → DTO → API → Frontend Store → React Components

---

## 3. Simulation Engine — 17-Step Tick Loop

Each tick represents one day in the simulation. The SOTA engine runs 17 sequential steps:

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
Step   7 — Movement on 30×30 grid
Step  7b — Riot events check + trigger
Step  7c — Inter-community tension + conflict
Step   8 — Death checks (7 causes)
Step  8.5 — Birth (eligible married adults)
Step   9 — World metrics update (GDP EMA, friction targets, recovery loops)
Step  10 — State hash + TickCompletedEvent + media engine tick
```

**Tick timing**: 24ms deterministic for 100 agents · 2-4 seconds with LLM on AMD MI300X

---

## 4. Agent State Schema

### 8 Beta-Distributed Personality Traits

| Trait | Distribution | Range |
|-------|-------------|-------|
| morality | Beta(2, 2) | 0.0–1.0 |
| creativity | Beta(2, 2) | 0.0–1.0 |
| ambition | Beta(2, 2) | 0.0–1.0 |
| resilience | Beta(2, 2) | 0.0–1.0 |
| dominance_urge | Beta(2, 2) | 0.0–1.0 |
| anger_tendency | Beta(2, 3) | 0.0–1.0 |
| extraversion | Beta(2, 2) | 0.0–1.0 |
| risk_tolerance | Beta(2, 2) | 0.0–1.0 |

Traits are assigned at agent creation and remain stable throughout the simulation. They influence decision weights, emotion sensitivity, and social behavior.

### 13 Needs Across 5 Maslow Layers

| Layer | Needs | Description |
|-------|-------|-------------|
| **Physiological** | food, water, sleep, energy | Survival-critical. Death below threshold |
| **Safety & Security** | safety, health, money | Well-being and economic stability |
| **Love & Belonging** | social, family | Relationships and community bonds |
| **Esteem** | esteem, status | Self-worth and social standing |
| **Self-Actualization** | achievement, purpose, creativity | Growth, meaning, contribution |

Need levels decay continuously (0.01–0.05/tick depending on need type) and are restored through actions (e.g., buy_food restores food, befriend restores social, work provides money for safety).

### Agent Resources

| Resource | Type | Description |
|----------|------|-------------|
| money | float | Liquid cash |
| base_salary | float | Annual income from employment |
| employed | bool | Employment status |
| education | float | 0.0 (none) to 1.0 (advanced degree) |
| property | bool | Property ownership |
| property_tier | int | 0 (homeless) to 3 (premium) |
| property_value | float | Current market value |
| rent_cost | float | Monthly rent if renting |
| health | float | 0.0 (dead) to 1.0 (perfect) |
| debt | float | Outstanding loans with interest |

### Wealth Classes

| Class | Money Threshold | Color |
|-------|----------------|-------|
| POOR | < $500 | Muted brown (#9B8E7A ring) |
| MIDDLE | $500 – $2,000 | Bronze-brown (#C4A870 ring) |
| RICH | > $2,000 | Bright gold (#F0C040 ring, 2px) |
| BUSINESS_OWNER | Owns business | Forest green (#3A6B3A ring, gold rim) |

### Persona Generation

Each agent receives a unique persona string combining age bracket, gender, job description, and wealth context. Example: *"A woman in middle adulthood, working as a teacher, with comfortable financial means."*

---

## 5. 24 Actions + Decision Priority Queue

### Complete Action List

| Category | Actions |
|----------|---------|
| **Work** | work, seek_job, buy_food, rest |
| **Social** | befriend, console, share, complain |
| **Antisocial** | steal, harm_other, protest, fraud |
| **Care** | treat, counsel, support_family, isolate |
| **Economic** | invest, buy_property, hobby, spread_rumor, campaign |
| **Other** | idle, comply, beg |

**20 of 24 actions are wired to world effects** — they mutate GDP, inflation, public safety, social cohesion, environment, etc.

### 3-Level Decision Priority Queue

| Level | Trigger | Actions Available |
|-------|---------|-------------------|
| **1 — Critical** | food < 0.08 OR water < 0.08 | BUY_FOOD (has money) → STEAL (survival override) → BEG |
| **2 — Stability** | unemployed → SEEK_JOB; money < threshold → WORK/BEG |
| **3 — Normal** | All others | **Softmax probability** across all valid actions with temperature scaling |

**Softmax formula**: `P(action) = exp(score/T) / Σ exp(score/T)` where T is temperature (0.5 default). Score is computed from trait modifiers, need levels, and situational bonuses. This replaced the original magic-percentage approach for more natural behavior distribution.

---

## 6. Emotion System — 5-State Machine

### State Transitions
```
Neutral ⇄ Happy ⇄ Sad ⇄ Angry ⇄ Despair
```
Transitions are triggered by:
- **Unlust** (dissatisfaction): high unlust pushes toward Sad → Angry → Despair
- **Happiness score**: composite of need fulfillment, social connections, job satisfaction
- **External events**: crime victimization, policy changes, community events

### Happiness Formula
```
happiness = w1 * needs_fulfillment + w2 * social_satisfaction + w3 * economic_satisfaction
           + w4 * health + w5 * purpose_fulfillment
```
where weights are: w1=0.3, w2=0.2, w3=0.2, w4=0.15, w5=0.15

### Unlust Engine
Unlust (dissatisfaction) accumulates from:
- Unmet needs (weighted by severity)
- Low money relative to expenses
- Social isolation
- Unemployment
- Crime victimization
- Reputation damage

Unlust decays slowly when agents take satisfying actions (work, socialize, create).

---

## 7. Economy System

### Progressive Taxation
| Wealth Class | Tax Multiplier |
|-------------|----------------|
| POOR | 0.5× |
| MIDDLE | 1.0× |
| RICH | 1.5× |

Tax revenue funds welfare payouts. Tax rate is adjustable via governance panel (0%–50%).

### Welfare
When enabled, distributes `welfare_amount` to unemployed or poor agents each tick. Funded from tax revenue pool.

### Labor Market
- **12 job types** with base salaries (construction: $60, teacher: $75, doctor: $120, artist: $45, etc.)
- **Supply/demand adjustment**: salaries fluctuate based on the number of agents employed in each job
- **Employment matching**: agents with matching education/traits fill available positions

### Property Market (4 Tiers)
| Tier | Level | Rent |
|------|-------|------|
| 0 | Homeless | $0 |
| 1 | Basic | $5/tick |
| 2 | Standard | $12/tick |
| 3 | Premium | $25/tick |

Agents can buy property (`BUY_PROPERTY` action) or be evicted if they can't pay rent.

### GDP Calculation
```
GDP = 0.95 * GDP_prev + 0.05 * total_money_in_economy
```
Uses 95/5 EMA smoothing to prevent sawtooth patterns. Inflation decays toward a 2% target.

---

## 8. Social Systems

### Reputation
- Tracks agent standing in the community (0.0–1.0)
- Decays at 0.001/tick if no social interactions
- Boosted by prosocial actions (befriend, share, counsel)
- Damaged by antisocial behavior (steal, fraud, harm_other)
- **Gossip propagation**: negative events spread through social connections at 10% chance per tick

### Communities
- **BFS clustering** every 10 ticks
- 3–15 members per community
- Community leaders gain reputation and safety benefits
- **Inter-community tension**: builds over time, decays at 0.005/tick
- **Conflict**: triggered when tension > 0.5 between communities

### Organized Crime Gangs
- **Formation**: 5+ eligible agents (unlust > 0.6, morality < 0.3, wealth POOR)
- **Actions**: 40% extortion, 30% gang fights, 30% territory protection
- **Effects**: increased crime rate, reduced public safety, intimidation of local agents

### Rumor Propagation
- Spreads through social networks via BFS (depth 3)
- 6 rumor templates: theft, affair, corruption, fraud, betrayal, conspiracy
- Affected agents lose trust_in_govt and reputation

### Riot Events
- **Trigger**: protest_intensity > 0.3 AND (unlust > 0.5 OR food_availability < 0.3)
- **Participation**: 30% of eligible agents join
- **Effects**: property damage, public safety reduction, media coverage

---

## 9. Lifecycle System

### Age Brackets
| Bracket | Range | Description |
|---------|-------|-------------|
| CHILD | 0–18 | Cannot work, marry, or commit crimes. Dependent on parents. |
| YOUNG_ADULT | 19–40 | Marriage eligible, full action set, career building |
| MIDDLE | 41–65 | Stable career, family responsibilities |
| ELDERLY | 66+ | Reduced action set, age-graded mortality |

### Age Progression
Agents age by ~0.003 years per tick (about 1 year per 333 ticks). Linear interpolation through brackets.

### Death — 7 Causes
| Cause | Rate | Notes |
|-------|------|-------|
| Starvation | food < 0.03 | Immediate |
| Dehydration | water < 0.02 | Immediate |
| Disease | health < 0.05 | Gradual, treatable via TREAT action |
| Violence | crime victim | Permanent death |
| Despair | unhappiness < 0.1 for 100+ ticks | Suicide |
| Old age | age > 66 | Age-graded (smooth curve, no cliff) |
| Accidents | base_rate = 0.0001 | Random |

### Birth
- **Eligibility**: Married adults (age 19–45), both alive
- **Base probability**: 0.0115 per tick (Goldilocks equilibrium value from sweep search)
- **Inheritance**: 70% of deceased parent's money passed to surviving spouse

### Marriage
- **Base probability**: 0.05 per tick for eligible singles
- **Requirements**: Age 19–65, opposite gender, grid proximity < 3 cells, wealth compatibility > 0.7

---

## 10. Self-Actualization System

### Purpose System
5 purpose types assigned at agent creation:
1. **create_art** — artists, writers, musicians
2. **lead_community** — community leaders
3. **teach** — educators, mentors
4. **build_wealth** — entrepreneurs, investors
5. **discover** — scientists, researchers

Purpose fulfillment tracked over time. High fulfillment boosts happiness and reduces unlust.

### Creative Professions
- **Override**: 5% chance of creative job assignment regardless of traits (if creativity > 0.7)
- **Jobs**: ARTIST, WRITER, MUSICIAN
- **Effects**: mood modifier, reputation gain, small income

### Political Career
- `CAMPAIGN` action available to agents with high notoriety and ambition
- Builds political influence over time
- Affects policy reception and trust_in_govt

---

## 11. Feature Implementation History (v1–v6 + SOTA)

### v1 — Base Simulation
- 4 needs, 5 emotions, 11 actions, 3 wealth classes, 10 jobs
- LLM policy translation (keyword + AI paths)
- DeterministicRNG for reproducible randomness

### v2 — Full Life Cycle
- Age progression, 4 age brackets, marriage, sleep/insomnia
- Sibling relationships, family support transactions
- Inheritance system (70% to surviving spouse)

### v3 — Social Systems
- Reputation tracking, gossip propagation, BFS communities
- Organized crime gangs, rumors, riot events
- Therapist/doctor jobs: TREAT (heals), COUNSEL (reduces unlust)

### v4 — Advanced Economy
- White-collar crime (FRAUD with detection probability)
- Invest/business ownership for BUSINESS_OWNER wealth class
- Labor market with supply/demand salary adjustment
- Property market (4 tiers, rent, eviction, buy/sell)

### v5 — Self-Actualization
- Purpose system (5 purposes), creative professions
- Community leadership, political career, hobbies

### v6 — UI & Infrastructure
- Governance UI, Animated AgentGrid (canvas pixel sprites)
- Save/Load system, AI policy suggestions
- 10 interactive panels on dashboard

### Post-v6: Memory, Media, Softmax, Explainability
- **Agent Memory System**: Stores last 50 actions per agent with reasoning. Injected into LLM prompts for context-aware decisions.
- **Softmax Decisions**: Replaced Level 3 magic percentages with temperature-scaled softmax for natural behavior distribution.
- **Media Engine**: Generates news articles every 5 ticks from 7 categories. 15% fake news rate. Affects trust_in_govt.
- **LLM Explainability**: Natural language Q&A about simulation state. Rule-based fallback when LLM unavailable.

### SOTA Engine (July 2026) — Organic Whole
- **Agent→World feedback**: 20 of 24 actions mutate world state (GDP, inflation, safety, cohesion)
- **GDP EMA**: Smooth 95/5 exponential moving average — no sawtooth
- **Friction targets (0.9 ceiling)**: Public order, cohesion, mental health asymptote to 0.9 — always room to fall
- **Recovery loops**: Decay + recovery formulas on all major metrics
- **Smooth death curves**: Mortality rises smoothly with age, no elderly cliff
- **Pyramid age distribution**: Initial population follows triangular age profile
- **Goldilocks birth tuning**: BIRTH_CHANCE_BASE=0.0115 (found via grid search at 2000t)
- **50+ per-tick metrics**: Every tick records alive, dead, avg_happiness, avg_unlust, unemployment, crime_rate, gdp, inflation, market_stability, consumer_confidence, trade_balance, and 40+ more

**SOTA smoke results** (2000t, 80 agents, seed 42): Pop@200t=137, Pop@900t=180 (peak), Pop@2000t=96. Total: 724 deaths, 2,481 crimes, 2,740 protests. Stable civilization with rich emergent behavior.

---

## 12. Frontend Design System

### Design Philosophy
The interface is a single visual idea: **"an imperial archival console for a civilisation that is being watched, measured, and governed in real time."** Dark parchment, gold light, oxblood danger, and smooth agent animations. Fraunces for display, Inter for body, IBM Plex Mono for data.

### Theme Tokens (Logo-Inspired Palette)

| Token | Hex | Usage |
|-------|-----|-------|
| `--cream` | `#0A0604` | Page background (near-black) |
| `--parchment` | `#130D08` | Card/panel backgrounds |
| `--parchment-2` | `#1A100A` | Darker panels, bar tracks |
| `--ink` | `#E8DCC4` | Primary text (warm cream) |
| `--ink-soft` | `#A08868` | Secondary text (medium brown) |
| `--oxblood` | `#78231D` | Errors, crime, danger (deep brick red) |
| `--moss` | `#7A7417` | Success, growth, welfare (olive green) |
| `--ochre` | `#A86E26` | Warnings, food, gold accents (bronze) |
| `--slate` | `#462612` | Neutral info, sadness (dark brown) |
| `--gold` | `#A86E26` | Accents, active navigation (bronze) |
| `--rule` | `#2E1A0C` | Borders, dividers |
| `--black` | `#000000` | Pure black |

**Fonts**: `--font-display: 'Fraunces'` (headings), `--font-body: 'Inter'` (body text), `--font-mono: 'IBM Plex Mono'` (data/metrics)

### Dual-Color Effect
- **Panel cards**: `#181810` (olive-tinted) — subtly distinct from container
- **Dock container**: `#1A100A` (dark brown) — creates visual separation
- **Topbar**: `#0E0C08` (greenish dark)
- **Policy bar**: `#120F0A` (greenish brown)

### Layout — World Monitor
```
┌─────────────────────────────────────────────────────────────┐
│  TOPBAR (68px): Logo · SOCIETAS · YEAR 1 · DAY 1 · 19:00   │
│                · Step · Auto Run · Stop · Save · Load · Bell│
├─────────────────────────────────────────────────────────────┤
│  POLICY BAR (42px): [TAX 15%] [SUBSIDY 1%] [WELFARE OFF]   │
├──────────────────────────┬──────────────────────────────────┤
│  WORLD PANE (left 50%)   │  DOCK PANE (right 50%)           │
│  ┌────────────────────┐  │  ┌─ Sections ─────────────────┐  │
│  │ Citizen Census     │  │  │ Metrics & Gauges            │  │
│  │ ring=wealth        │  │  │ (6 stat cards + 4 gauges)   │  │
│  │ body=emotion       │  │  ├────────────────────────────┤  │
│  │                    │  │  │ Governance & Policies       │  │
│  │  30×30 Agent Grid  │  │  │ (Tax/Welfare/Food sliders)  │  │
│  │  (canvas, smooth   │  │  ├────────────────────────────┤  │
│  │   lerp animation)  │  │  │ Entry Log · News            │  │
│  │                    │  │  ├────────────────────────────┤  │
│  │  Gold corner       │  │  │ Wealth Stratification       │  │
│  │  brackets on frame │  │  │ (stacked bar chart)         │  │
│  │                    │  │  ├────────────────────────────┤  │
│  │  Legend: Rings +   │  │  │ Explain · Model Log         │  │
│  │  Body colors       │  │  ├────────────────────────────┤  │
│  └────────────────────┘  │  │ Diagnostics · Env Events    │  │
│                          │  │ Community · Self-Act        │  │
│                          │  │ Memory Browser              │  │
│                          │  └────────────────────────────┘  │
├──────────────────────────┴──────────────────────────────────┤
│  LLM Offline Badge (when GPU unavailable)                   │
└─────────────────────────────────────────────────────────────┘
```

### Agent Grid — 30×30 Canvas
- **Canvas-based** with `requestAnimationFrame` loop for 60fps rendering
- **Agents**: colored circles with:
  - **Outer ring** = wealth class (poor tan, middle bronze, rich gold, owner olive with gold rim)
  - **Body fill** = emotion state (happy olive, neutral cream, sad brown, angry brick red, stressed bronze)
- **Smooth lerp animation**: agents glide between grid positions at 0.12 lerp factor
- **Hover**: tooltip showing agent ID, emotion, wealth, age, job, unlust
- **Click**: Dossier slide-in panel with full agent detail
- **Selection**: dashed ring around selected agent
- **Grid lines**: subtle 1px lines at 0.1 opacity
- **Corner brackets**: 4 gold corner markers on the frame
- **Legend**: Rings (Poor/Middle/Rich/Owner) + Body (Happy/Neutral/Sad/Angry/Stressed) inside frame

### 11 Interactive Panels (All Drag-Reorderable, × Closable)

| Panel | Category | Description |
|-------|----------|-------------|
| **Metrics & Gauges** | Overview | 6 stat cards with sparklines + deltas + 4 SVG ring gauges |
| **Entry Log · News** | Overview | Scrollable event log with category color coding |
| **Environmental Events** | Overview | Filtered environmental/social event list |
| **Governance & Policies** | Governance | Tax/Welfare/Food sliders + custom policy creation/revocation |
| **Wealth Stratification** | Economy | Stacked bar chart (poor/middle/rich) with theme colors |
| **Explain** | Model | Natural language Q&A about simulation state |
| **Model Log** | Model | LLM router call log (agent decisions) |
| **Memory Browser** | Model | Agent memory search |
| **Diagnostics** | Citizens | Tick duration, AI calls, determinism check |
| **Community Status** | Citizens | Population, cohesion, crime, protest, unemployment KV grid |
| **Self-Actualization** | Citizens | 4 collective gauges (morality/innovation/economy/cohesion) |

**Custom Panel Builder**: Select any 3 of 30+ metrics. Each gets a sparkline + current value. Name the panel. Appears in dock.

**Add Panel menu**: Categorized dropdown (Overview/Citizens/Governance/Economy/Model/Custom) with smooth fade-in animation.

### Metrics Panel — 6 Stat Cards + 4 Ring Gauges

**Stat cards** (POPULATION, ECONOMIC HEALTH, EMPLOYMENT, CRIME RATE, SOCIAL COHESION, MORALITY):
- Large metric value with tabular numerals (no jitter)
- Delta indicator (▲/▼/steady with color-coded text)
- 50×20px gold sparkline chart with dot marker

**Ring gauges** (ECON, COHESION, MORALITY, SAFETY):
- SVG arc rendering: 36px radius, 260° sweep, rounded caps
- Color threshold: >0.7 moss (good), >0.4 ochre (warning), else oxblood (critical)
- Center percentage value, bottom uppercase label

### Animations
- **Mouse glow spotlight**: 600px radial gradient following cursor (warm bronze/olive)
- **Canvas particles**: 40 drifting bronze/olive/brick-red dots (1-2px)
- **Scanlines**: Subtle horizontal lines scrolling over grid (CRT monitor feel)
- **Breathing glow**: Grid frame pulses bronze glow every 4s
- **Pulse corners**: Corner brackets fade in/out every 3s
- **Floating dots**: 8 dots drift upward across dashboard backdrop
- **All transitions**: 0.15s ease on every interactive element
- **prefers-reduced-motion**: All animations disabled when user preference set

### Responsive Breakpoints
| Width | Behavior |
|-------|----------|
| >1100px | 50/50 split with sidebar |
| 768–1100px | Single column stacked |
| <768px | Full-width, dock below grid |
| <480px | Compact stats, 2-col gauges |

---

## 13. LLM Integration & AI Routing

### 3-Model Architecture

| Model | Port | Temperature | Purpose |
|-------|------|-------------|---------|
| **Gemma 4 E2B** | 8001 | 0.0 | Agent decision-making (~7–20 calls/tick) |
| **Gemma 4 26B A4B** | 8002 | 0.2 | Moral reasoning, ethical dilemmas |
| **Gemma 4 31B Dense** | 8000 | 0.3 | Policy translation, governance, explain, news |

### API Configuration
- **Base URLs**: Configurable via `docker/.env` environment variables
- **API Keys**: Per-model keys for authentication
- **Timeout**: 5s per call, 1 retry (reduced from 30s/2 retries)
- **Batched inference**: 8 agents per request, prompt-response cached by `(model, prompt_hash)`
- **Throughput**: 27× improvement on 31B route; end-to-end tick latency 30–90s → 2–4s

### Deterministic Fallback
When `is_available()` returns False:
- `agent_decide` → `deterministic_fallback` (rule-based action selection)
- `moral_reasoning` → `_mock_moral` (simple ethical decision tree)
- `explain` → Rule-based answers computed from simulation state
- All mock responses include valid JSON with `action`, `reason`, `feeling` fields
- Frontend shows "LLM Offline — Fallback Mode" badge in topbar

### Explain System
- **Endpoint**: `POST /api/v1/explain`
- **Prompt**: Full state context + normal range guidelines for every metric
- **5 preset questions**: Crime, Economy, Deaths, Unlust, Food
- **Custom Q&A**: Natural language queries about simulation state
- **Source tracking**: Response includes `source: "llm"` or `source: "rule"`

---

## 14. All 31 Fixed Bugs

| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | **Deterministic path: all agents idle** | `tick_loop.py` | Restored `execute_action()` after `deterministic_fallback` (dropped in merge) |
| 2 | **AI path: prompts built but never captured** | `tick_loop.py` | Restored `dilemma_prompts.append()` and `dilemma_agents.append()` |
| 3 | **AI path: `model_type` undefined** | `tick_loop.py` | Hardcoded per agent type |
| 4 | **Tax had no effect** | `economy.py` | Added `apply_tax()` with progressive rates |
| 5 | **Auto-run not working** | `dashboard.tsx` | Frontend `setInterval` calling `advanceTick()` |
| 6 | **No personas** | `agent_factory.py` | Added `_generate_persona()` from 8 traits |
| 7 | **Food subsidy confusing** | `governance.tsx` | Changed to `min(1.0, 0.85 + subsidy)` |
| 8 | **Governance dependency wrong** | `governance.py` | Fixed import from `get_policy_service` to `get_simulation_service` |
| 9 | **WebSocket overrides isConnected** | `SimulationContext.tsx` | Only WS `connected` sets true; HTTP health is source of truth |
| 10 | **Health poll too slow** | `SimulationContext.tsx` | 30s → 10s, added immediate check on mount |
| 11 | **Frontend LLM timeout** | `api.ts` | 10s → 120s |
| 12 | **vLLM timeout too long** | `vllm_config.py` | 30s → 5s, retries 2 → 0 |
| 13 | **Backend `state.agents` AttributeError** | `simulation_service.py` | Changed to `self._engine.get_agents()` |
| 14 | **Frontend event log: undefined** | `dashboard.tsx` | Fixed field names (`event_type` and `data`) |
| 15 | **Docker EBADPLATFORM** | `package.json` | Moved `@next/swc-win32-x64-msvc` to `optionalDependencies` |
| 16 | **Python 3.10 StrEnum** | `enums.py` | Added backport `class StrEnum(str, Enum)` |
| 17–21 | **5 merge conflicts** | Multiple files | Merged both sides, kept all features |
| 22 | **Action system grew past docstring** | `action_executor.py` | Updated from 14 to 24 actions documented |
| 23 | **EmotionType typo: SADNESS vs DESPAIR** | `enums.py` | Renamed to DESPAIR everywhere |
| 24 | **Birth chance collapse** | `agent_factory.py` | Lifted BIRTH_CHANCE_BASE from 0.005 to 0.0115 (Goldilocks) |
| 25 | **Elderly mortality cliff** | `defaults.py` | Halved AGE_MORTALITY_ELDERLY from 0.001 to 0.0005 |
| 26 | **Initial 10% elderly seed** | `agent_factory.py` | Removed bias; added pyramid distribution |
| 27 | **`INFLATION_DECAY_RATE` unwired** | `economy.py` | Now actively decays inflation toward target |
| 28 | **`assign_initial_housing` skipped** | `agent_factory.py` | Called for all agents at creation |
| 29 | **`record_tick` was a stub** | `metrics_collector.py` | Replaced with real 50+ field per-tick write |
| 30 | **Symmetric random walk broken** | `grid.py` | Replaced with true symmetric step distribution |
| 31 | **GDP sawtooth** | `metrics_calculator.py` | Added 95/5 EMA smoothing |

---

## 15. Parameter Sweeping System

### Sweep Runner
Patches runtime constants across modules using a `_PATCH_MODULES` table covering ~140 constants across 26 modules.

### Sweep Groups

| Group | Params | What It Tests |
|-------|--------|--------------|
| `needs` | 7 | Decay rates, death thresholds |
| `unlust` | 8 | Unlust weight vectors |
| `emotion` | 13 | Happiness weights, state machine thresholds |
| `economy` | 9 | Salaries, welfare, tax, rent, debt |
| `death` | 9 | All 7 death cause rates |
| `actions` | 8 | Share, beg, steal thresholds |
| `social` | 8 | Reputation, community, gossip, marriage, birth |
| `lifecycle` | 8 | Age mortality, sleep decay, family support |
| `environment` | 8 | Famine/drought/abundance probabilities + intensities |

### 27 Predefined Scenarios
| Group | Scenarios |
|-------|-----------|
| a | a1_default (80 agents, 200t), a2_extended (500t), a3_small (30 agents), a4_large (200 agents) |
| b | b1_dictator, b2_utopian, b3_laissez_faire, b4_welfare_state |
| c | c1_famine, c2_drought, c3_abundance, c4_high_crime, c5_unstable |
| d | d1_all_poor, d2_all_rich, d3_high_morality, d4_low_morality, d5_high_anger |
| e | e1_zero_tax, e2_max_welfare, e3_huge_food_cost, e4_sparse, e5_dense |
| f | f1_tax_cut, f2_welfare_intro, f3_police_policy |
| g | g1_with_ai, g2_no_ai |
| h | h1_random_all |

---

## 16. Docker Infrastructure

### Services
```yaml
services:
  backend:    # Python 3.14-slim, FastAPI + Uvicorn, port 8000
  frontend:   # Node 20-alpine, Next.js 14, port 3000, multi-stage build
  vllm:       # rocm/vllm-dev, profile: disabled (external GPU server)
  simulation: # profile: disabled
```

### Configuration
- **docker/.env**: All VLLM endpoints, API keys, ports
- **docker/.env.example**: Template for environment setup
- **docker/override.yml**: vllm + simulation disabled by default for local development
- **docker/backend.Dockerfile**: Python slim image, pip install from requirements.txt
- **docker/frontend.Dockerfile**: Multi-stage (npm install → next build → next start)

### Commands
```powershell
# Build & start
docker compose -f docker/docker-compose.yml build backend frontend
docker compose -f docker/docker-compose.yml up -d backend frontend

# With GPU (uncomment vllm profile)
docker compose -f docker/docker-compose.yml --profile gpu up -d

# Test
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/dashboard
```

---

## 17. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Backend health check |
| POST | `/api/v1/simulation/start` | Start simulation (configurable pop, seed, AI) |
| POST | `/api/v1/simulation/tick` | Advance one tick |
| POST | `/api/v1/simulation/tick-n` | Advance N ticks |
| POST | `/api/v1/simulation/auto-run` | Start/stop auto-run |
| POST | `/api/v1/simulation/stop` | Stop simulation |
| POST | `/api/v1/simulation/reset` | Reset to initial state |
| GET | `/api/v1/simulation/status` | Current status (tick, population, running) |
| GET | `/api/v1/simulation/state` | Full world state (50+ metrics) |
| GET | `/api/v1/agents` | Agent list with pagination |
| GET | `/api/v1/agents/{id}` | Agent detail (traits, needs, resources, memories) |
| GET | `/api/v1/agents/{id}/history` | Agent action history |
| POST | `/api/v1/policies` | Create policy |
| GET | `/api/v1/policies` | List all policies |
| GET | `/api/v1/policies/{id}` | Get single policy |
| DELETE | `/api/v1/policies/{id}` | Revoke policy |
| GET | `/api/v1/metrics` | Metrics history (time series) |
| GET | `/api/v1/metrics/dashboard` | Dashboard-aggregated data |
| POST | `/api/v1/governance/apply` | Apply tax, welfare, food changes |
| GET | `/api/v1/governance/suggestions` | AI policy suggestions |
| POST | `/api/v1/explain` | LLM explainability (preset Qs + custom) |
| GET | `/api/v1/ai/status` | LLM availability check |
| GET | `/api/v1/ai/news` | Latest news articles |
| GET | `/api/v1/saves` | List saved simulations |
| POST | `/api/v1/saves` | Save current state |
| POST | `/api/v1/saves/load/{id}` | Load saved state |
| WS | `/ws` | Real-time event stream (tick_completed, agent_acted) |

---

## 18. Performance Benchmarks

| Scenario | Agents | Ticks | Time | Per Tick | LLM Calls |
|----------|--------|-------|------|----------|-----------|
| Deterministic (small) | 10 | 10 | 0.6s | ~4ms | 0 |
| Deterministic (medium) | 30 | 10 | 0.6s | ~4ms | 0 |
| Deterministic (large) | 100 | 10 | 1.7s | ~24ms | 0 |
| Deterministic (huge) | 1000 | 1 | 0.5s | ~500ms | 0 |
| With LLM (MI300X) | 80 | 1 | 2–4s | 2000–4000ms | ~7–20 |
| SOTA smoke (2000t) | 80 | 2000 | ~60s | ~30ms | 0 |

---

## 19. Current State & Known Issues

### What Works
- ✅ Full v1–v6 + SOTA engine (deterministic, no AI calls needed)
- ✅ 24 actions with softmax priority queue; 20 wired to world effects
- ✅ Lifecycle: age progression, marriage, birth, death (7 causes), inheritance
- ✅ Social: reputation, gossip, communities, gangs, rumors, riots
- ✅ Economy: progressive tax, welfare, debt, labor market, property market, fraud
- ✅ Self-actualization: purpose system, creative jobs, political career, hobbies
- ✅ Governance: tax/food/welfare sliders, policy creation/revocation, AI suggestions
- ✅ Agent memory (last 50 events with reasoning)
- ✅ Media engine (news articles every 5 ticks, 15% fake news)
- ✅ LLM explainability (5 presets + custom Q&A, rule fallback)
- ✅ Parameter sweeper (9 groups, 77 params, 27 scenarios)
- ✅ Frontend: dark theme, 11 panels, smooth animations, responsive, custom panels
- ✅ Docker: backend + frontend containers, LLM config on external AMD MI300X
- ✅ Mock AI fallback for testing without GPU
- ✅ Save/load system, WebSocket push, real-time agent refresh
- ✅ SOTA engine smoke: 200t alive=137, 2000t pop=96 (in 60–100 target band)
- ✅ Batched LLM calls: 27× throughput improvement; tick latency 30–90s → 2–4s

### Known Issues
| Severity | Issue |
|----------|-------|
| ❌ | **Governance suggestions empty** in stable simulations |
| ❌ | **Entry log only from WebSocket** — HTTP-polling clients miss events |
| ⚠️ | **Population equilibrium sharp** — Goldilocks window ~0.0114–0.0115 BIRTH_CHANCE_BASE |
| ⚠️ | **Cold start on restart** — In-memory state lost; no persistence |
| ⚠️ | **No save/load UI** — API exists but no frontend controls |
| ⚠️ | **Sweep report gaps** — ~120 newer constants not covered in sweep groups |

---

## 20. Repository Structure

```
societas/
├── backend/              # FastAPI server, 10 routers, services, dependencies
│   ├── app/
│   │   ├── routers/      # agents, ai, explain, governance, health, metrics, policies, save, simulation
│   │   ├── services/     # Agent, policy, simulation, governance services
│   │   ├── dependencies/ # DI container, engine singleton
│   │   └── repositories/ # SQLite repositories
│   └── requirements.txt
├── frontend/             # Next.js 14 dashboard
│   ├── src/
│   │   ├── pages/        # index (setup), dashboard, agents, governance, policies
│   │   ├── components/   # AgentGrid, MetricsPanel, DossierPanel, ToastStack, 11 panels
│   │   ├── contexts/     # SimulationContext (state, actions, WebSocket)
│   │   ├── store/        # Zustand simulation store (metrics, events)
│   │   ├── services/     # api.ts (axios), websocket.ts
│   │   └── styles/       # globals.css (1492 lines of theme + component CSS)
│   ├── package.json
│   ├── tsconfig.json
│   └── public/           # societas_logo_v2.png, favicon
├── simulation/           # Core deterministic simulation engine
│   ├── agents/           # AgentState, decision_engine, needs_calculator, action_executor, memory_system
│   ├── engine/           # tick_loop (17 steps), simulation_engine
│   ├── world/            # economy (tax, welfare, rent, GDP), metrics_calculator (50+ fields)
│   ├── events/           # event_bus, media_engine (news, fake news, trust effects)
│   └── test_reports/     # sweep_runner.py (9 groups, 27 scenarios)
├── shared/               # Shared types, DTOs, constants, schemas
│   ├── dto/              # AgentDetailDTO, AgentSummaryDTO, SimulationStateResponseDTO
│   ├── schemas/          # AgentState, SimulationState, TickResult
│   ├── types/            # enums (ActionType, EmotionType, WealthClass, PolicyCategory)
│   └── constants/        # defaults.py (~150 constants), simulation_constants.py
├── docker/               # Dockerfiles, compose.yml, .env, .env.example
├── docs/                 # ADRs, guides, architecture overview, PROJECT_OVERVIEW.md
│   └── images/           # setup-screen.png, dashboard.png
├── tests/                # Integration and regression tests (Phase 7, economy, determinism)
├── prompts/              # AI prompt templates by purpose (agent_decide, moral_reasoning, explain)
├── models/               # LLM routing: vllm_router.py, mock fallback
├── scripts/              # Build, deploy, and utility scripts
├── tools/                # Mock tools, parameter sweep helpers
├── vault/                # Obsidian knowledge base (version-controlled project docs)
├── presentation/         # Competition materials
└── contracts/            # Data contract definitions (DTO interfaces)
```

---

**Document generated for SOCIETAS — AMD Hackathon 2026 Submission.**  
Feed this to Claude or any LLM to generate project descriptions, grant proposals, or investor pitches.
