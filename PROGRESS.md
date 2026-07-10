# SOCIETAS — Project Progress

## Overview

SOCIETAS is an agent-based simulation featuring hundreds of AI-driven agents with personality traits, needs, emotions, and economic roles on a 20×20 toroidal grid. Three Gemma 4 models (E2B, 26B A4B, 31B) serve agent decisions, moral reasoning, and policy translation via an external AMD GPU server.

---

## v1 — Baseline Simulation (Complete)

### Agent System
- **Agent class** with `IAgent` interface, 118 lines
- **13 Needs** across 5 Maslow layers (survival, safety, social, esteem, self-actualization)
- **8 Traits** via Beta distributions: morality, creativity, ambition, resilience, dominance_urge, anger_tendency, extraversion, risk_tolerance
- **5 Emotion states**: neutral, happy, sad, angry, stressed with state machine transitions
- **3 Wealth classes**: POOR (50%), MIDDLE (35%), RICH (15%) with money ranges
- **11 Job types**: doctor, engineer, teacher, artist, etc. with salary ranges
- **AgentFactory**: `create_agent()` + `create_initial_population()` with Beta-distributed traits, socioeconomic status, job assignment
- **Deterministic RNG** for reproducible simulations

### Decision Engine
- `build_agent_prompt()` — constructs LLM prompt from agent state
- `build_moral_dilemma_prompt()` — constructs dilemma prompt when conditions trigger
- `is_moral_dilemma()` — 5 conditions: action is harmful + morality < 0.4 + unlust > 0.6 + anger > 0.5 + need urgency > threshold
- `parse_llm_response()` — parses JSON action responses
- `validate_action()` — validates action type/permissions
- `deterministic_fallback()` — 3-level priority queue: survival → social → growth

### Action System (14 actions → now 22)
- `action_executor.py` (810 lines): work, buy_food, rest, seek_job, beg, befriend, console, isolate, share, steal, harm_other, protest, complain, idle
- Per-action wealth-class multipliers (food costs 2× for rich, salaries scaled)
- Toroidal grid distance calculations
- **v4+ additions**: support_family, treat, counsel, buy_property, spread_rumor, fraud, invest, campaign, hobby

### Simulation Engine
- `SimulationEngine` class with `start()`, `tick()`, `stop()`, `reset()`
- 12-step tick loop (up from original 10)
- `WorldStateManager` wrapping `SimulationState`
- `MetricsCollector`, `EventBus`, `TickScheduler`

### LLM Integration
- `VLLMRouter` (276 lines) — routes to 3 Gemma 4 models on external server (165.245.130.202)
  - E2B port 8001 (temp=0.0): agent decisions
  - 26B A4B port 8002 (temp=0.2): moral reasoning with thinking mode
  - 31B port 8000 (temp=0.3): governance advisory + policy translation
- `MockAIRouter` (299 lines) — trait-aware deterministic responses for testing
- `policy_translator.py` — bridge between policy descriptions and LLM, with keyword fallback

### API Layer (FastAPI Backend)
- Routers: health, simulation, policies, metrics, agents, governance, ai
- Simulation endpoints: GET /status, POST /start/stop/tick/reset, GET /state
- Policy endpoints: GET/POST /, GET/DELETE /{id}
- Metrics endpoints: GET /, GET /dashboard
- WebSocket at /ws for real-time tick broadcasts
- Docker: `docker-compose.yml` with backend(8000), frontend(3000), simulation, vllm(8001)

### Frontend (Next.js 14)
- Dashboard, agents, policies, governance pages
- Charts: TimeSeriesChart, WealthStratifiedChart, ActionFrequencyChart
- MetricsPanel: 8 key metrics (population, economic_health, social_cohesion, crime_rate, protest_intensity, unemployment, unlust, morality)
- DiagnosticsPanel: tick duration, AI calls, ambiguity count, state hash
- `SimulationControls` with start/stop/tick/reset
- AgentGrid: 20×20 canvas with emotion-colored circles, lerp animation, heatmap toggle
- EventLog, ActionDataSummary, LLMPanel
- Auto-run toggle with frontend-setInterval

