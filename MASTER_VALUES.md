# SOCIETAS Master Values & Simulation Guide

Comprehensive reference for the SOCIETAS agent-based simulation — all constants, dependencies, thresholds, and mechanics across v1–v6.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent State Schema](#agent-state-schema)
3. [Actions & Dependencies](#actions--dependencies)
4. [Needs System (Maslow)](#needs-system-maslow)
5. [Emotion System](#emotion-system)
6. [Unlust (Dissatisfaction) Engine](#unlust-dissatisfaction-engine)
7. [Decision Priority Queue (deterministic_fallback)](#decision-priority-queue)
8. [Economy System](#economy-system)
9. [Policy System](#policy-system)
10. [Lifecycle: Age, Marriage, Birth, Death](#lifecycle)
11. [Social Systems](#social-systems)
12. [Environmental Events](#environmental-events)
13. [Gangs & Organized Crime](#gangs--organized-crime)
14. [Self-Actualization (Maslow Layer 5)](#self-actualization)
15. [Wealth Classes & Multipliers](#wealth-classes--multipliers)
16. [VLLM 3-Model Architecture](#vllm-3-model-architecture)
17. [All Constants Reference](#all-constants-reference)

---

## Architecture Overview

```
SimulationEngine (orchestrator)
  │
  ├── tick_loop.py (12-step tick)
  │    1. Policy effects + aggregate weights
  │    2. Age progression
  │    3. Need decay + environmental effects
  │    3a. Insomnia update
  │    3b. Environmental event processing
  │    4. Marriage formation
  │    4a. Welfare + rent + tax + debt interest
  │    4b. Property market update
  │    5. Emotions (unlust → happiness → state machine)
  │    5a. Purpose/self-actualization
  │    5b. Social: reputation, rumors, communities, gangs, family
  │    6. Action selection + execution (staggered 1/3 per tick)
  │    7. Movement on toroidal grid
  │    7b. Riot events
  │    7c. Inter-community conflict
  │    8. Death checks + birth
  │    9. World metrics + state hash
  │
  ├── decision_engine.py (3-level priority queue)
  ├── action_executor.py (24 actions)
  ├── VLLMRouter / MockAIRouter (LLM interface)
  ├── PolicyEngine (policy lifecycle)
  └── MetricsCollector + EventBus
```

---

## Agent State Schema

Full agent state is defined in `shared/schemas/agent_state.py` (298 lines).

### Core Traits (`AgentTraits`)
All generated via Beta distributions at birth:

| Trait | Default | Beta(α, β) | Description |
|-------|---------|------------|-------------|
| `morality` | 0.5 | Beta(2, 2) | 0=amoral, 1=highly moral |
| `creativity` | 0.5 | Beta(2, 2) | 0=conventional, 1=creative |
| `ambition` | 0.5 | Beta(2, 2) | 0=passive, 1=ambitious |
| `resilience` | 0.5 | Beta(2, 2) | 0=fragile, 1=resilient |
| `dominance_urge` | 0.5 | Beta(2, 2) | 0=submissive, 1=dominant |
| `anger_tendency` | 0.4 | Beta(2, 3) | 0=calm, 1=quick to anger |
| `extraversion` | 0.5 | Beta(2, 2) | 0=introverted, 1=extraverted |
| `risk_tolerance` | 0.5 | Beta(2, 2) | 0=cautious, 1=risk-seeking |

### Needs (`AgentNeeds`)
13 needs across 5 Maslow layers, stored as `Dict[NeedType, float]` where 0=critical, 1=satisfied.

**Layer 1 — Physiological:** FOOD, WATER, SLEEP, SEXUAL_TENSION
**Layer 2 — Safety:** SAFETY, FINANCIAL_SECURITY, SHELTER
**Layer 3 — Love/Belonging:** SOCIAL_CONNECTION, FAMILY_BOND, ROMANTIC_BOND
**Layer 4 — Esteem:** SELF_ESTEEM, REPUTATION, INFERIORITY_GAP
**Layer 5 — Self-Actualization:** (tracked via `purpose_fulfillment`, `self_actualization_drive`)

### Emotions (`AgentEmotions`)
5-state state machine with timers:

| Emotion | Entry Threshold | Timer (ticks) |
|---------|----------------|---------------|
| HAPPY | happiness > 0.65 | -- |
| NORMAL | (default) | -- |
| SAD | happiness < 0.35 | 2 |
| ANGRY | unlust > 0.58 + anger_tendency > 0.4 | 3 |
| DESPAIR | unlust > 0.82 | 4 |

### Key Agent Flags
| Field | Type | Default |
|-------|------|---------|
| `is_alive` | bool | True |
| `employed` | bool | False |
| `money` | float | 100.0 |
| `health` | float | 1.0 |
| `unlust` | float | 0.0 |
| `age` | int | 25 |
| `age_bracket` | str | "young_adult" |
| `spouse` | str\|None | None |
| `community_id` | str\|None | None |
| `insomnia_severity` | float | 0.0 |
| `purpose` | str\|None | None |
| `purpose_fulfillment` | float | 0.0 |
| `hobby` | str\|None | None |
| `good_acts` | int | 0 |
| `crimes_committed` | int | 0 |
| `notoriety` | float | 0.0 |
| `trust_in_govt` | float | 0.5 |
| `protest_count` | int | 0 |

---

## Actions & Dependencies

### Action List (24 actions)

| Action | Category | Conditions | Effects |
|--------|----------|------------|---------|
| **WORK** | Economic | Must be employed | income = salary × (1−tax) × productivity_mod × creativity_mod × wealth_mult |
| **BUY_FOOD** | Economic | money ≥ food_cost | food +0.30, water +0.20 |
| **REST** | Physiological | -- | sleep +0.35, unlust −0.05, insomnia −0.1 |
| **SEEK_JOB** | Economic | Must be unemployed | chance = 0.08 / (1+unemp×2) × (0.5+ambition); success → employed |
| **BEG** | Survival | Nearby moral agents | each gives min(money×0.02, £5); reputation −0.02 |
| **BEFRIEND** | Social | radius < 2, reputation > 0.25 | 55% success; mutual social_connections +0.02 rep |
| **CONSOLE** | Social | Nearby sad/despair agent | social +0.05/0.08, resets emotion_timer |
| **ISOLATE** | Coping | -- | social −0.02 |
| **SHARE** | Prosocial | morality > 0.68, money > 250, nearby poor | gives money×0.06; happiness +0.04, rep +0.03 |
| **STEAL** | Criminal | Morality gate | takes min(victim.money×0.18, £60); rep −0.10, notoriety +0.05 |
| **HARM_OTHER** | Criminal | Morality gate | victim safety −0.18, rep −0.10, health −0.01 |
| **PROTEST** | Political | -- | protest_count +1, social +0.06, trust −0.02 |
| **COMPLAIN** | Political | trust_in_govt < 0.3 | rep +0.02; 15% contagion to nearby |
| **TREAT** | Doctor | job=DOCTOR, nearby health<0.5 | heal by 0.15; earns £120 |
| **COUNSEL** | Therapist | job=THERAPIST, nearby unlust>0.4 | unlust −0.05, happiness +0.08; earns £85 |
| **SPREAD_RUMOR** | Social | dominance > 0.6, nearby targets | creates rumor (10 tick life); dominance −0.05 |
| **SUPPORT_FAMILY** | Family | parent/child in range | See Family Support section |
| **INVEST** | Economic | has money | invest 10-25% of money (cap £50); return 1.0-1.15× |
| **FRAUD** | Criminal | money ≥ 200, morality ≤ 0.3 | gain £30-80; 50% fine if detected |
| **BUY_PROPERTY** | Economic | money ≥ property value | own property, no more rent |
| **CAMPAIGN** | Political | can_campaign() | notoriety +0.1, rep +0.05 |
| **HOBBY** | Leisure | -- | unlust −0.03, happiness +0.04 |
| **COMPLY** | Neutral | -- | outcome="complied" |
| **IDLE** | Default | -- | outcome="idle" |

### Wealth Class Effects on Actions

| Factor | POOR | MIDDLE | RICH | BUSINESS_OWNER |
|--------|------|--------|------|---------------|
| Salary Multiplier | 0.6× | 1.0× | 1.3× | 1.5× |
| Food Cost Multiplier | 1.3× | 1.0× | 0.8× | 0.8× |
| Rent per tick | £5 | £25 | £80 | £120 |
| Education: PRIMARY | 70% | 20% | 5% | 2% |
| Education: SECONDARY | 27% | 60% | 35% | 18% |
| Education: HIGHER | 3% | 20% | 60% | 80% |
| Property Ownership | 10% | 60% | 90% | 98% |

---

## Needs System (Maslow)

### Need Decay Rates (base, per tick)
Needs decay linearly by these rates every tick, modified by scarcity:

| Need | Base Decay Rate |
|------|----------------|
| FOOD | 0.018 |
| WATER | 0.014 |
| SLEEP | 0.040 |
| SEXUAL_TENSION | 0.008 (growth) |
| SAFETY | 0.004 |
| SOCIAL_CONNECTION | 0.009 |
| FAMILY_BOND | 0.005 |
| ROMANTIC_BOND | 0.006 |
| SELF_ESTEEM | 0.003 |
| REPUTATION | 0.001 |

### Scarcity Modifier
```
scarcity = SCARCITY_BASE (2.0) - food_availability (default 0.85)
decay *= scarcity  // e.g., default: 2.0 - 0.85 = 1.15×
```

### Environmental Crisis Modifier
When `food_availability < 0.4`: FOOD decay multiplied by 1.2×
When `water_availability < 0.4`: WATER decay multiplied by 1.2×

### Death Thresholds
| Cause | Threshold | Notes |
|-------|-----------|-------|
| Starvation | FOOD ≤ 0.02 | -- |
| Dehydration | WATER ≤ 0.02 | -- |
| Health failure | health ≤ 0.02 | -- |
| Insomnia exhaustion | SLEEP < 0.05 AND ticks_without_sleep ≥ 50 | -- |
| Despair | emotion = DESPAIR | 0.4% per tick |
| Old age (elderly) | age_bracket = elderly | 0.1% base + 0.8% elderly = 0.9%/tick |
| Economic hardship | -- | calculated per tick (see below) |

Economic hardship death formula:
```
risk = (1.0 - employed) × (1.0 - min(1.0, money/500)) × max(0.0, inflation) × 10 × 0.003 × 2
```

---

## Emotion System

### State Machine Transitions
```
NORMAL ──happiness>0.65──► HAPPY
HAPPY  ──happiness<0.35──► SAD
NORMAL ──unlust>0.58 AND anger_tendency>0.4──► ANGRY
ANGRY  ──timer_expires──► NORMAL
NORMAL ──unlust>0.82──► DESPAIR
SAD    ──timer_expires──► NORMAL
DESPAIR──timer_expires──► SAD
```

### Happiness Formula
```
happiness = (
    FOOD          × 0.11 +
    WATER         × 0.09 +
    SAFETY        × 0.09 +
    SOCIAL        × 0.09 +
    SLEEP         × 0.08 +
    SELF_ESTEEM   × 0.08 +
    financial     × 0.08 +
    HEALTH        × 0.13 +
    REPUTATION    × 0.05 +
    (1 - unlust)  × 0.15 +
    employed_bonus(0.05)
)
```

---

## Unlust (Dissatisfaction) Engine

### Formula
```
unlust = (
    (1 - FOOD)          × 0.28 +
    (1 - WATER)         × 0.22 +
    (1 - SAFETY)        × 0.20 +
    (1 - SOCIAL)        × 0.12 +
    financial_unlust    × 0.18 +
    morality_penalty    (if morality < 0.58)
)
```
Where `financial_unlust = money / 600` and `morality_penalty` applies when actions contradict morality.

---

## Decision Priority Queue (deterministic_fallback)

The deterministic fallback in `decision_engine.py` has 3 levels of hard priority, then weighted random:

### Level 1 — Critical Survival (checked first)
```python
if food < 0.08 or water < 0.08:
    if money ≥ food_cost → BUY_FOOD
    elif not moral → STEAL
    else → BEG
```

### Level 2 — Stability (checked second)
```python
if not employed → SEEK_JOB
if money < 120 → WORK (if employed) / BEG (if not)
```

### Level 3 — Weighted Selection
Weights dictionary (action → base weight + conditional bonuses):

| Action | Base Weight | Condition | Bonus |
|--------|------------|-----------|-------|
| WORK | 40.0 | always | -- |
| REST | 10.0 | always | -- |
| BEFRIEND | 5.0 | always | +10 if social < 0.5 |
| SHARE | 10.0 | morality > 0.68 AND money > 250 | -- |
| CONSOLE | 5.0 | emotion = SAD or DESPAIR | -- |
| COMPLAIN | 5.0 | trust_in_govt < 0.3 | -- |
| ISOLATE | 5.0 | unlust > 0.4 | +25 if DESPAIR |
| STEAL | 0 | conditionally | +20 if unlust > 0.45 AND not moral; +10 if ANGRY |
| PROTEST | 0 | conditionally | +15 if unlust > 0.45 AND not moral; +20 if ANGRY |
| HARM_OTHER | 0 | conditionally | +5 if unlust > 0.45 AND not moral AND anger>0.6; +8 if ANGRY |
| BEG | 0 | conditionally | +10 if DESPAIR |

Selection is `rng.weighted_choice(weights)`, which picks an action proportional to its weight.

### Policy Weight Modifiers (added to action weights)
```
WORK      += economic_freedom × 0.1
SHARE     += social_welfare × 0.15
CONSOLE   += social_welfare × 0.1
STEAL     -= social_welfare × 0.1 + public_order × 0.15
HARM_OTHER -= public_order × 0.2
PROTEST   -= public_order × 0.1
```

---

## Economy System

### Jobs & Salaries (annual, £)
| Job | Salary Range | Education | Category |
|-----|-------------|-----------|----------|
| Engineer | £80k-130k | HIGHER | Technical (15%) |
| Computer Scientist | £90k-130k | HIGHER | Technical |
| Pilot | £80k-120k | SECONDARY | Mid-tier (35%) |
| Doctor | £80k-130k | HIGHER | Mid-tier |
| Therapist | £40k-70k | HIGHER | Mid-tier |
| Mechanic | £30k-50k | SECONDARY | Mid-tier |
| Electrician | £35k-55k | SECONDARY | Mid-tier |
| Construction Planner | £40k-60k | SECONDARY | Mid-tier |
| Construction Worker | £25k-40k | PRIMARY | Manual (50%) |
| Cleaner | £18k-30k | PRIMARY | Manual |
| Taxi Driver | £20k-35k | PRIMARY | Manual |
| Artist | £25k-65k | SECONDARY | Creative |
| Writer | £30k-80k | SECONDARY | Creative |
| Musician | £20k-60k | SECONDARY | Creative |
| Community Leader | £40k-100k | SECONDARY | Leadership |

**Per-tick salary** = `annual_salary / 365 × wealth_class_multiplier`

### Wealth Class Money Ranges
| Class | Range (starting) | Classification |
|-------|-----------------|----------------|
| POOR | £100-800 | £0-1,000 |
| MIDDLE | £2,000-8,000 | £1,000-15,000 |
| RICH | £15,000-80,000 | £15,000-80,000 |
| BUSINESS_OWNER | £80,000-200,000 | £80,000+ |

### Distribution
| Class | % of Population |
|-------|----------------|
| POOR | 50% |
| MIDDLE | 35% |
| RICH | 15% |
| BUSINESS_OWNER | 0% (earned via investment) |

### Welfare & Tax
- Default tax rate: **15%**
- Welfare amount: **£8/tick** (paid to unemployed when welfare_enabled)
- Tax is progressive: POOR × 1.0, MIDDLE × 1.2, RICH × 1.5 (effective rate, capped at 80%)

### Debt
- Interest rate: **1% per tick**
- Agents can go into debt when buying food they can't afford

### Labor Market
- `compute_job_demand()`: supply/demand per job type
- `adjust_salaries()`: salary multipliers fluctuate based on demand
- `maybe_change_job()`: unemployed agents may accept available jobs
- Default unemployment rate: **10%**

---

## Policy System

### Policy Categories
| # | Category | Weight Dimensions |
|---|----------|-------------------|
| 1 | ECONOMIC | economic_freedom |
| 2 | SOCIAL | social_welfare |
| 3 | ENVIRONMENTAL | environmental_protection |
| 4 | PUBLIC_ORDER | public_order |
| 5 | EDUCATION | innovation |
| 6 | HEALTHCARE | (unused) |
| 7 | INFRASTRUCTURE | (unused) |
| 8 | CULTURAL | cultural_preservation |

### PolicyWeights (6 dimensions, each clamped to [-1, 1])
| Dimension | Effect on Actions |
|-----------|------------------|
| `economic_freedom` | > 0 boosts WORK |
| `social_welfare` | > 0 boosts SHARE, CONSOLE; reduces STEAL |
| `environmental_protection` | Not yet wired |
| `public_order` | > 0 reduces STEAL, HARM_OTHER, PROTEST |
| `innovation` | Not yet wired |
| `cultural_preservation` | Not yet wired |

### ImpactDelta (per wealth class, applied each tick)
| Field | Type | Purpose |
|-------|------|---------|
| `money_delta` | float | Per-tick money change |
| `food_delta` | float | Per-tick food need change |
| `safety_delta` | float | Per-tick safety need change |
| `social_delta` | float | Per-tick social need change |
| `anger_spike` | float | Added to agent.unlust |
| `new_tax_rate` | float\|None | Applied once to world.tax_rate |
| `welfare_on` | bool\|None | Applied once to world.welfare_enabled |
| `food_event` | float\|None | Applied once to world.food_availability |

### Fallback Keyword Policies (8 presets)
| Keyword | Weights | Key Effects |
|---------|---------|-------------|
| "tax increase" | econ_freedom=-0.3, order=0.1 | POOR: −£2; MIDDLE: −£10; RICH: −£50 |
| "tax cut" | econ_freedom=+0.3 | POOR: +£2; MIDDLE: +£10; RICH: +£50 |
| "welfare" | social=0.4 | POOR: +£8, safety +0.05; RICH: −£5 |
| "food subsidy" | social=0.2 | POOR: food +0.10, −£1; RICH: food +0.02, −£10 |
| "police" | order=0.4 | POOR: safety +0.10; MIDDLE: +0.08; RICH: +0.05 |
| "education" | econ=0.1, social=0.2 | POOR: +£5, safety +0.03; RICH: −£20 |
| "housing" | social=0.3 | POOR: safety +0.08, +£3; RICH: −£15 |
| "minimum wage" | econ=−0.1, social=0.2 | POOR: +£5; MIDDLE: +£3; RICH: −£10 |

### LLM Policy Path
When `enable_ai=True` and policy has a description:
1. Engine sends description to **Gemma 4 31B** (port 8000)
2. LLM returns structured `PolicyWeights` + `ImpactDelta`s + `world_changes`
3. Effects applied to world state + each agent per wealth class
4. On failure → falls back to keyword matching

---

## Lifecycle

### Age Brackets
| Bracket | Age Range | Mortality Modifier |
|---------|-----------|-------------------|
| child | 0-18 | (not independently simulated) |
| young_adult | 19-40 | base (0.1%) |
| middle_adult | 41-65 | base (0.1%) |
| elderly | 66-1000 | base + 0.8% = 0.9%/tick |

### Birth Eligibility
- Both parents must be alive, age 18-50, married
- Base chance: **0.2% per tick**
- Newborn inherits 70% of parent wealth (split between both parents)
- Traits generated via Beta distributions
- Linked as siblings to existing children

### Marriage
- Age range: 19-65
- Base probability: **5% per tick** for eligible pairs
- Requirements: grid proximity ≤ 3, wealth ratio ≥ 0.3 (relative), age gap ≤ 15, not enemies, opposite gender
- Sets `spouse`, `family_id`, `marriage_tick`

### Family Support
| Type | Direction | Amount | Condition |
|------|-----------|--------|-----------|
| Education support | Parent → Child | £15/tick | child age < 25 |
| Elderly support | Child → Parent | £8/tick | parent age ≥ 65 |
| Unlust relief | Both directions | −0.02 | when support given |
| Base probability | Both directions | 10%/tick | when eligible |

### Death Causes (7 total)
| Cause | Trigger |
|-------|---------|
| `food_starvation` | FOOD ≤ 0.02 |
| `water_dehydration` | WATER ≤ 0.02 |
| `health_failure` | health ≤ 0.02 |
| `insomnia_exhaustion` | SLEEP < 0.05 + ticks_without_sleep ≥ 50 |
| `despair` | emotion = DESPAIR + 0.4% dice roll |
| `old_age` | elderly bracket + 0.9% dice roll |
| `economic_hardship` | formula-based (unemployed + low money + inflation) |

---

## Social Systems

### Reputation
- Range: 0.0 to 1.0 (drifts toward 0.5)
- Decay rate: **0.001/tick**
- Crime penalty: −0.02 per crime (scaled by min(crimes,10)/10)
- Good-acts bonus: +0.01 per act (scaled similarly)
- `rep < 0.3`: self-esteem −0.01/tick
- `rep > 0.7`: self-esteem +0.005/tick

### Gossip Propagation
- **10%** chance per tick per nearby agent to learn reputation
- Known reputations decay at **0.05/tick**

### Communities
- Reclustered every **10 ticks** via BFS proximity
- Min size: **3 agents**; Max size: **15 agents**
- Members get social connection boost (+0.005/tick)
- Leader present → safety +0.10 for all members
- Leader → reputation +0.02/tick

### Rumors
| Parameter | Value |
|-----------|-------|
| Min dominance_urge to spread | 0.6 |
| Magnitude range | 0.05-0.15 rep penalty |
| Lifetime | 10 ticks |
| Propagation chance per connection | 30% |
| BFS depth | 3 hops |
| Per-tick rep penalty | magnitude / 10 |

### Inter-Community Tension
Computed per community pair as:
```
tension = wealth_gap × 0.3 + pop_imbalance × 0.5 + proximity × 0.2
```
Where each factor is [0, 1].

| Threshold | Event | Probability | Effect |
|-----------|-------|-------------|--------|
| > 0.3 | Gang recruitment | 15%/tick | Tag 1/3 of source community |
| > 0.5 | Property damage | 30%/tick | 5% wealth loss, lose property |
| > 0.6 | Hate crimes | 20%/tick | safety −0.20, trust −0.05 |

Tension decays at **0.01/tick**, floor 0.

### Riot Events
Conditions (both needed):
```
protest_intensity > 0.3  AND  (unlust > 0.5  OR  food_availability < 0.3)
```
Effects:
- 30% of eligible join (agents with protest_count > 0)
- trust_in_govt −0.10
- Nearby non-participants: 50% chance of safety −0.15
- World: food −0.05, crime_rate +0.02

---

## Environmental Events

| Event | Probability | Duration | Effect |
|-------|-------------|----------|--------|
| Famine | 15% | 10 ticks | food −0.40 |
| Drought | 15% | 10 ticks | water −0.40 |
| Abundance | 10% | 10 ticks | food +0.15, water +0.10 |
| Mild shortage | 25% | 5 ticks | food/water −0.05 to −0.10 |
| Normal | 35% | -- | no change |

**Cycle timing:** 15-40 ticks between events
**Phase-in:** 3 ticks to reach full effect
**Regression:** 0.005/tick back to defaults (food=0.85, water=0.90)

---

## Gangs & Organized Crime

### Gang Formation
- Eligibility: unlust > 0.6, morality < 0.3, POOR wealth class
- Cluster via BFS proximity (radius 2)
- **5+** eligible agents within proximity → 10% chance to form a gang
- Leader = first in shuffled cluster

### Gang Actions (40/30/30 split)
| Roll | Action | Effect |
|------|--------|--------|
| < 0.4 (40%) | Extort | up to £15 from nearby non-member; notoriety +0.02 |
| 0.4-0.7 (30%) | Fight rival gang | 50/50; loser loses member; winner notoriety +0.05 |
| ≥ 0.7 (30%) | Protect members | set gang_protected; crime immunity |

### Recruitment
- 5%/tick per eligible agent (POOR, unlust > 0.6, not in gang, nearby gang member)

### Power Formula
```
power = wealth × 0.01 + member_count × 0.1
```

### Member Effects
- Safety need: +0.02/tick
- If crimes ≤ 1: crime immunity
- Reputation: −0.005/tick

---

## Self-Actualization

### Purpose Assignment
- 5%/tick chance to receive a purpose
- Purposes: `["create_art", "build_community", "seek_knowledge", "achieve_wealth", "gain_power"]`
- Purpose fulfillment: +0.02 per relevant action, −0.002/tick decay when idle

### Effects
| Fulfillment Level | Effect |
|-------------------|--------|
| High (> 0.6) | happiness +0.05 |
| Low (< 0.2) + persistent | despair risk +0.01/tick |
| Low + DESPAIR | existential death chance 0.1%/tick |

### Creative Professions
- **5%** of agents with creativity > 0.7 assigned as artists/writers/musicians
- Creative happiness bonus: +0.08

### Political Career
- Campaign action builds notoriety
- Political influence tracked per agent
- Community leader role: reputation +0.02/tick, safety +0.10 for community

---

## Wealth Classes & Multipliers

### Complete Multiplier Table
| Factor | POOR | MIDDLE | RICH | BUSINESS_OWNER |
|--------|------|--------|------|---------------|
| Salary | 0.6× | 1.0× | 1.3× | 1.5× |
| Food cost | 1.3× | 1.0× | 0.8× | 0.8× |
| Rent/tick | £5 | £25 | £80 | £120 |
| Property | 10% | 60% | 90% | 98% |
| Population | 50% | 35% | 15% | 0% (earned) |
| Higher edu | 3% | 20% | 60% | 80% |
| Secondary | 27% | 60% | 35% | 18% |
| Primary | 70% | 20% | 5% | 2% |

---

## VLLM 3-Model Architecture

| Model | Port | Temp | Max Tokens | Purpose |
|-------|------|------|------------|---------|
| Gemma 4 E2B | 8001 | 0.0 | 64 | Agent decisions (~20/tick) |
| Gemma 4 26B A4B | 8002 | 0.2 | 256 | Moral reasoning with thinking |
| Gemma 4 31B | 8000 | 0.3 | 512 | Governance advisory, policy translation |

### Mock Fallback (when server unreachable)
The VLLMRouter always reports `is_available() = True`. On failed LLM calls, it returns:
```json
{"action": "work", "feeling": "neutral", "reason": "vllm fallback"}
```
The `_mock_decide()` function generates trait-aware responses using `deterministic_fallback()`.

### LLM Call Count
- ~7-10 AI calls per tick for 20-30 agents (33% evaluate per tick due to staggering)
- Each call ~2-3 seconds when server unreachable (connection timeout)
- When real server available: ~0.3-0.5s per call

---

## World State Metrics (SimulationState)

Full world state tracked in `shared/schemas/simulation_state.py`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `time_step` | int | 0 | Current tick |
| `population` | int | 0 | Living agent count |
| `economic_health` | float | 0.5 | Composite economic indicator |
| `social_cohesion` | float | 0.5 | Social stability measure |
| `environmental_quality` | float | 0.5 | Environmental health |
| `public_order` | float | 0.5 | Public order index |
| `innovation_index` | float | 0.5 | Innovation metric |
| `unlust` | float | 0.0 | Average systemic unhappiness |
| `morality` | float | 0.5 | Average agent morality |
| `food_availability` | float | 0.85 | Food supply (0-1) |
| `water_availability` | float | 0.90 | Water supply (0-1) |
| `crime_rate` | float | 0.05 | Overall crime rate (0-1) |
| `protest_intensity` | float | 0.0 | Protest escalation level |
| `unemployment_rate` | float | 0.10 | Jobless rate |
| `tax_rate` | float | 0.15 | Current tax rate |
| `welfare_enabled` | bool | False | Welfare system flag |
| `welfare_amount` | float | 8.0 | Per-tick welfare payout |
| `national_debt` | float | 0.0 | Accumulated debt |
| `inflation_rate` | float | 0.0 | Economic inflation |

### Sub-States
- **EconomyState**: gdp, unemployment_rate, inflation_rate, wealth_distribution, consumer_confidence, etc.
- **CrimeState**: overall_crime_rate, crime_by_type, enforcement_effectiveness, incarceration_rate, etc.
- **NeedsState**: average_need_levels, fulfillment_rate, unmet_needs_count, most_urgent_need
- **PsychologyState**: average_morality, average_happiness, average_stress, emotional_distribution

---

## Event Log & Explainability

### Events Published
The dashboard displays events from the database (`recent_events` array at `/api/v1/metrics/dashboard`):

| Event Type | Trigger | Data |
|------------|---------|------|
| `agent_acted` | Every action execution | agent_id, action |
| `env_event` | Environmental event starts | type (famine/drought/etc), tick |
| `marriage` | Marriage formed | count, tick |
| `evictions` | Property eviction | count |
| `property_upgrades` | Property bought | count |
| `riot` | Riot triggered | tick |

### LLM Explainability Panel
Every AI call logs:
- `tick`: Tick number
- `agent_id`: Which agent decided
- `model_type`: `agent_decide` or `moral_reasoning`
- `action`: Chosen action
- `reason`: Natural language reasoning (truncated 200 chars)
- `feeling`: Emotional descriptor (truncated 100 chars)

Displayed as a scrollable list at the bottom of the dashboard, newest first.

### Personas
Generated by rule-based system at agent creation (no LLM used):
- Combines age bracket, gender, job, wealth class
- Adds trait modifiers for high/low values
- Example: *"A man in midlife working as a construction worker with limited financial means."*
- Example: *"An elderly woman working as a cleaner with limited financial means. disciplined and organized. outgoing and sociable."*

---

## All Constants Reference

### Emotional & Happiness Weights
| Constant | Value |
|----------|-------|
| HAPPY_THRESHOLD | 0.65 |
| SAD_THRESHOLD | 0.35 |
| ANGRY_UNLUST_THRESHOLD | 0.58 |
| DESPAIR_UNLUST_THRESHOLD | 0.82 |
| ANGRY_TENDENCY_THRESHOLD | 0.4 |
| SAD_TIMER | 2 |
| ANGRY_TIMER | 3 |
| DESPAIR_TIMER | 4 |

### Unlust Weights (sum = 1.0)
| Component | Weight |
|-----------|--------|
| FOOD | 0.28 |
| WATER | 0.22 |
| SAFETY | 0.20 |
| SOCIAL | 0.12 |
| FINANCIAL | 0.18 |
| MORALITY_GATE | 0.58 |
| NEED_THRESHOLD | 0.7 |
| FINANCIAL_DIVISOR | 600.0 |

### Happiness Weights (sum = 1.0)
| Component | Weight |
|-----------|--------|
| FOOD | 0.11 |
| WATER | 0.09 |
| SAFETY | 0.09 |
| SOCIAL_CONNECTION | 0.09 |
| SLEEP | 0.08 |
| SELF_ESTEEM | 0.08 |
| FINANCIAL_SECURITY | 0.08 |
| HEALTH | 0.13 |
| REPUTATION | 0.05 |
| (1 - unlust) | 0.15 |
| employed_bonus | 0.05 |

### Mortality Rates
| Cause | Rate |
|-------|------|
| Despair (per tick when DESPAIR) | 0.004 |
| Old age base (all agents) | 0.001 |
| Old age elderly bonus | 0.008 |
| Economic hardship base | 0.003 |
| Existential despair (low purpose) | 0.001 |

### Sleep & Insomnia
| Constant | Value |
|----------|-------|
| SLEEP_DECAY_RATE | 0.04 |
| SLEEP_RECOVERY_REST | 0.35 |
| SLEEP_RECOVERY_NATURAL | 0.02 |
| SLEEP_REPLENISH_RATE | 0.05 |
| SLEEP_RESET_THRESHOLD | 0.5 |
| SLEEP_HALF_TIMER_THRESHOLD | 0.3 |
| SLEEP_DEATH_THRESHOLD | 0.05 |
| INSOMNIA_STRESS_THRESHOLD | 0.6 |
| INSOMNIA_SAFETY_THRESHOLD | 0.3 |
| INSOMNIA_INCREASE_RATE | 0.03 |
| INSOMNIA_DECAY_RATE | 0.02 |
| INSOMNIA_MAX | 1.0 |

### Job & Economy
| Constant | Value |
|----------|-------|
| JOB_LOSS_RATE | 0.002 |
| JOB_LOSS_ECON_SENSITIVITY | 2.0 |
| JOB_SEEK_ECON_SENSITIVITY | 1.5 |
| INFLATION_DECAY_RATE | 0.002 |
| DEBT_INTEREST_RATE | 0.01 |
| BASE_FOOD_COST | 10.0 |
| DEFAULT_TAX_RATE | 0.15 |
| DEFAULT_WELFARE_AMOUNT | 8.0 |
| BASE_UNEMPLOYMENT_RATE | 0.10 |
| SCARCITY_BASE | 2.0 |
| FOOD_AVAILABILITY_DEFAULT | 0.85 |
| WATER_AVAILABILITY_DEFAULT | 0.90 |
| SEEK_JOB_BASE_CHANCE | 0.08 |
| BEG_MAX_AMOUNT | 5.0 |
| STEAL_PERCENTAGE_CAP | 0.18 |
| STEAL_AMOUNT_CAP | 60.0 |
| SHARE_PERCENTAGE | 0.06 |

### Lifecycle Constants
| Constant | Value |
|----------|-------|
| AGE_CHILD_MAX | 18 |
| AGE_YOUNG_ADULT_MAX | 40 |
| AGE_MIDDLE_ADULT_MAX | 65 |
| AGE_ELDERLY_MAX | 1000 |
| AGE_PROGRESSION_INTERVAL | 1 |
| BIRTH_CHANCE_BASE | 0.002 |
| MIN_ADULT_AGE_FOR_BIRTH | 18 |
| MAX_REPRODUCTION_AGE | 50 |
| DEATH_INHERITANCE_FRACTION | 0.7 |
| MARRIAGE_BASE_PROBABILITY | 0.05 |
| MARRIAGE_AGE_MIN | 19 |
| MARRIAGE_AGE_MAX | 65 |
| MARRIAGE_MAX_AGE_GAP | 15 |
| MARRIAGE_WEALTH_COMPAT | 0.3 |
| MARRIAGE_GRID_PROXIMITY | 3 |
| PARENT_EDUCATION_SUPPORT | 15.0 |
| CHILD_ELDERLY_SUPPORT | 8.0 |
| SUPPORT_FAMILY_EDUCATION_AGE_MAX | 25 |
| SUPPORT_FAMILY_PARENT_AGE_MIN | 65 |
| SUPPORT_FAMILY_PROBABILITY | 0.10 |
| SUPPORT_FAMILY_UNLUST_RELIEF | 0.02 |

### Sibling Dynamics
| Constant | Value |
|----------|-------|
| SIBLING_JEALOUSY_WEALTH_WEIGHT | 0.4 |
| SIBLING_JEALOUSY_SUCCESS_WEIGHT | 0.3 |
| SIBLING_JEALOUSY_DECAY_RATE | 0.02 |
| SIBLING_BOND_INCREASE_RATE | 0.01 |
| SIBLING_BOND_DECREASE_RATE | 0.03 |
| SIBLING_AFFECT_UNLUST_WEIGHT | 0.15 |
| SIBLING_SUPPORT_PROBABILITY | 0.05 |

### Adler Comparison
| Constant | Value |
|----------|-------|
| ADLER_GAP_THRESHOLD | 0.15 |
| ADLER_INFERIORITY_GAIN_PER_GAP | 0.1 |
| ADLER_SELF_ESTEEM_CHANGE_PER_GAP | 0.05 |
| ADLER_UNLUST_CHANGE_PER_GAP | 0.03 |
| ADLER_DOMINANCE_CHANGE_PER_GAP | 0.02 |
| ADLER_SUPERIORITY_GAIN | 0.02 |

### Social System Constants
| Constant | Value |
|----------|-------|
| REPUTATION_DECAY_RATE | 0.001 |
| REPUTATION_CRIME_PENALTY | 0.02 |
| REPUTATION_GOOD_BONUS | 0.01 |
| REPUTATION_CHANGE_GOOD | 0.02 |
| REPUTATION_CHANGE_CRIMINAL | −0.06 |
| REPUTATION_CHANGE_KILL | −0.30 |
| GOSSIP_SPREAD_CHANCE | 0.1 |
| REPUTATION_KNOWN_DECAY | 0.05 |
| COMMUNITY_RECLUSTER_INTERVAL | 10 |
| COMMUNITY_MIN_SIZE | 3 |
| COMMUNITY_MAX_SIZE | 15 |
| LEADER_SAFETY_BONUS | 0.1 |
| LEADER_REPUTATION_GAIN | 0.02 |
| CREATIVE_HAPPINESS_BONUS | 0.08 |

### Rumor Constants
| Constant | Value |
|----------|-------|
| RUMOR_DOMINANCE_THRESHOLD | 0.6 |
| RUMOR_MAGNITUDE_MIN | 0.05 |
| RUMOR_MAGNITUDE_MAX | 0.15 |
| RUMOR_DECAY_PER_TICK | 0.1 |
| RUMOR_PROPAGATION_CHANCE | 0.3 |
| RUMOR_BFS_DEPTH | 3 |

### Riot Constants
| Constant | Value |
|----------|-------|
| RIOT_PROTEST_THRESHOLD | 0.3 |
| RIOT_UNLUST_THRESHOLD | 0.5 |
| RIOT_FOOD_THRESHOLD | 0.3 |
| RIOT_JOIN_CHANCE | 0.3 |

### Gang Constants
| Constant | Value |
|----------|-------|
| GANG_FORMATION_MIN_MEMBERS | 5 |
| GANG_FORMATION_PROBABILITY | 0.1 |
| GANG_RECRUIT_BASE_CHANCE | 0.05 |
| GANG_EXTORT_AMOUNT | 15.0 |
| GANG_POWER_MEMBER_WEIGHT | 0.1 |
| GANG_POWER_WEALTH_WEIGHT | 0.01 |
| GANG_MAX_NAME_LENGTH | 20 |

### Environmental Event Constants
| Constant | Value |
|----------|-------|
| ENV_CYCLE_MIN_INTERVAL | 15 |
| ENV_CYCLE_MAX_INTERVAL | 40 |
| ENV_FAMINE_CHANCE | 0.15 |
| ENV_DROUGHT_CHANCE | 0.15 |
| ENV_ABUNDANCE_CHANCE | 0.10 |
| ENV_MILD_SHORTAGE_CHANCE | 0.25 |
| ENV_FAMINE_DROP | 0.4 |
| ENV_DROUGHT_DROP | 0.4 |
| ENV_ABUNDANCE_FOOD_BOOST | 0.15 |
| ENV_ABUNDANCE_WATER_BOOST | 0.10 |
| ENV_FAMINE_DURATION | 10 |
| ENV_DROUGHT_DURATION | 10 |
| ENV_MILD_DURATION | 5 |
| ENV_EVENT_PHASE_IN | 3 |
| ENV_REGRESSION_RATE | 0.005 |
| ENV_FOOD_DEFAULT | 0.85 |
| ENV_WATER_DEFAULT | 0.90 |
| ENV_NEED_DECAY_FOOD_MULTIPLIER | 1.2 |
| ENV_NEED_DECAY_WATER_MULTIPLIER | 1.2 |

### Inter-Community Tension
| Constant | Value |
|----------|-------|
| TENSION_BASE_DECAY | 0.01 |
| TENSION_WEALTH_GAP_WEIGHT | 0.3 |
| TENSION_PROXIMITY_WEIGHT | 0.2 |
| TENSION_CRIME_ESCALATION | 0.1 |
| CONFLICT_PROPERTY_DAMAGE_THRESHOLD | 0.5 |
| CONFLICT_HATE_CRIME_THRESHOLD | 0.6 |
| CONFLICT_GANG_RECRUIT_THRESHOLD | 0.3 |

### Purpose & Self-Actualization
| Constant | Value |
|----------|-------|
| PURPOSE_ASSIGN_CHANCE | 0.05 |
| PURPOSE_FULFILLMENT_GAIN | 0.02 |
| PURPOSE_FULFILLMENT_DECAY | 0.002 |
| PURPOSE_HAPPINESS_BONUS | 0.05 |
| PURPOSE_DESPAIR_RISK | 0.01 |
| EXISTENTIAL_DEATH_CHANCE | 0.001 |

### Fraud (White-Collar Crime)
| Constant | Value |
|----------|-------|
| FRAUD_MIN_WEALTH | 200.0 |
| FRAUD_MORALITY_MAX | 0.3 |
| FRAUD_GAIN_MIN | 30.0 |
| FRAUD_GAIN_MAX | 80.0 |
| FRAUD_FINE_MULTIPLIER | 0.5 |
| FRAUD_NOTORIETY_GAIN | 0.2 |

### Grid
| Constant | Value |
|----------|-------|
| GRID_SIZE | 20 (20×20 toroidal grid) |
| INTERACTION_RADIUS | 2 (Euclidean distance) |

### Decision Staggering
| Constant | Value |
|----------|-------|
| DECISION_STAGGER_INTERVAL | 3 (1/3 of agents evaluate per tick) |
| MORAL_DILEMMA_FOOD_THRESHOLD | 0.15 |
| MORAL_DILEMMA_MORALITY_THRESHOLD | 0.5 |
| MORAL_DILEMMA_UNLUST_THRESHOLD | 0.5 |

### Simulation Defaults
| Constant | Value |
|----------|-------|
| DEFAULT_POPULATION_SIZE | 1000 |
| DEFAULT_SIMULATION_SEED | 42 |
| DEFAULT_TICK_RATE_MS | 1000 |
| DEFAULT_MAX_TICKS | 10000 |
| DEFAULT_AGENT_LIFESPAN_TICKS | 5000 |
| DEFAULT_INITIAL_WEALTH | 100.0 |
| DEFAULT_AMBIGUITY_THRESHOLD | 0.05 |
| DEFAULT_DETERMINISTIC_WEIGHT | 0.7 |
| DEFAULT_GEMMA_WEIGHT | 0.3 |
| NEWS_INTERVAL_TICKS | 10 |

### Doctor/Therapist Job Effects
| Constant | Value |
|----------|-------|
| DOCTOR_SALARY | 120.0 (per tick) |
| THERAPIST_SALARY | 85.0 |
| HEAL_EFFECTIVENESS | 0.15 |
| THERAPY_HAPPINESS_BOOST | 0.08 |
| MAX_PATIENTS_PER_DOCTOR | 5 |
| MAX_CLIENTS_PER_THERAPIST | 8 |

### Creative/Leadership Thresholds
| Constant | Value |
|----------|-------|
| CREATIVE_MIN_CREATIVITY | 0.7 |
| LEADER_MIN_REPUTATION | 0.6 |
| LEADER_MIN_MORALITY | 0.5 |
| LEADER_ELECTION_INTERVAL | 50 |
| ARTIST_SALARY | 45.0 |
| WRITER_SALARY | 55.0 |
| MUSICIAN_SALARY | 40.0 |
| COMMUNITY_LEADER_SALARY | 70.0 |
