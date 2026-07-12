# SOCIETAS — Master Design Reference

> Comprehensive specification of every variable, system, metric, and UI component.
> Designed to be fed to Claude for prompt refinement.
> Version: 1.0 (July 2026)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Agent State Schema](#2-agent-state-schema)
3. [Enums & Types](#3-enums--types)
4. [Traits & Personality](#4-traits--personality)
5. [Needs System (Maslow Hierarchy)](#5-needs-system)
6. [Emotion System](#6-emotion-system)
7. [Unlust Engine](#7-unlust-engine)
8. [Happiness Formula](#8-happiness-formula)
9. [Decision Priority Queue](#9-decision-priority-queue)
10. [All 24 Actions](#10-all-24-actions)
11. [Economy System](#11-economy-system)
12. [Policy System](#12-policy-system)
13. [Lifecycle System](#13-lifecycle-system)
14. [Social Systems](#14-social-systems)
15. [Environmental Events](#15-environmental-events)
16. [Self-Actualization (Maslow Layer 5)](#16-self-actualization)
17. [Media Engine](#17-media-engine)
18. [Memory System](#18-memory-system)
19. [LLM Integration (3-Model Router)](#19-llm-integration)
20. [API Endpoints](#20-api-endpoints)
21. [Dashboard UI Components](#21-dashboard-ui-components)
22. [Store & State Management](#22-store--state-management)
23. [Default Constants Table](#23-default-constants-table)
24. [Calibration Values](#24-calibration-values)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                      │
│  http://localhost:8000/api/v1/*                          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │             12-Step Tick Loop                     │    │
│  │  run_tick() → TickResult                          │    │
│  │  Staggered: 1/3 agents evaluated per tick         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Simulation    │  │Policy        │  │Governance    │  │
│  │Engine        │  │Engine        │  │Service       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │AI Historian  │  │Save/Load    │  │WebSocket     │  │
│  │Service       │  │Manager      │  │Manager       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                      │
│  http://localhost:3000                                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Dashboard     │  │Governance    │  │Policies      │  │
│  │(ledger view) │  │(sliders/form)│  │(list/create) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │AgentGrid     │  │ExplainPanel  │  │AgentDetail   │  │
│  │(pixel sprites)│  │(Q&A)        │  │(slide-in)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  State: Zustand store (simulationStore)                  │
│  API: Axios client (apiService)                          │
│  WS: SimulationWebSocketClient (auto-reconnect)          │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Agent State Schema

### AgentTraits (8 psychological traits, Beta-distributed)

| Field | Alias | Beta(α,β) | Range | Description |
|-------|-------|-----------|-------|-------------|
| `morality` | Agreeableness | Beta(2,2) | 0.0-1.0 | Moral compass, gates criminal actions |
| `creativity` | Openness | Beta(2,2) | 0.0-1.0 | Creative profession eligibility |
| `ambition` | Conscientiousness | Beta(2,2) | 0.0-1.0 | Career advancement |
| `resilience` | Emotional stability | Beta(2,2) | 0.0-1.0 | Shortens emotion timers |
| `dominance_urge` | — | Beta(2,2) | 0.0-1.0 | Rumor spreading, campaign eligibility |
| `anger_tendency` | — | Beta(2,3) | 0.0-1.0 | Skewed low; anger-threshold multiplier |
| `extraversion` | — | Beta(2,2) | 0.0-1.0 | Social need decay, CONSOLE/BEFRIEND weights |
| `risk_tolerance` | — | Beta(2,2) | 0.0-1.0 | STEAL/HARM_OTHER weights |

### AgentNeeds (13 needs across 5 Maslow layers)

**Layer 1 — Physiological:** FOOD, WATER, SLEEP, SEXUAL_TENSION
**Layer 2 — Safety:** SAFETY, FINANCIAL_SECURITY, SHELTER
**Layer 3 — Love/Belonging:** SOCIAL_CONNECTION, FAMILY_BOND, ROMANTIC_BOND
**Layer 4 — Esteem:** SELF_ESTEEM, REPUTATION, INFERIORITY_GAP
**Layer 5 — Self-Actualization:** (tracked via purpose_system.py)

Each need: `NeedValue(float)` — 0.0 = critical/dead, 1.0 = fully satisfied.

### AgentEmotions (5-state machine)

| Field | Type | Description |
|-------|------|-------------|
| `primary` | EmotionType | Current emotional state |
| `intensities` | Dict[EmotionType, float] | Intensity of each emotion |
| `emotion_timer` | int | Remaining ticks in current state |
| `happiness_score` | float | 0.0-1.0 composite happiness |

### AgentResources

| Field | Type | Description |
|-------|------|-------------|
| `money` | float | Liquid currency |
| `base_salary` | float | Per-tick salary |
| `employed` | bool | Employment status flag |
| `education` | EducationLevel | NONE(0) / PRIMARY(1) / SECONDARY(2) / HIGHER(3) |
| `property` | bool | Owns property |
| `property_tier` | int | 0-3 (poor→luxury) |
| `property_value` | float | Market value |
| `rent_cost` | float | Per-tick rent |
| `health` | float | 0.0-1.0, decays -0.001/tick |
| `wealth` | float | money + assets |
| `debt` | float | Outstanding debt |
| `assets` | List[str] | Asset names |
| `skills` | List[str] | Skill names |

### AgentDecisionScores

| Field | Type | Description |
|-------|------|-------------|
| `scores` | Dict[ActionType, float] | Score per action |
| `top_action` | ActionType | Highest-scored action |
| `top_score` | float | Highest score |
| `second_score` | float | Second-highest score |
| `is_ambiguous(thresh=0.05)` | bool | True if top-second < threshold |

### AgentState (~50 fields)

**Identity:** `id: AgentId`, `persona: str`, `gender: Gender`, `culture: Culture`, `born_tick: int`

**Composition:** `traits: AgentTraits`, `needs: AgentNeeds`, `emotions: AgentEmotions`, `resources: AgentResources`, `decision_scores: AgentDecisionScores`

**Employment:** `employment_status: EmploymentStatus`, `wealth_class: WealthClass`, `job_type: JobType`

**Grid:** `grid_x: GridCoordinate`, `grid_y: GridCoordinate`

**Social:** `social_connections: int`, `spouse: Optional[str]`, `siblings: List[str]`, `sibling_jealousy: float`, `sibling_bond: float`, `family_id: Optional[str]`, `marriage_tick: int`, `partner_preferences: Dict`, `enemies: List[str]`, `parent_ids: List[str]`, `children_ids: List[str]`, `community_id: Optional[str]`

**Psychology:** `unlust: float`, `notoriety: float`, `trust_in_govt: float`, `insomnia_severity: float`, `energy: float`, `last_sleep_tick: int`, `ticks_without_sleep: int`

**Tracking:** `good_acts: int`, `crimes_committed: int`, `protest_count: int`, `cause_of_death: Optional[str]`, `memories: List[Memory]`

**Self-Actualization:** `purpose: Optional[str]`, `hobby: Optional[str]`, `hobby_ticks: int`, `purpose_fulfillment: float`, `creativity_unlocked: bool`, `self_actualization_drive: float`, `support_received: float`, `support_given: float`

**Action:** `last_action: Optional[str]`, `last_reasoning: str`

---

## 3. Enums & Types

### ActionType (24 values)

```
WORK, BUY_FOOD, REST, SEEK_JOB, BEG, BEFRIEND, CONSOLE, ISOLATE,
SHARE, STEAL, HARM_OTHER, FRAUD, TREAT, PROTEST, COUNSEL, COMPLAIN,
CAMPAIGN, COMPLY, SPREAD_RUMOR, SUPPORT_FAMILY, INVEST, BUY_PROPERTY,
HOBBY, IDLE
```

### NeedType (13 values)

```
FOOD, WATER, SLEEP, SEXUAL_TENSION, SAFETY, FINANCIAL_SECURITY, SHELTER,
SOCIAL_CONNECTION, FAMILY_BOND, ROMANTIC_BOND, SELF_ESTEEM, REPUTATION,
INFERIORITY_GAP
```

### EmotionType (5 values)

`HAPPY`, `NORMAL`, `SAD`, `ANGRY`, `DESPAIR` — priority order for state machine

### WealthClass (4 values)

`POOR`, `MIDDLE`, `RICH`, `BUSINESS_OWNER`

### JobType (15 values)

```
ENGINEER, COMPUTER_SCIENTIST, PILOT, DOCTOR, THERAPIST, MECHANIC,
ELECTRICIAN, CONSTRUCTION_PLANNER, CONSTRUCTION_WORKER, CLEANER,
TAXI_DRIVER, ARTIST, WRITER, MUSICIAN, COMMUNITY_LEADER, UNEMPLOYED
```

### PolicyCategory (8 values)

`ECONOMIC`, `SOCIAL`, `ENVIRONMENTAL`, `PUBLIC_ORDER`, `EDUCATION`, `HEALTHCARE`, `INFRASTRUCTURE`, `CULTURAL`

### EmploymentStatus (5 values)

`UNEMPLOYED`, `EMPLOYED`, `SELF_EMPLOYED`, `STUDENT`, `RETIRED`

### EducationLevel (4 values, IntEnum)

`NONE(0)`, `PRIMARY(1)`, `SECONDARY(2)`, `HIGHER(3)`

### Gender (2 values)

`MALE`, `FEMALE`

### Culture (3 values)

`A`, `B`, `C`

### CrimeType (7 values)

`THEFT`, `VIOLENCE`, `FRAUD`, `VANDALISM`, `DRUG_OFFENSE`, `TAX_EVASION`, `CORRUPTION`

---

## 4. Traits & Personality

### Beta Distribution Parameters

| Trait | α | β | Notes |
|-------|---|----|-------|
| creativity | 2.0 | 2.0 | Symmetric |
| morality | 2.0 | 2.0 | Symmetric |
| anger_tendency | 2.0 | 3.0 | Skewed low (most agents less angry) |
| extraversion | 2.0 | 2.0 | Symmetric |
| ambition | 2.0 | 2.0 | Symmetric |
| resilience | 2.0 | 2.0 | Symmetric |
| dominance_urge | 2.0 | 2.0 | Symmetric |
| risk_tolerance | 2.0 | 2.0 | Symmetric |

### Persona Generation

Rule-based string built at creation:
```
{A/An} {age_descriptor} {gender} working as {job_type} with {wealth_descriptor} financial means.
```
- Age descriptors: "child", "young adult", "person in midlife", "elderly"
- Gender: "man" / "woman" / "person"
- Wealth descriptors: "very limited" (POOR), "moderate" (MIDDLE), "substantial" (RICH), "extensive" (BUSINESS_OWNER)
- Trait modifiers: high-creativity → "creative", high-morality → "principled", etc.

---

## 5. Needs System

### Decay Rates (per tick)

| Need | Base Decay Rate | Notes |
|------|----------------|-------|
| FOOD | 0.012 | ×1.2 when food_availability < 0.4 |
| WATER | 0.008 | ×1.2 when water_availability < 0.4 |
| SLEEP | 0.02 | Natural recovery +0.02/tick |
| SEXUAL_TENSION | 0.008 (growth) | Grows upward, decay via marriage/befriend |
| SAFETY | 0.004 | Modulated by crime_rate, property |
| SOCIAL | 0.009 | Modulated by extraversion, community size |
| FAMILY | 0.005 | Modulated by family presence |
| ROMANTIC | 0.006 | Modulated by spouse presence |
| SELF_ESTEEM | 0.003 | Modulated by adler comparison |
| REPUTATION | 0.001 | Separate decay in reputation system |
| FINANCIAL_SECURITY | — | Computed from money/wealth |
| SHELTER | — | Boolean (has property) |
| INFERIORITY_GAP | — | Computed from adler system |

### Scarcity Modifier

```
need_decay *= SCARCITY_BASE / (food_availability + water_availability)
```
Where `SCARCITY_BASE = 2.0`. At default (0.85+0.90)/2=0.875, multiplier ≈ 1.14×.

### Death Thresholds

| Condition | Threshold | Dice Roll |
|-----------|-----------|-----------|
| STARVATION | FOOD < 0.02 | No (always die) |
| DEHYDRATION | WATER < 0.02 | No (always die) |
| HEALTH FAILURE | HEALTH < 0.02 | 50% (`rng.random() < 0.5`) |
| INSOMNIA | insomnia > 0.05 + 50 ticks awake | 30% (`rng.random() < 0.3`) |
| DESPAIR | happiness < 0.02 + per-tick roll | `rng.random() < DESPAIR_MORTALITY_RATE(0.004)` |
| EXISTENTIAL | purpose_fulfillment < 0.1 | `rng.random() < EXISTENTIAL_DEATH_CHANCE(0.001)` |
| OLD AGE | elderly + per-tick roll | `rng.random() < AGE_MORTALITY_BASE + AGE_MORTALITY_ELDERLY` |
| ECONOMIC | unemployed + money < 50 | `rng.random() < ECONOMIC_HARDSHIP_DEATH_RATE(0.001)` |

### Wealth Class Thresholds

| Class | Money Range | Distribution |
|-------|-------------|-------------|
| POOR | 0–500 | 50% |
| MIDDLE | 500–5000 | 35% |
| RICH | 5000+ | 15% |
| BUSINESS_OWNER | 80000+ | 0% (earned) |

Initial wealth ranges by class:
- POOR: 100–800
- MIDDLE: 2000–8000
- RICH: 15000–80000
- BUSINESS_OWNER: 80000–200000

---

## 6. Emotion System

### State Machine (tick-based hysteresis)

```
DESPAIR → ANGRY → SAD → HAPPY → NORMAL
(highest priority first)
```

### Trigger Conditions (each tick)

| Emotion | Trigger | Timer (base) |
|---------|---------|-------------|
| HAPPY | happiness_score ≥ 0.65 | — |
| SAD | happiness_score < 0.35 | 2 ticks |
| ANGRY | unlust ≥ 0.45 | 3 ticks |
| DESPAIR | unlust ≥ 0.55 | 4 ticks |

Resilience modulation: `timer = base_timer × (1 - resilience × 0.5)`

### Emotion Modifiers on Actions

| Emotion | Productivity | Creativity | Social |
|---------|-------------|------------|--------|
| HAPPY | 1.2× | 1.3× | 1.4× |
| NORMAL | 1.0× | 1.0× | 1.0× |
| SAD | 0.7× | 0.8× | 0.7× |
| ANGRY | 0.9× | 0.9× | 0.5× |
| DESPAIR | 0.4× | 0.5× | 0.2× |

### Sleep Reset

When agent performs REST action:
```
sleep_quality = current_safety × (1 - unlust) × resilience
Quality > 0.5 → reset to NORMAL
Quality > 0.3 → half timer
else → no reset
```

---

## 7. Unlust Engine

Composite measure of agent distress (0.0–1.0+).

### Component Weights

| Factor | Weight | Input |
|--------|--------|-------|
| Food | 0.28 | 1 - agent.needs.food |
| Water | 0.22 | 1 - agent.needs.water |
| Safety (inverse) | 0.20 | 1 - agent.needs.safety |
| Social (inverse) | 0.12 | 1 - agent.needs.social |
| Financial stress | 0.18 | max(0, 1 - money/600) |

### Morality Gate

```
if unlust >= UNLUST_MORALITY_GATE (0.38):
    → morality-driven actions (STEAL, HARM_OTHER) become available
```

### Emotion Thresholds (must be ordered)

```
ANGRY at unlust >= 0.45
DESPAIR at unlust >= 0.55 (invariant: > UNLUST_MORALITY_GATE)
```

---

## 8. Happiness Formula

```
happiness_score = Σ(weight_i × need_level_i) + employment_bonus
```

| Component | Weight |
|-----------|--------|
| FOOD | 0.11 |
| WATER | 0.09 |
| SAFETY | 0.09 |
| SOCIAL | 0.09 |
| SLEEP | 0.08 |
| SELF_ESTEEM | 0.08 |
| FINANCIAL | 0.08 |
| HEALTH | 0.13 |
| REPUTATION | 0.05 |
| UNLUST (inverse) | 0.15 |
| EMPLOYED BONUS | 0.05 (additive, outside sum) |

Total weighted sum ≈ 1.0, plus 0.05 employment bonus.

---

## 9. Decision Priority Queue

### Level 1 — Critical Survival (checked first)

| Condition | Selected Action |
|-----------|----------------|
| FOOD < 0.08 | BUY_FOOD (if money ≥ FOOD_COST) |
| FOOD < 0.08 AND money < FOOD_COST | STEAL if not moral, else BEG |
| WATER < 0.08 | BUY_FOOD (water bundled) |

### Level 2 — Employment & Stability

| Condition | Selected Action |
|-----------|----------------|
| Not employed AND no job | SEEK_JOB |
| Not employed | SEEK_JOB |
| Money < 120 | WORK (if employed), BEG (if unemployed) |

### Level 3 — Softmax Selection (temperature-scaled probability)

```
P(action) = exp(score_i / temperature) / Σexp(score / temperature)
```

**Temperature:** 0.5 (normal), 0.8 (when unlust > 0.3)

**Score Modulations:**
- **Employment:** WORK gets +50 if employed, -80 if not
- **BEFRIEND:** extraversion × 10 + 5
- **CONSOLE:** +10 if neighbors sad/despair
- **SHARE:** morality × 30 (if money > 250)
- **STEAL:** risk_tolerance × 20 + anger_factor × 15 (unlust > 0.3)
- **PROTEST:** +15 if unlust > 0.3 AND trust_in_govt < 0.4 AND morality < 0.6
- **ISOLATE:** +10 if unlust > 0.4
- **HARM_OTHER:** anger_tendency × 12 (if angry/despair)
- **FRAUD:** risk_tolerance × 8 + dominance_urge × 10 (if money > 200, morality < 0.3)
- **INVEST:** risk_tolerance × 15 + ambition × 10 (if money > 500)
- **BUY_PROPERTY:** ambition × 12 + money/1000 (if no property, money > 2000)
- **CAMPAIGN:** dominance_urge × 15 + notoriety × 10 (if notoriety > 0.3, morality > 0.4)
- **HOBBY:** +5 (always available)
- Moral filter: STEAL and HARM_OTHER blocked if morality > 0.5

### Action Validation

| Action | Required Conditions |
|--------|-------------------|
| BUY_FOOD | money ≥ BASE_FOOD_COST × wealth_multiplier |
| WORK | is employed |
| SEEK_JOB | not employed |
| STEAL | morality ≤ 0.5 |
| HARM_OTHER | morality ≤ 0.5 |
| TREAT | is_doctor AND nearby sick agents |
| COUNSEL | is_therapist AND nearby distressed agents |
| FRAUD | money ≥ 200 AND morality ≤ 0.3 |
| CAMPAIGN | notoriety > 0.3 AND morality > 0.4 AND employed |
| BUY_PROPERTY | money ≥ 2000 AND no property |
| INVEST | money ≥ 500 |
| SPREAD_RUMOR | dominance_urge ≥ 0.5 |

---

## 10. All 24 Actions

### WORK
| Detail | Value |
|--------|-------|
| Effect | Earn `salary × productivity_mod × wealth_multiplier − tax` |
| Productivity mod | Emotion × education (1.0–1.4) |
| Wealth multiplier | POOR: 0.6, MIDDLE: 1.0, RICH: 1.3 |
| Side effects | Increase financial security, decrease sleep |

### BUY_FOOD
| Detail | Value |
|--------|-------|
| Cost | `BASE_FOOD_COST(10) × FOOD_COST_MULTIPLIER` |
| Wealth multiplier | POOR: 1.3×, MIDDLE: 1.0×, RICH: 0.8× |
| Effect | FOOD +0.20, WATER +0.10 |
| Side effects | Inflation markup: `cost × (1 + inflation_rate)` |

### REST
| Detail | Value |
|--------|-------|
| Effect | SLEEP +0.35, insomnia -0.1 |
| Side effects | 30% chance to break ANGRY emotion |

### SEEK_JOB
| Detail | Value |
|--------|-------|
| Chance | `BASE_SEEK_CHANCE × JOB_SEEK_ECON_SENSITIVITY` |
| On success | Assign job based on education, set salary |
| Economy sensitivity | Higher when more jobs available |

### BEG
| Detail | Value |
|--------|-------|
| Max amount | £5/tick |
| Source | Nearby agents with money > £50 |
| Side effects | Small social penalty |

### BEFRIEND
| Detail | Value |
|--------|-------|
| Effect | Social +0.15 both ways |
| Fidelity | 10% chance friendship ends each tick |
| Max friends | Not capped (but social_connections is tracked) |

### CONSOLE
| Detail | Value |
|--------|-------|
| Target | Nearest agent with SAD/DESPAIR emotion |
| Effect | Target happiness +0.08, source social +0.10 |
| Side effects | Counts as good act (+reputation) |

### ISOLATE
| Detail | Value |
|--------|-------|
| Effect | Social −0.20, self_esteem −0.05 |
| Side effects | Sleep +0.05 (rest bonus) |

### SHARE
| Detail | Value |
|--------|-------|
| Amount | 6% of current money |
| Target | Nearest agent with money < £50 |
| Effect | Target money +amount, source happiness +0.03 |
| Side effects | Reputation +0.01 |

### STEAL
| Detail | Value |
|--------|-------|
| Amount | Up to 18% of target money (capped at £60) |
| Target | Nearest agent with money > £30 |
| Morality gate | Blocked if morality > 0.5 |
| Effects | Target becomes angry, reputation −0.06 |

### HARM_OTHER
| Detail | Value |
|--------|-------|
| Effect | Target safety −0.15, target health −0.05 |
| Self cost | Source health −0.03 |
| Morality gate | Blocked if morality > 0.5 |

### PROTEST
| Detail | Value |
|--------|-------|
| Effect | protest_count +1, trust_in_govt −0.05 |
| Side effects | Contributes to protest_intensity metric |

### COMPLAIN
| Detail | Value |
|--------|-------|
| Effect | Nearby agents trust_in_govt −0.03 |
| Range | 2 cells |

### FRAUD
| Detail | Value |
|--------|-------|
| Requirements | money ≥ 200, morality ≤ 0.3 |
| Gain | £30–80 (random) |
| Detection | Not yet implemented (gain always succeeds) |
| Side effects | Notoriety +0.20 if undetected |

### TREAT (doctor)
| Detail | Value |
|--------|-------|
| Requirements | JobType.DOCTOR |
| Target | Nearest agent with health < 0.5 |
| Effect | Target health +0.15 (HEAL_EFFECTIVENESS) |
| Side effects | Earn salary |

### COUNSEL (therapist)
| Detail | Value |
|--------|-------|
| Requirements | JobType.THERAPIST |
| Target | Nearest agent with unlust > 0.3 |
| Effect | Target happiness +0.08, unlust −0.05 |
| Side effects | Earn salary |

### SUPPORT_FAMILY
| Detail | Value |
|--------|-------|
| Direction | Parent→child (if child < 25): send PARENT_EDUCATION_SUPPORT(£15) |
| | Child→parent (if parent > 65): send CHILD_ELDERLY_SUPPORT(£8) |
| Chance per tick | 10% |
| Side effects | unlust −0.02 both parties |

### SPREAD_RUMOR
| Detail | Value |
|--------|-------|
| Requirements | dominance_urge ≥ 0.6 |
| Effect | Target reputation −RUMOR_MAGNITUDE(0.05–0.15) |
| Propagation | BFS depth 3 through social connections |
| Decay | −10% per tick |

### INVEST
| Detail | Value |
|--------|-------|
| Requirements | money ≥ 500 |
| Effect | Deduct investment, return 1.0–1.15× after random interval |

### BUY_PROPERTY
| Detail | Value |
|--------|-------|
| Requirements | money ≥ 2000, no property |
| Effect | property=true, deduct property_value |
| Side effects | Rent stops, shelter need satisfied |

### CAMPAIGN
| Detail | Value |
|--------|-------|
| Requirements | notoriety > 0.3, morality > 0.4, employed |
| Effect | notoriety +0.05, trust_in_govt +0.02 |
| Side effects | Advances political career |

### HOBBY
| Detail | Value |
|--------|-------|
| Effect | Happiness +0.03, unlust −0.02 |
| Options | 5 types (reading, gardening, crafting, sports, music) |

### COMPLY
| Detail | Value |
|--------|-------|
| Effect | No-op (`did not protest`) |
| Side effects | Minor trust_in_govt +0.01 |

### IDLE
| Detail | Value |
|--------|-------|
| Effect | No-op (fallback when no valid action) |

---

## 11. Economy System

### Per-Tick Economy Steps (process_economy_tick)

1. **Inflation decay**: `inflation_rate *= (1 - INFLATION_DECAY_RATE(0.001))`
2. **Labor market**: Adjust job demand based on economy, random salary fluctuation ±5%
3. **Job changes**: Unemployed agents may find jobs, employed may lose them
4. **Apply rent**: Per-wealth-class rent from AgentResources (or property if owned)
5. **Apply welfare**: £WELFARE_AMOUNT(8)/tick if welfare_enabled AND unemployed
6. **Apply tax**: Progressive: MIDDLE pays 1.2× rate, RICH pays 1.5× rate, cap 80%
7. **Apply debt interest**: Compounds at DEBT_INTEREST_RATE(0.05)

### Economic Metrics

| Metric | Formula |
|--------|---------|
| economic_health | Weighted: employment(0.3) + money_ratio(0.3) + gdp(0.2) + inflation_factor(0.2) |
| unemployment_rate | unemployed / total_agents |
| inflation_rate | Decays toward 0 from INFLATION_DECAY_RATE |
| GDP | Σ(agent_salary × productivity) over all employed agents |

### Wealth Class Multipliers

| Class | Salary Multiplier | Food Cost Multiplier | Rent | Property Ownership |
|-------|------------------|---------------------|------|-------------------|
| POOR | 0.6× | 1.3× (food deserts) | £5 | 10% |
| MIDDLE | 1.0× | 1.0× | £25 | 60% |
| RICH | 1.3× | 0.8× (cheaper access) | £80 | 90% |
| BUSINESS_OWNER | 2.0× | 0.7× | £120 | 98% |

### Salary Ranges (annual, per tick approx)

| Job Type | Min (annual) | Max (annual) |
|----------|-------------|-------------|
| ENGINEER | 80,000 | 130,000 |
| COMPUTER_SCIENTIST | 90,000 | 130,000 |
| PILOT | 80,000 | 120,000 |
| DOCTOR | 80,000 | 130,000 |
| THERAPIST | 40,000 | 70,000 |
| MECHANIC | 30,000 | 50,000 |
| ELECTRICIAN | 35,000 | 55,000 |
| CONSTRUCTION_PLANNER | 40,000 | 60,000 |
| CONSTRUCTION_WORKER | 25,000 | 40,000 |
| CLEANER | 18,000 | 30,000 |
| TAXI_DRIVER | 20,000 | 35,000 |
| ARTIST | 25,000 | 65,000 |
| WRITER | 30,000 | 80,000 |
| MUSICIAN | 20,000 | 60,000 |
| COMMUNITY_LEADER | 40,000 | 100,000 |
| UNEMPLOYED | 0 | 0 |

---

## 12. Policy System

### PolicyWeights (6 dimensions, range -1.0 to +1.0)

| Dimension | Description |
|-----------|-------------|
| economic_freedom | Low = regulation, High = laissez-faire |
| social_welfare | Low = austerity, High = generous welfare |
| public_order | Low = civil liberties, High = law enforcement |
| environmental_regulation | Low = exploitation, High = protection |
| education_investment | Low = minimal, High = funded education |
| healthcare_investment | Low = private, High = public healthcare |

### ImpactDelta (per wealth class)

| Field | Description |
|-------|-------------|
| money_delta | Per-tick money change (±) |
| food_delta | Per-tick food need change (±) |
| safety_delta | Per-tick safety need change (±) |
| social_delta | Per-tick social need change (±) |
| anger_spike | Immediate unlust change (±) |

### World Changes

| Field | Description |
|-------|-------------|
| new_tax_rate | Override world tax_rate |
| welfare_on | Toggle welfare_enabled |
| food_event | Override food_availability |

### Fallback Policy Keywords (8 predefined)

| Keyword | Economic Effect | POOR Effect | MIDDLE Effect | RICH Effect |
|---------|----------------|-------------|--------------|-------------|
| tax increase | econ_freedom -0.3, public_order +0.1 | money -2, anger +0.05 | money -10 | money -50 |
| tax cut | econ_freedom +0.2 | money +2 | money +10 | money +30 |
| welfare | social_welfare +0.4 | money +8, safety +0.1 | — | money -5, anger +0.05 |
| food subsidy | social_welfare +0.3 | money +5, food +0.1 | food +0.05 | tax +0.02 |
| police | public_order +0.4 | safety +0.15 | safety +0.08 | — |
| education | education_invest +0.5 | — | — | — |
| housing | social_welfare +0.3 | safety +0.2, money -3 | — | — |
| minimum wage | econ_freedom -0.2, social_welfare +0.3 | money +5 | money -3 | money -8 |

### Policy Application (each tick)

```
Step 1: apply_all_policies(agents, policies, world)
Step 1a: apply_policy_effects → per-class deltas → agent resources/needs/unlust
Step 1b: apply_policy_weights → modify action utility scores
Step 1c: compute_aggregate_weights → sum all active policy weights → [-1, 1] clamp
```

---

## 13. Lifecycle System

### Age Brackets

| Bracket | Age Range | Key Behaviors |
|---------|-----------|---------------|
| Child | 0–18 | No marriage, no work, no birth |
| Young Adult | 19–40 | Marriage eligible, birth eligible, full workforce |
| Middle Adult | 41–65 | Marriage eligible until 65, reduced birth after 50 |
| Elderly | 66+ | No marriage, no birth, age_mortality_elderly risk, child support eligible |

### Age Progression

```
age += AGE_PROGRESSION_INTERVAL(0.1) per tick
```
(200 ticks ≈ 20 simulated years)

### Marriage

| Parameter | Value |
|-----------|-------|
| Base probability | 0.05/tick |
| Min age | 19 |
| Max age | 65 |
| Max age gap | 15 years |
| Wealth compatibility | ratio > 0.3 |
| Grid proximity | ≤ 3 cells (Chebyshev) |
| Gender | Opposite |
| Enemies | Cannot marry |

### Birth

| Parameter | Value |
|-----------|-------|
| Base chance | 0.005/tick |
| Min age | 18 |
| Max age | 50 |
| Requirements | Has spouse, female agent |
| Effect | New agent created with inheritance from parents |

### Death (8 causes)

| Cause | Condition | Notes |
|-------|-----------|-------|
| Starvation | FOOD < 0.02 | Always fatal |
| Dehydration | WATER < 0.02 | Always fatal |
| Health failure | HEALTH < 0.02 | 50% dice roll |
| Sleep deprivation | insomnia > 0.05 AND 50+ ticks awake | 30% dice roll |
| Despair | happiness < 0.02 | 0.004/tick mortality rate |
| Existential | purpose_fulfillment < 0.1 | 0.001/tick death chance |
| Old age | elderly bracket | 0.001/tick elderly mortality |
| Economic hardship | unemployed + money < 50 + inflation | 0.001/tick |

### Inheritance

On death: `70%` of wealth passed to children (split equally).

---

## 14. Social Systems

### Reputation System

| Parameter | Value |
|-----------|-------|
| Natural decay | 0.001/tick |
| Crime penalty | −0.06 per crime + 0.02/tick cumulative |
| Good act bonus | +0.02 per act + 0.01/tick cumulative |
| Kill penalty | −0.30 (HARM_OTHER fatal) |
| Gossip spread | 10% chance per tick per nearby agent |

### Community System

| Parameter | Value |
|-----------|-------|
| Recluster interval | Every 10 ticks |
| Clustering method | BFS proximity on grid |
| Min community size | 3 agents |
| Max community size | 15 agents |
| Leader effects | Safety +0.1, reputation +0.02/tick |
| Creative bonus | Happiness +0.08 for creative agents |

### Inter-Community Tension

| Parameter | Value |
|-----------|-------|
| Base decay | 0.01/tick |
| Wealth gap weight | 0.3 |
| Proximity weight | 0.2 |
| Crime escalation | +0.1 per cross-community crime |
| Conflict threshold | 0.5 (property damage) |
| Hate crime threshold | 0.6 (violent events) |
| Gang recruitment | Activates at tension > 0.3 |

### Riot System

| Trigger | Value |
|---------|-------|
| Protest intensity | > 0.3 |
| AND (unlust | > 0.5 OR food < 0.3) |
| Join chance | 30% of eligible agents |
| Effect | Property damage, trust_in_govt drop |

### Gang System

| Parameter | Value |
|-----------|-------|
| Formation | 5+ eligible agents (POOR, unlust > 0.6, morality < 0.3) |
| Formation probability | 0.15/tick when conditions met |
| Actions | Extortion (40%), Fight (30%), Protect (30%) |
| Power formula | `sum(member_wealth × 0.01) + member_count × 0.1` |

### Rumor System

| Parameter | Value |
|-----------|-------|
| Spread requirement | dominance_urge ≥ 0.6 |
| Magnitude | 0.05–0.15 reputation penalty |
| Decay | 10% per tick |
| Propagation | 30% chance per contact, BFS depth 3 |

---

## 15. Environmental Events

### Event Types & Probabilities

| Event | Probability | Duration | Effect |
|-------|-------------|----------|--------|
| Famine | 15% (per cycle) | 10 ticks | food_availability → 0.15 (from 0.85) |
| Drought | 15% | 10 ticks | water_availability → 0.15 (from 0.90) |
| Abundance | 10% | — | food +0.15, water +0.10 |
| Mild shortage | 25% | 5 ticks | food/water −0.05 to −0.10 |
| Normal | 35% | — | No change |

### Event Mechanics

- Events cannot fire more often than every `ENV_CYCLE_MIN_INTERVAL(15)` ticks
- Maximum gap between events: `ENV_CYCLE_MAX_INTERVAL(40)` ticks
- Phase-in: Effects ramp over `ENV_EVENT_PHASE_IN(3)` ticks
- Regression: `ENV_REGRESSION_RATE(0.005)/tick` toward defaults (0.85/0.90)

### Crisis Multipliers

When `food_availability < 0.4`: food decay × 1.2
When `water_availability < 0.4`: water decay × 1.2

---

## 16. Self-Actualization

### Purpose System (Maslow Layer 5)

| Purpose | Effect When Fulfilled |
|---------|----------------------|
| creative_work | Creativity bonus, happiness +0.05 |
| community_lead | Reputation growth, social connections |
| knowledge | Skill acquisition |
| family | Family bond boost |
| wealth | Financial motivation |

| Parameter | Value |
|-----------|-------|
| Assignment chance | 0.05/tick |
| Fulfillment gain per relevant action | 0.02 |
| Fulfillment decay (idle) | 0.002/tick |
| Happiness bonus (fulfillment > 0.5) | 0.05 |
| Existential death chance | 0.001/tick when fulfillment < 0.1 |

### Political Career

| Parameter | Value |
|-----------|-------|
| Campaign eligibility | notoriety > 0.3, morality > 0.4, employed |
| Campaign effect | Notoriety +0.05, trust_in_govt +0.02 |
| Leader selection | Highest notoriety in community |
| Leader election interval | Every 50 ticks |
| Leader bonus | Safety +0.1 (global) |

### Creative Professions

| Profession | Min Creativity | Salary |
|------------|---------------|--------|
| ARTIST | > 0.7 | £45/tick |
| WRITER | > 0.7 | £55/tick |
| MUSICIAN | > 0.7 | £40/tick |
| COMMUNITY_LEADER | — | £70/tick |

### Hobby System

5 random hobby options assigned at birth: reading, gardening, crafting, sports, music.
- Effect: Happiness +0.03, unlust −0.02
- Always available (no conditions)

---

## 17. Media Engine

### News Generation (every 5 ticks)

| Category | Trigger Condition | Template |
|----------|------------------|----------|
| Crime | crime_rate > 0.12 | "Crime wave sweeps city" |
| Economic | economic_health < 0.3 | "Economic downturn reported" |
| Protest | protest_intensity > 0.15 | "Protests erupt across city" |
| Environment | food_availability < 0.5 | "Food shortage crisis" |
| Social | social_cohesion < 0.3 | "Community tensions rising" |
| General | — | "City report: {tick} entries recorded" |

### Fake News (15% chance when eligible)

3 templates: exaggerated crime, government cover-up, foreign enemy fabrication.

### Effects

- Negative news → trust_in_govt −0.02
- Positive news → trust_in_govt +0.01
- Fake news → trust_in_govt −0.03

### Parameters

| Parameter | Value |
|-----------|-------|
| MEDIA_SENSATIONALISM_BASE | 0.3 |
| MEDIA_TRUST_BASE | 0.6 |
| MEDIA_FAKE_NEWS_CHANCE | 0.15 |
| MEDIA_SENTIMENT_DECAY | 0.02/tick |

---

## 18. Memory System

### Memory Schema

```python
@dataclass
class Memory:
    tick: int          # When the memory was recorded
    agent_id: str      # Which agent this memory belongs to
    action: str        # Action taken
    description: str   # Human-readable description
    reasoning: str     # Agent's stated reasoning
    feeling: str       # Emotional state during action
    importance: float  # 0.0-1.0 (not yet used for pruning)
```

### Memory Collection (every tick, per agent)

Stored in `agent.memories: list[Memory]`. Max 50 entries (oldest pruned first).

### LLM Prompt Injection

When building agent decision prompts (for E2B model):
- Last 5 memories are injected as context
- Format: `"Memory {n}: At tick {t}, you took {action} because {reasoning}. You felt {feeling}."`

---

## 19. LLM Integration

### 3-Model Architecture

| Model | Type | Port | Temperature | Purpose | Max Tokens |
|-------|------|------|-------------|---------|------------|
| Gemma 4 E2B | Small decision | 8001 | 0.0 | Agent action selection | 64 |
| Gemma 4 26B A4B | MoE reasoning | 8002 | 0.2 | Moral dilemmas, negotiations | 256 |
| Gemma 4 31B | Dense | 8000 | 0.3 | Policy translation, governance, news | 512 |

### API Configuration

```
VLLM_BASE_URL_E2B=http://129.212.187.34:8001/v1
VLLM_BASE_URL_MOE_26B=http://129.212.187.34:8002/v1
VLLM_BASE_URL_DENSE_31B=http://129.212.187.34:8000/v1
```

### Failover Strategy

1. `is_available()` → returns True (always, to avoid blocking)
2. Each LLM call: 5s timeout, 0 retries
3. If server unreachable: returns `FALLBACK_RESPONSE` = `{"action":"work","reason":"vllm fallback","feeling":"neutral"}`
4. Deterministic engine runs regardless

### LLM Call Flow (per tick)

```
1. Stagger: 1/3 of agents evaluated (should_evaluate_this_tick)
2. For each evaluated agent:
   a. Check is_moral_dilemma() (5 conditions)
   b. Build prompt with memories + needs + emotions + world state
   c. If dilemma: send to 26B A4B (moral_reasoning)
   d. If normal: send to E2B (agent_decide)
   e. Parse JSON response
   f. Validate action
   g. Execute action
   h. Log to llm_log
3. Non-evaluated agents: use deterministic_fallback
4. Non-LLM agents: always use deterministic_fallback
```

### LLM Log Entry

```
{
  "tick": int,
  "agent_id": str,
  "model_type": "agent_decide" | "moral_reasoning",
  "action": str,
  "reason": str (truncated 200 chars),
  "feeling": str (truncated 100 chars)
}
```

---

## 20. API Endpoints

### Simulation

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/simulation/status` | — | `SimulationStatusDTO` |
| POST | `/simulation/start` | `SimulationStartRequestDTO` | `SimulationStatusDTO` |
| POST | `/simulation/tick` | — | `SimulationStateResponseDTO` |
| POST | `/simulation/tick-n` | `{"n": int}` | `SimulationStateResponseDTO` |
| POST | `/simulation/stop` | — | `{"status":"stopped"}` |
| POST | `/simulation/reset` | — | `{"status":"reset"}` |
| GET | `/simulation/state` | — | `SimulationStateResponseDTO` |
| POST | `/simulation/start_auto_run` | `{"active":bool,"interval_ms":int}` | `{"status":"auto_run_started"}` |
| POST | `/simulation/stop_auto_run` | — | `{"status":"stopped"}` |

### Agents

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/agents/` | `AgentListResponseDTO` |
| GET | `/agents/{id}` | `AgentDetailDTO` (including recent_actions, memories) |

### Policies

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/policies/` | — | `PolicyListResponseDTO` |
| POST | `/policies/` | `PolicyCreateRequestDTO` | `PolicyResponseDTO` |
| DELETE | `/policies/{id}` | — | `PolicyRevokeResponseDTO` |

### Governance

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | `/governance/apply` | `GovernanceChangeRequest` | `{status, changes, state}` |
| GET | `/governance/suggestions` | — | `{suggestions: [...]}` |

### Explain

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | `/explain` | `{"question": str}` | `{answer: str, evidence: dict, source: "rule"}` |

### Metrics

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/metrics/` | `MetricsResponseDTO` |
| GET | `/metrics/dashboard` | Full dashboard data |

### Saves

| Method | Endpoint | Request |
|--------|----------|---------|
| GET | `/saves/` | List saves |
| POST | `/saves/save` | Save current state |
| POST | `/saves/load/{id}` | Load saved state |

### Health

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/health` | `HealthResponse` |

### WebSocket

| Route | Protocol | Events |
|-------|----------|--------|
| `/ws` | WebSocket | `tick_completed`, `agent_acted` |

---

## 21. Dashboard UI Components

### Main Layout (dashboard.tsx)

```
┌──────────┬─────────────────────────────────────────────┐
│ Sidebar  │  Masthead (title + controls)                │
│          │  Dateline                                   │
│ Soc.crest│  StatStrip (6 metrics + Sparkline)          │
│          │  GaugeStrip (4 gauges)                      │
│ Register │                                              │
│  Overview│  ┌─────────────────┬────────────────────┐   │
│  Citizens│  │ Citizen Grid    │ Wealth Strat.     │   │
│  Gov.    │  │ (AgentGrid)     │ Governance Sliders│   │
│          │  └─────────────────┴────────────────────┘   │
│ Records  │  Explain Panel                               │
│  Economy │  ┌─────────────────┬────────────────────┐   │
│  Life    │  │ Model Log       │ Entry Log          │   │
│  Model   │  │ (LLM calls)     │ (Events)           │   │
│          │  └─────────────────┴────────────────────┘   │
│ vLLM:3   │                                              │
└──────────┴─────────────────────────────────────────────┘
```

### StatBox Component

**Data source:** `SimulationStateResponseDTO` fields
**Display:** Label, value, delta arrow (↑↓), embedded Sparkline mini-chart
**Color states:** Normal (default), Warning (ochre), Critical (oxblood)

### WorldGauge Component

**Data source:** Computed from simulation metrics
**Display:** Circular gauge with value, label, color
**Metrics:** ECON (gold), COHESION (moss), MORALITY (slate), SAFETY (ochre inverse)

### AgentGrid Component

**Data source:** `AgentSummaryDTO[]` from store
**Display:** Canvas-based 20×20 grid with pixel-art emotion sprites (face expressions)
**Emotion colors:** HAPPY=#8aac4a, NORMAL=#9a8a6a, SAD=#6d8aaa, ANGRY=#c54a3f, DESPAIR=#d4a04a
**Interactions:** Hover → pixel-face with gold ring, Click → opens AgentDetailPanel
**Dead agents:** Small hollow circles
**Background:** Cream parchment (#F4EFD8)

### AgentDetailPanel (slide-in)

**Data source:** `GET /agents/{id}` → `AgentDetailDTO` + `recent_actions`
**Display:** Persona, emotion dot, needs (key-value), traits, resources, recent actions list
**Position:** Fixed right panel, 420px wide

### ExplainPanel

**Data source:** `POST /explain` 
**Display:** 5 preset buttons (Crime, Economy, Deaths, Unlust, Food) + text input
**Response:** Natural language answer + evidence data

### Sparkline

**Data source:** `MetricsHistoryEntry[]` from store
**Display:** Mini line chart (72×20px), embedded in StatBox

### Governance Sliders

**Data source:** Local state → `POST /governance/apply`
**Controls:** Tax rate (0–50%), Food subsidy (0–50%), Welfare amount (0–50)
**Display:** Slider labels with values, apply button, status message

### Model Log

**Data source:** `store.llmLog`
**Display:** Reverse-chronological list of LLM calls
**Each entry:** tick, model badge (agent·e2b / moral·26b), reason, action

### Entry Log

**Data source:** `store.events`
**Display:** Reverse-chronological list of world events
**Colors:** crime=oxblood, env_event=ochre, marriage=moss, tick_completed=slate
**Format:** `t-n` relative timing

---

## 22. Store & State Management

### Zustand Store (simulationStore.ts)

**History tracking (max 100 entries each):**
- `metricsHistory: MetricsHistoryEntry[]` — tick, economic_health, social_cohesion, crime_rate, protest_intensity, unemployment_rate, avg_unlust, population
- `actionHistory: ActionHistoryEntry[]` — tick, action_counts
- `wealthStratified: WealthStratifiedEntry[]` — tick, poor, middle, rich

**Snapshot fields:** unlust, morality, food_availability, crime_rate, protest_intensity, unemployment_rate, tax_rate, welfare_enabled, welfare_amount, duration_ms, ai_calls, state_hash

**Events:** `events: SimulationEvent[]` (max 200)

**LLM Log:** `llmLog: Array<{tick, agent_id, model_type, action, reason, feeling}>` (max 200)

**Agent animation:** `agentAnimPositions`, `agentTargetPositions` — lerp interpolation for smooth grid movement

**Actions:** `appendTickData()`, `addEvent()`, `setAutoRun()`, `reset()`, `updateAnimPositions()`, `advanceAnimations()`

### API Service (api.ts)

Axios client with 120s timeout, interceptors for error handling.
Base URL: `http://localhost:8000/api/v1` (configurable via `NEXT_PUBLIC_API_URL`)

---

## 23. Default Constants Table

### Death Constants

| Constant | Value | What |
|----------|-------|------|
| FOOD_DEATH_THRESHOLD | 0.02 | Starvation death threshold |
| WATER_DEATH_THRESHOLD | 0.02 | Dehydration death threshold |
| HEALTH_DEATH_THRESHOLD | 0.02 | Health death threshold (50% dice) |
| DESPAIR_MORTALITY_RATE | 0.004 | Despair mortality per tick |
| AGE_MORTALITY_BASE | 0.0001 | Base mortality per tick |
| AGE_MORTALITY_ELDERLY | 0.001 | Additional elderly mortality |
| DEATH_INHERITANCE_FRACTION | 0.7 | Fraction passed to children |
| EXISTENTIAL_DEATH_CHANCE | 0.001 | Death from purpose < 0.1 |
| ECONOMIC_HARDSHIP_DEATH_RATE | 0.001 | Death from poverty |

### Emotion Constants

| Constant | Value | What |
|----------|-------|------|
| HAPPY_THRESHOLD | 0.65 | Happiness threshold |
| SAD_THRESHOLD | 0.35 | Sadness threshold |
| ANGRY_UNLUST_THRESHOLD | 0.45 | Anger unlust threshold |
| DESPAIR_UNLUST_THRESHOLD | 0.55 | Despair unlust threshold |
| SAD_TIMER | 2 | Sad state timer |
| ANGRY_TIMER | 3 | Anger state timer |
| DESPAIR_TIMER | 4 | Despair state timer |

### Unlust Weights

| Constant | Value |
|----------|-------|
| UNLUST_FOOD_WEIGHT | 0.28 |
| UNLUST_WATER_WEIGHT | 0.22 |
| UNLUST_SAFETY_WEIGHT | 0.20 |
| UNLUST_SOCIAL_WEIGHT | 0.12 |
| UNLUST_FINANCIAL_WEIGHT | 0.18 |
| UNLUST_FINANCIAL_DIVISOR | 600.0 |
| UNLUST_MORALITY_GATE | 0.38 |
| UNLUST_NEED_THRESHOLD | 0.70 |

### Economy Constants

| Constant | Value | What |
|----------|-------|------|
| BASE_FOOD_COST | 10.0 | Base food price |
| DEFAULT_TAX_RATE | 0.15 | Default tax |
| DEFAULT_WELFARE_AMOUNT | 8.0 | Base welfare |
| INFLATION_DECAY_RATE | 0.001 | Inflation decay/tick |
| DEBT_INTEREST_RATE | 0.05 | Per-tick debt interest |
| JOB_LOSS_RATE | 0.002 | Job loss probability |
| JOB_LOSS_ECON_SENSITIVITY | 2.0 | Economy job loss factor |

### Social Constants

| Constant | Value |
|----------|-------|
| REPUTATION_DECAY_RATE | 0.001 |
| GOSSIP_SPREAD_CHANCE | 0.1 |
| COMMUNITY_RECLUSTER_INTERVAL | 10 |
| COMMUNITY_MIN_SIZE | 3 |
| COMMUNITY_MAX_SIZE | 15 |
| RIOT_PROTEST_THRESHOLD | 0.3 |
| RIOT_UNLUST_THRESHOLD | 0.5 |
| RIOT_JOIN_CHANCE | 0.3 |
| GANG_FORMATION_MIN_MEMBERS | 5 |
| TENSION_BASE_DECAY | 0.01 |
| RUMOR_BFS_DEPTH | 3 |

### Environment Constants

| Constant | Value |
|----------|-------|
| ENV_FAMINE_CHANCE | 0.15 |
| ENV_DROUGHT_CHANCE | 0.15 |
| ENV_ABUNDANCE_CHANCE | 0.10 |
| ENV_MILD_SHORTAGE_CHANCE | 0.25 |
| ENV_CYCLE_MIN_INTERVAL | 15 |
| ENV_CYCLE_MAX_INTERVAL | 40 |
| ENV_FAMINE_DROP | 0.4 |
| ENV_DROUGHT_DROP | 0.4 |
| ENV_REGRESSION_RATE | 0.005 |

### Lifecycle Constants

| Constant | Value |
|----------|-------|
| AGE_PROGRESSION_INTERVAL | 0.1 |
| MARRIAGE_BASE_PROBABILITY | 0.05 |
| BIRTH_CHANCE_BASE | 0.005 |
| DEATH_INHERITANCE_FRACTION | 0.7 |
| MIN_ADULT_AGE_FOR_BIRTH | 18 |
| MAX_REPRODUCTION_AGE | 50 |

### Decision Constants

| Constant | Value |
|----------|-------|
| DECISION_STAGGER_INTERVAL | 3 |
| MORAL_DILEMMA_FOOD_THRESHOLD | 0.15 |
| MORAL_DILEMMA_MORALITY_THRESHOLD | 0.5 |
| MORAL_DILEMMA_UNLUST_THRESHOLD | 0.5 |
| SEEK_JOB_BASE_CHANCE | 0.08 |
| BEG_MAX_AMOUNT | 5.0 |
| STEAL_PERCENTAGE_CAP | 0.18 |
| STEAL_AMOUNT_CAP | 60.0 |

---

## 24. Calibration Values

> Tuned 2026-07-11 (v2 engine calibration). These values differ from the original
> v1 specification and were empirically determined through sweeps.

| Parameter | v1 Original | Calibrated | Reason |
|-----------|-------------|------------|--------|
| ANGRY_UNLUST_THRESHOLD | 0.58 | 0.45 | 0.58 unreachable (max unlust ~0.37) |
| DESPAIR_UNLUST_THRESHOLD | 0.82 | 0.55 | 0.82 unreachable |
| UNLUST_MORALITY_GATE | 0.58 | 0.38 | Must be < DESPAIR threshold |
| FOOD_DECAY_RATE | 0.018 | 0.012 | 0.018 × 1.15 = death in 23 ticks |
| WATER_DECAY_RATE | 0.010 | 0.008 | Water should last > food |
| SLEEP_DECAY_RATE | 0.04 | 0.02 | With recovery 0.02, net change ≈ 0 |
| AGE_MORTALITY_BASE | 0.001 | 0.0001 | 0.001 = 36% mortality per year |
| AGE_MORTALITY_ELDERLY | 0.008 | 0.001 | Combined was 97% per year |
| AGE_PROGRESSION_INTERVAL | 1.0 | 0.1 | 1.0 = 40→66 in 26 ticks |
| BIRTH_CHANCE_BASE | 0.0002 | 0.005 | 0.0002 = extinction, 0.005 = stable |
| WEALTH_POOR_THRESHOLD | 500 | 1000 | Better class stratification |
| WEALTH_MIDDLE_THRESHOLD | 5000 | 15000 | Better class stratification |
| HEALTH_DEATH | Always die | 50% dice | Less deterministic |
| SLEEP_DEATH | Always die | 30% dice | Less deterministic |
| HEALTH_DECAY | 0/tick | −0.001/tick | Aging/neglect matters |
| INFLATION_DECAY | Not present | 0.001/tick | Economy stabilization |
| LLM_TIMEOUT | 30s | 5s | Faster fallback |
| LLM_RETRIES | 2 | 0 | Faster fallback |

---

## Appendix: Key Code Files

| File | Purpose |
|------|---------|
| `shared/constants/defaults.py` | All constants and thresholds |
| `shared/constants/simulation_constants.py` | Salary ranges, job configs, beta params |
| `shared/types/enums.py` | All enumeration types |
| `shared/schemas/agent_state.py` | Agent state dataclasses |
| `shared/dto/simulation_dto.py` | Simulation response DTOs |
| `shared/dto/agent_dto.py` | Agent response DTOs |
| `simulation/engine/tick_loop.py` | Main tick orchestrator |
| `simulation/agents/decision_engine.py` | Softmax + deterministic fallback |
| `simulation/agents/needs_calculator.py` | Need decay, death checks |
| `simulation/agents/action_executor.py` | All 24 actions |
| `simulation/agents/emotion_engine.py` | Emotion state machine |
| `simulation/world/economy.py` | Rent, tax, welfare, inflation |
| `simulation/agents/lifecycle.py` | Birth, inheritance |
| `simulation/agents/memory_system.py` | Episodic memory collection |
| `simulation/events/media_engine.py` | News generation |
| `models/router/vllm_router.py` | 3-model LLM router |
| `models/router/vllm_config.py` | LLM configuration |
| `backend/app/main.py` | FastAPI app + router mounts |
| `backend/app/routers/explain.py` | Explain endpoint |
| `frontend/src/pages/dashboard.tsx` | Main dashboard UI |
| `frontend/src/store/simulationStore.ts` | Zustand state management |
| `frontend/src/services/api.ts` | Axios API client |
| `frontend/src/styles/globals.css` | Global CSS (ledger theme) |
| `frontend/src/types/api.ts` | TypeScript type definitions |