---

## v2 — Life Cycle (Complete)

### Age System
- **Age brackets**: child (0–18), young adult (19–40), middle adult (41–65), elderly (66–100)
- `progress_age()` — advances age, transitions brackets
- Initial age distribution: 60% young adult, 30% middle, 10% elderly
- Age-dependent mortality in `check_death()`

### Marriage
- `try_form_marriages()` — eligibility: age 19–65, wealth compatibility ratio > 0.7, grid proximity < 3, gender opposite, not enemies
- Base 5% formation probability per eligible pair per tick
- Sets `spouse`, `family_id`, `marriage_tick` on AgentState

### Birth & Inheritance
- `try_birth()` — eligible adults with spouses can produce children
- `DEATH_INHERITANCE_FRACTION = 0.7` of deceased parent's wealth to children
- Child inherits traits via Beta distribution from parent baseline
- `parent_ids`, `children_ids`, `siblings` linked at birth

### Death System
- `check_death()` with 5 causes: starvation, dehydration, health failure, despair, old age
- `cause_of_death` field on AgentState
- `SLEEP_DEATH_THRESHOLD` for insomnia-related death

### Sleep & Insomnia
- `update_insomnia()` — 3 severity tiers with unlust effects
- `energy` field (1.0 → 0.0), `ticks_without_sleep` counter
- `SLEEP_DECAY_RATE`, `SLEEP_RECOVERY_NATURAL`, `SLEEP_RECOVERY_REST`
- Sleep resets via `apply_sleep_reset()` in emotion step

### Sibling Dynamics
- `link_siblings_at_birth()` — wires sibling references in lifecycle
- `update_sibling_dynamics()` — jealousy (extraversion×dominance), bond (conscientiousness), unlust effects
- `maybe_sibling_support()` — money share or console when need < threshold

### Family Support
- `process_family_support()` — education support parent→child (under 25), elderly support child→parent (over 65)
- `support_received`, `support_given` counters
- Unlust relief from family support transactions

---

## v3 — Social Systems (Complete)

### Communities
- `update_communities()` — BFS grid-proximity clustering, recluster every 10 ticks
- `community_effects()` — community_size bonus to safety/reputation
- `community_id` on AgentState

### Inter-Community Conflict
- `compute_community_tensions()` — based on territorial pressure, resource competition, reputation differences
- `check_conflict_events()` — triggers at tension > 0.5, riot events at > 0.6
- `INTER_COMMUNITY_TENSION_DECAY`, `RESOURCE_COMPETITION_FACTOR` constants

### Organized Crime Gangs
- `GangState` dataclass: members, territory, power, formation_tick
- `try_form_gangs()` — formation from agents with high dominance_urge, low morality, unemployed + poor
- `process_gang_actions()` — extortion (POOR, unemployed victims), fight (rival territory), protect (business owners)
- `update_gang_power()` — more members = more power
- `apply_gang_effects()` — victim safety/money effects
- 7 gang-related constants in defaults

### Therapist & Doctor Jobs
- `TREAT` action — heals agent health (reduces health deficit, gives safety boost)
- `COUNSEL` action — improves happiness, gives social boost
- `DOCTOR_SALARY`, `THERAPIST_SALARY`, `HEAL_EFFECTIVENESS`, `THERAPY_HAPPINESS_BOOST`
- Doctors can treat, therapists can counsel

### Rumors
- `SPREAD_RUMOR` action — BFS propagation through social connections
- `apply_rumor_effects()` — reputation damage/bonus
- `decay_rumors()` — time-based decay
- `propagate_rumors()` — distance-attenuated spread
- `RUMOR_DOMINANCE_THRESHOLD`, `RUMOR_MAGNITUDE_MIN/MAX`

---

## v4 — Advanced Economy (Complete)

### White-Collar Crime
- `FRAUD` action — only for rich/middle agents with morality < 0.4
- `detect_fraud()` — detection probability inversely proportional to morality
- `process_fraud()` — 1.5×–3× stake profit on success, stake loss + jail_prob on failure
- Reputation damage on detection

### Investment & Business
- `INVEST` action — money × return_multiplier (0.3–2.5)
- `BUSINESS_OWNER` wealth class
- `invested_capital`, `business_value`, `is_business_owner` on AgentState

### Labor Market
- `compute_job_demand()` — supply/demand per job type based on employed count
- `adjust_salaries()` — demand-driven salary multiplier (0.8–1.5)
- `maybe_change_job()` — unemployed or low-morale agents seek new jobs
- `update_unemployment_rate()` — tracks global unemployment
- `job_demand`, `job_salary_multipliers` on SimulationState

### Property Market
- 4 property tiers (none, rental, owned, luxury) with costs
- `assign_initial_housing()` — POOR=none, MIDDLE=rental (50% owned), RICH=owned (30% luxury)
- `compute_property_values()` — supply/demand driven pricing
- `process_rent()` — rent collection or eviction
- `try_buy_property()` — money > property_cost threshold
- `update_property_market()` — annual market adjustments
- `BUY_PROPERTY` action

---

## v5 — Self-Actualization (Complete)

### Purpose/Meaning System
- `PurposeSystem` — 5 purposes: creative, community, family, achievement, spiritual
- `assign_purpose()` — matched to trait profile at birth
- `update_purpose_fulfillment()` — action-driven fulfillment tracking
- `apply_self_actualization_effects()` — happiness bonus/penalty based on fulfillment
- `check_self_actualization_death()` — existential despair at low fulfillment + high self_actualization need
- `purpose`, `purpose_fulfillment` on AgentState

### Creative Professions
- ARTIST, WRITER, MUSICIAN job types added
- 5% override for agents with creativity > 0.7
- `CREATIVE_MIN_CREATIVITY` threshold
- Creative salary range £15–25

### Community Leadership
- `COMMUNITY_LEADER` job type
- `_assign_community_leader()` — called in `create_initial_population()`
- Requirements: reputation need > `LEADER_MIN_REPUTATION`, morality > `LEADER_MIN_MORALITY`
- Community leader gets safety bonus + reputation gain

### Political Career
- `CAMPAIGN` action — notoriety-based influence gain
- `can_campaign()` — notoriety > 0.3, employed
- `do_campaign()` — influence gain × ambition
- `process_political_influence()` — world-wide influence redistribution
- `track_political_career()` — career stage tracking
- `political_influence`, `political_career_stage` on AgentState

### Hobbies
- `HOBBY` action — mood improvement, reduces unlust
- `hobby`, `hobby_ticks` on AgentState

---

## v6 — UI & Infrastructure (Complete)

### Interactive Governance UI (`/governance`)
- World state overview card (6 metrics)
- Policy sliders: tax rate 0–50%, welfare toggle switch, food subsidy 0–50% (as delta from 0.85)
- Impact preview text
- Active policies list with revoke button
- Create policy form (name/description/category)
- AI policy suggestions panel

### Animated Agent Grid
- Canvas-based rendering (emotion-colored circles)
- 200ms lerp animation between tick positions
- Heatmap overlay toggle (wealth density)
- Hover tooltip with agent details
- `useAnimationFrame` custom hook
- `agentAnimPositions` in simulation store

### Save/Load System
- `save_simulation()`, `load_simulation()` in save_load_manager.py
- JSON serialization of agents, world state, RNG state
- Backend API: GET /save, POST /load/{id}
- Save files in `data/saves/` directory

### AI Policy Suggestions (`/api/v1/governance/suggestions`)
- `analyze_world()` — 6 crisis indicators (unemployment > 0.2, crime_rate > 0.1, etc.)
- `generate_suggestions()` — prioritized action list (unemployment → stimulus, crime → police funding, etc.)
- LLM-powered when available, rule-based fallback

### Chart System
- `TimeSeriesChart`: 7 selectable metrics over last 100 ticks (recharts LineChart)
- `WealthStratifiedChart`: per-class wealth stacked bar + summary table
- `ActionFrequencyChart`: 22 color-coded action bars
- All store last 100 tick snapshots

### LLM Explainability Panel
- `LLMPanel.tsx` — scrollable list of last 30 LLM calls
- Shows model_type badge (Moral/Agent), tick, agent_id, action, reason, feeling
- Data from `llm_log` field in `SimulationStateResponseDTO`
- Accumulates up to 200 entries in store

### API Extensions
- `POST /simulation/tick-n` — advance N ticks at once
- `POST /simulation/auto-run` — backend auto-run endpoint
- `POST /governance/apply` — apply tax/welfare/food changes to world state
- `POST /governance/apply-suggestion` — apply AI-generated policy suggestion

---

## Bug Fixes & Improvements

### Tax System (Fixed)
- **Issue**: `world.tax_rate` was stored but never deducted from agents
- **Fix**: Added `apply_tax()` to `economy.py` with progressive rates (RICH 1.5×, MIDDLE 1.2× base rate, hard cap 80%), wired into `process_economy_tick()`

### Auto-Run (Fixed)
- **Issue**: Backend `start_auto_run()` just stored a number with no background loop
- **Fix**: Frontend `useEffect` + `setInterval` calling `advanceTick()` from context, toggled by store `isAutoRunning` + button

### Personas (Fixed)
- **Issue**: `AgentState.persona` field existed but was never populated
- **Fix**: `_generate_persona()` in agent_factory.py builds description from age, gender, job, wealth class, and 8 trait dimensions

### Food Subsidy Slider (Fixed)
- **Issue**: Slider set `food_availability` directly (range 0–0.5), clashing with default 0.85
- **Fix**: Applied as delta: `min(1.0, 0.85 + subsidy)`

### Governance Dependency Bug (Fixed)
- **Issue**: Governance router used `get_policy_service` instead of `get_simulation_service`
- **Fix**: Changed dependency to `get_simulation_service` in governance.py

### Weblity Stratification Bug (Fixed)
- **Issue**: `_state_to_dto()` referenced `state.agents` which doesn't exist on `SimulationState`
- **Fix**: Changed to `self._engine.get_agents()`

### Frontend TypeScript Build Errors (Fixed)
- **Issue**: `tickFormatter` return type (`string | number`) incompatible with recharts `YAxis` expectation (`string`)
- **Fix**: Changed `formatTick` to always return `String(value)`
- **Issue**: Tooltip `formatter` strict type annotation incompatible with recharts
- **Fix**: Changed parameter type to `any`

### Docker Frontend Build (Fixed)
- **Issue**: `@next/swc-win32-x64-msvc` in dependencies fails on Linux/alpine
- **Fix**: Moved to `optionalDependencies`

### Python 3.10 Compatibility
- **Issue**: Project uses Python 3.11+ `StrEnum`
- **Fix**: Added version check backport: imports `StrEnum` from `enum` if ≥3.11, otherwise defines `class StrEnum(str, Enum)`

---

## Known Gaps

- **Events**: `EventLog` component wired but backend doesn't send descriptive events for all tick steps
- **WebSocket**: WsManager broadcasts tick_completed/agent_acted but frontend doesn't consume via WebSocket (polls REST instead)
- **Crime/Protest Generation**: Thresholds are high enough that crimes rarely trigger in default scenarios
- **400-agent scale**: Tested with 20–80 agents; 500+ may need optimization
- **vLLM local docker**: ROCm vLLM image (`rocm/vllm-dev:rocm6.2_ubuntu22.04`) not available on Docker Hub (external server used instead)
- **Docker Compose**: `docker-compose.yml` in `docker/` directory, not at project root

---

## How to Run

### Docker (recommended)
```powershell
cd docker
docker compose build backend frontend
docker compose up -d backend frontend
```

### Start Simulation
```powershell
curl -X POST http://localhost:8000/api/v1/simulation/start `
  -H "Content-Type: application/json" `
  -d '{"population_size":20,"enable_ai":true}'
```

### Dashboard
Open http://localhost:3000/dashboard

### Governance
Open http://localhost:3000/governance
