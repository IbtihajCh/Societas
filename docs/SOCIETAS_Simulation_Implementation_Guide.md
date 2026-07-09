# SOCIETAS Simulation Engine — Complete Implementation Guide

**Version:** 2.0  
**Date:** 2026-07-09  
**Owner:** Simulation Engineer  
**Related:** [ADR-005](adr/ADR-005-simulation-implementation-architecture.md),
[Feature Spec](../vault/060-Features/simulation-engine-v1.md),
[Project Guide](SOCIETAS_Project_Guide.md)

**Hackathon:** AMD Developer Hackathon Act II — Unicorn Track  
**Goal:** Win using a hybrid deterministic+LLM governance simulation on AMD GPUs  
**Pitch:** *"Entirety of society, running on a single GPU"*  
**Timeline:** 2-3 days  
**Models:** Gemma 4 E2B (agent brains) + Gemma 4 26B A4B (moral reasoning) + Gemma 4 31B (governance advisor) on AMD GPU (198GB VRAM) via vLLM or Fireworks AI

---

> **How to use this document:** This is the single source of truth for implementing
> the simulation engine. Every formula, parameter, enum value, and code template is
> specified here. Subagents should follow this document strictly — do not invent
> formulas or parameters not defined here. If something is unclear, ask the lead
> agent before implementing.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Schema Extensions](#2-schema-extensions)
3. [Agent Parameters & Initialization](#3-agent-parameters--initialization)
4. [Needs System](#4-needs-system)
5. [Unlust Engine](#5-unlust-engine)
6. [Emotion System](#6-emotion-system)
7. [Happiness Score](#7-happiness-score)
8. [Decision Architecture](#8-decision-architecture)
9. [Action System](#9-action-system)
10. [Economy System](#10-economy-system)
11. [World System](#11-world-system)
12. [Policy System](#12-policy-system)
13. [Adler Comparison Engine](#13-adler-comparison-engine)
14. [Tick Loop](#14-tick-loop)
15. [Metrics & Events](#15-metrics--events)
16. [LLM Integration](#16-llm-integration)
17. [Determinism & Testing](#17-determinism--testing)
18. [Implementation Order](#18-implementation-order)
19. [File Manifest](#19-file-manifest)
20. [Code Templates](#20-code-templates)

---

## 1. Architecture Overview

### 1.1 Design Philosophy

> *Deterministic systems should model reality. LLMs should model human reasoning.*

The engine blends two layers — but unlike traditional hybrid systems, **the LLM IS
the agent's brain**. The deterministic engine handles the "physics" of the world
(needs decay, economy, emotions, death, grid). The LLM handles the **decision**:
"given my current life situation, what do I do?"

| Layer | Role | Components |
|---|---|---|
| **Layer 1 — Deterministic Engine** | Models reality: needs decay, Unlust, emotions, economy, grid, death, metrics | All math, all state updates, all RNG, state hash |
| **Layer 2 — AI (Gemma on AMD)** | Models human reasoning: agent decisions, moral reasoning, policy translation, governance advisory, news | 3 Gemma 4 models via vLLM, batched + staggered |

### 1.2 How They Blend — The E2B Hybrid

```
Every tick (deterministic):
  1. Apply policy effects
  2. Decay needs, compute Unlust, update emotions
  3. Welfare + rent
  4. For each agent (STAGGERED — 1/3 per tick, agent_id % 3):
       a. Build state prompt (full agent state as structured text)
       b. Is this a moral dilemma? → 26B A4B (thinking mode, ~5-15%)
       c. Otherwise → E2B brain (returns {action, feeling, reason})
       d. Validate LLM output (action exists? preconditions met?)
       e. If invalid → deterministic fallback (simplified priority queue)
       f. Execute action (deterministic state updates)
  5. Agents not scheduled this tick → continue last action
  6. Movement, death checks, world metrics, state hash
  7. Every 10 ticks: 31B governance advisory + news generation
```

**Key principle:** The world IS deterministic regardless. Needs decay, economy,
emotions, death — all computed by the engine. The ONLY thing the LLM decides is:
**"given my current state, what do I do next?"**

### 1.3 Three Gemma 4 Models — Multi-Tier AI

| Model | Role | VRAM (Q4 QAT) | Thinking Mode | Calls/Tick |
|---|---|---|---|---|
| **Gemma 4 E2B** | Agent brains — each agent reasons about their life | ~1 GB × 3 replicas = ~3 GB | No | ~27 (80 agents ÷ 3 stagger) |
| **Gemma 4 26B A4B** | Moral reasoning — ethical dilemmas with chain-of-thought | ~16.5 GB | Yes (`<\|think\|>`) | 1-2 (batched, ~5-15% of decisions) |
| **Gemma 4 31B** | Governance advisor + policy translation | ~20.3 GB | Yes (`<\|think\|>`) | 0.1 (every 10 ticks) + on-demand |
| **Total VRAM** | | **~40 GB of 198 GB** | | **~30 calls/tick** |

**Why this works:** E2B is fast (~1000+ tok/s batched on MI300X) and smart enough
for simple decisions ("I'm hungry, I have £12, buy food"). 26B A4B has ELO 1441
with thinking mode for genuine moral reasoning. 31B is the flagship (ELO 1452)
for policy analysis. All three run simultaneously on one GPU via vLLM multi-instance.

### 1.4 Staggered Call Strategy

Agents don't re-evaluate every tick — they re-evaluate every **3 ticks** and
continue their last action in between. This is both more realistic (humans don't
reconsider their life every second) and solves throughput:

| Agent Count | Calls/Tick (÷3) | Output Tokens/Tick | Time/Tick (3 E2B replicas) |
|---|---|---|---|
| 80 | ~27 | ~1,600 | ~0.5 sec |
| 150 | ~50 | ~3,000 | ~1 sec |
| 500 | ~167 | ~10,000 | ~3.3 sec |
| 1000 | ~333 | ~20,000 | ~6.7 sec |

Stagger assignment: `agent_tick_offset = agent_id % 3`. Agent re-evaluates when
`current_tick % 3 == agent_tick_offset`.

### 1.5 Deterministic Fallback

If LLM is unavailable or returns invalid output, a **simplified 3-level priority
queue** kicks in:

| Level | Check | Action |
|---|---|---|
| 1 — Critical | food < 0.08 OR water < 0.08 | buy_food (if money) / beg / steal (if not moral) |
| 2 — Survival | money < 120 OR unemployed | work / seek_job / beg |
| 3 — Default | none triggered | rest |

This is much simpler than the 7-level queue in v1.0 — it's a safety net, not the
primary decision-maker.

### 1.6 The Three Master Drives

Everything in the simulation is downstream of three forces:

| Drive | Source | Manifestation |
|---|---|---|
| Power & Status | Alfred Adler | Dominance urge, inferiority gap, jealousy, comparison, reputation-seeking |
| Material Resources | Karl Marx | Money, food, shelter — class determines life outcomes |
| Pleasure / Pain (Lust / Unlust) | Sigmund Freud | Unlust score drives irrational behavior. High Unlust bypasses morality. |

### 1.7 Everything Is Tweakable

All values flow from configuration — nothing is hardcoded. See Section 17 for the
complete 3-tier config system. Agent count, grid size, decay rates, economy
parameters, LLM model names, temperatures, thinking modes — all configurable.

---

## 2. Schema Extensions

All schema changes are in `shared/` to maintain the zero-dependency foundation principle.
The existing interfaces (`ISimulationEngine`, `IAgent`, etc.) are NOT changed — only the
data schemas and enums they reference.

### 2.1 Enum Replacements (`shared/types/enums.py`)

Replace existing enum values with Guide-aligned values. The existing values are stubs
that do not match the Project Guide.

```python
"""Shared type enumerations for SOCIETAS simulation."""

from enum import Enum, auto
from typing import List


class ActionType(Enum):
    """Actions an agent can perform. Aligned with Project Guide v1."""
    WORK = auto()
    BUY_FOOD = auto()
    REST = auto()
    SEEK_JOB = auto()
    BEG = auto()
    BEFRIEND = auto()
    CONSOLE = auto()
    ISOLATE = auto()
    SHARE = auto()
    STEAL = auto()
    HARM_OTHER = auto()
    PROTEST = auto()
    COMPLAIN = auto()
    COMPLY = auto()
    IDLE = auto()


class NeedType(Enum):
    """Maslow needs. 13 needs across 5 layers, aligned with Project Guide."""
    # Layer 1 - Physiological
    FOOD = auto()
    WATER = auto()
    SLEEP = auto()
    SEXUAL_TENSION = auto()
    # Layer 2 - Safety & Security
    SAFETY = auto()
    FINANCIAL_SECURITY = auto()
    SHELTER = auto()
    # Layer 3 - Love & Belonging
    SOCIAL_CONNECTION = auto()
    FAMILY_BOND = auto()
    ROMANTIC_BOND = auto()
    # Layer 4 - Esteem
    SELF_ESTEEM = auto()
    REPUTATION = auto()
    # Layer 5 - Self-Actualisation (purpose is derived, not a need enum)
    INFERIORITY_GAP = auto()


class EmotionType(Enum):
    """Discrete emotion states. 5 states with timers, aligned with Project Guide."""
    HAPPY = auto()
    NORMAL = auto()
    SAD = auto()
    ANGRY = auto()
    DESPAIR = auto()


class WealthClass(Enum):
    """Wealth classes. 3 classes per Project Guide."""
    POOR = auto()
    MIDDLE = auto()
    RICH = auto()


class Gender(Enum):
    """Agent gender. Affects marriage compatibility (v2)."""
    MALE = auto()
    FEMALE = auto()


class Culture(Enum):
    """Agent culture. Same-culture agents bond more easily."""
    A = auto()
    B = auto()
    C = auto()


class EducationLevel(Enum):
    """Education levels per Project Guide."""
    LOWER = auto()       # Level 0 - Primary
    SECONDARY = auto()   # Level 1
    HIGHER = auto()      # Level 2


class JobType(Enum):
    """Job types per Project Guide. 11 jobs + UNEMPLOYED."""
    ENGINEER = auto()
    COMPUTER_SCIENTIST = auto()
    PILOT = auto()
    DOCTOR = auto()
    THERAPIST = auto()
    MECHANIC = auto()
    ELECTRICIAN = auto()
    CONSTRUCTION_PLANNER = auto()
    CONSTRUCTION_WORKER = auto()
    CLEANER = auto()
    TAXI_DRIVER = auto()
    UNEMPLOYED = auto()


class PolicyCategory(Enum):
    """Policy categories (unchanged from existing)."""
    ECONOMIC = auto()
    SOCIAL = auto()
    ENVIRONMENTAL = auto()
    PUBLIC_ORDER = auto()
    EDUCATION = auto()
    HEALTHCARE = auto()
    INFRASTRUCTURE = auto()
    CULTURAL = auto()


class CrimeType(Enum):
    """Crime types (unchanged from existing)."""
    THEFT = auto()
    VIOLENCE = auto()
    FRAUD = auto()
    VANDALISM = auto()
    DRUG_OFFENSE = auto()
    TAX_EVASION = auto()
    CORRUPTION = auto()


class EmploymentStatus(Enum):
    """Employment status (unchanged from existing)."""
    EMPLOYED = auto()
    UNEMPLOYED = auto()
    STUDENT = auto()
    RETIRED = auto()
    UNABLE_TO_WORK = auto()


# Job-to-education mapping for the economy system
JOB_EDUCATION_REQUIREMENTS: dict = {
    JobType.ENGINEER: EducationLevel.HIGHER,
    JobType.COMPUTER_SCIENTIST: EducationLevel.HIGHER,
    JobType.PILOT: EducationLevel.HIGHER,
    JobType.DOCTOR: EducationLevel.HIGHER,
    JobType.THERAPIST: EducationLevel.HIGHER,
    JobType.MECHANIC: EducationLevel.SECONDARY,
    JobType.ELECTRICIAN: EducationLevel.SECONDARY,
    JobType.CONSTRUCTION_PLANNER: EducationLevel.SECONDARY,
    JobType.CONSTRUCTION_WORKER: EducationLevel.LOWER,
    JobType.CLEANER: EducationLevel.LOWER,
    JobType.TAXI_DRIVER: EducationLevel.LOWER,
}

# Jobs available per education level
JOBS_BY_EDUCATION: dict = {
    EducationLevel.HIGHER: [
        JobType.ENGINEER, JobType.COMPUTER_SCIENTIST, JobType.PILOT,
        JobType.DOCTOR, JobType.THERAPIST,
    ],
    EducationLevel.SECONDARY: [
        JobType.MECHANIC, JobType.ELECTRICIAN, JobType.CONSTRUCTION_PLANNER,
    ],
    EducationLevel.LOWER: [
        JobType.CONSTRUCTION_WORKER, JobType.CLEANER, JobType.TAXI_DRIVER,
    ],
}
```

### 2.2 AgentTraits (`shared/schemas/agent_state.py`)

```python
@dataclass
class AgentTraits:
    """
    Fixed innate traits, generated at birth from Beta distributions.

    Attributes:
        creativity: Beta(2,2). High = earns more, solves problems.
        morality: Beta(2,2). High = prosocial, never harms.
        anger_tendency: Beta(2,3) skewed low. High = quick to anger.
        extraversion: Beta(2,2). High = seeks social connection.
        ambition: Beta(2,2). High = pursues promotions, education.
        resilience: Beta(2,2). High = recovers faster from negative emotions.
        dominance_urge: Beta(2,2). High = triggered by Adler comparisons.
        risk_tolerance: Beta(2,2). High = risk-seeking (kept from existing).
    """
    creativity: float = 0.5
    morality: float = 0.5
    anger_tendency: float = 0.5
    extraversion: float = 0.5
    ambition: float = 0.5
    resilience: float = 0.5
    dominance_urge: float = 0.5
    risk_tolerance: float = 0.5
```

### 2.3 AgentNeeds

```python
@dataclass
class AgentNeeds:
    """
    Dynamic Maslow needs (0.0-1.0). 13 needs across 5 layers.
    Decays every tick. If Layer 1 need reaches zero, agent dies.
    """
    levels: dict = field(default_factory=dict)

    def get_level(self, need: NeedType) -> float:
        return self.levels.get(need, 0.5)

    def set_level(self, need: NeedType, value: float) -> None:
        self.levels[need] = max(0.0, min(1.0, value))

    def get_most_urgent_need(self) -> NeedType:
        if not self.levels:
            return NeedType.FOOD
        return min(self.levels, key=lambda n: self.levels[n])
```

### 2.4 AgentEmotions

```python
@dataclass
class AgentEmotions:
    """
    Discrete emotion state with hysteresis timer.

    Attributes:
        primary: Current emotion state (5 values).
        intensities: Emotion intensity dict (kept for compat).
        emotion_timer: Ticks remaining in current state (0 = re-evaluate).
        happiness_score: Composite 0.0-1.0 metric.
    """
    primary: EmotionType = EmotionType.NORMAL
    intensities: dict = field(default_factory=dict)
    emotion_timer: int = 0
    happiness_score: float = 0.5
```

### 2.5 AgentResources

```python
@dataclass
class AgentResources:
    """
    Agent resource holdings and socioeconomic status.

    Attributes:
        wealth: (existing, kept for compat) — alias for money.
        money: Current cash in £.
        base_salary: £/tick derived from job category.
        employed: Whether agent has a job.
        education: 0/1/2 education level.
        property: Whether agent owns shelter.
        health: 0.0-1.0, death at <=0.
        assets: (existing) List of asset names.
        skills: (existing) List of skill names.
    """
    wealth: float = 0.0
    money: float = 0.0
    base_salary: float = 0.0
    employed: bool = False
    education: EducationLevel = EducationLevel.LOWER
    property: bool = False
    health: float = 1.0
    assets: list = field(default_factory=list)
    skills: list = field(default_factory=list)
```

> **Note on `wealth` vs `money`**: The existing schema has `wealth`. The Guide uses
> `money`. We keep both: `money` is the canonical field; `wealth` is updated to
> mirror `money` for backward compatibility with backend/frontend code.

### 2.6 AgentState

```python
@dataclass
class AgentState:
    """
    Complete state representation of an autonomous agent.

    Extended with Project Guide fields. Existing fields preserved for compat.
    """
    id: AgentId
    persona: str = ""
    traits: AgentTraits = field(default_factory=AgentTraits)
    needs: AgentNeeds = field(default_factory=AgentNeeds)
    emotions: AgentEmotions = field(default_factory=AgentEmotions)
    resources: AgentResources = field(default_factory=AgentResources)
    decision_scores: AgentDecisionScores = field(default_factory=AgentDecisionScores)
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    wealth_class: WealthClass = WealthClass.POOR
    age: int = 0
    is_alive: bool = True
    location: str = "default"
    social_connections: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    # --- NEW: Project Guide fields ---
    gender: Gender = Gender.MALE
    culture: Culture = Culture.A
    born_tick: int = 0
    unlust: float = 0.0
    good_acts: int = 0
    crimes_committed: int = 0
    notoriety: float = 0.0
    trust_in_govt: float = 0.5
    protest_count: int = 0
    grid_x: int = 0
    grid_y: int = 0
    job_type: JobType = JobType.UNEMPLOYED
    spouse: object = None  # Optional[AgentId]
    enemies: list = field(default_factory=list)  # List[AgentId]
    community_id: object = None  # Optional[str]
    last_action: ActionType = ActionType.IDLE  # For staggered re-evaluation
    last_reasoning: str = ""  # Last LLM reasoning (explainability)
```

### 2.7 SimulationState

```python
@dataclass
class SimulationState:
    """World/environment state. Extended with Guide world variables."""
    time_step: TickNumber = TickNumber(0)
    population: int = 0
    economic_health: float = 0.5
    social_cohesion: float = 0.5
    environmental_quality: float = 0.5
    public_order: float = 0.5
    innovation_index: float = 0.5
    unlust: float = 0.0
    morality: float = 0.5
    economy: EconomyState = field(default_factory=EconomyState)
    crime: CrimeState = field(default_factory=CrimeState)
    needs: NeedsState = field(default_factory=NeedsState)
    psychology: PsychologyState = field(default_factory=PsychologyState)
    active_policy_ids: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    # --- NEW: Project Guide world variables ---
    food_availability: float = 1.0
    water_availability: float = 1.0
    crime_rate: float = 0.0
    protest_intensity: float = 0.0
    unemployment_rate: float = 0.12
    tax_rate: float = 0.20
    welfare_enabled: bool = False
    welfare_amount: float = 8.0
```

### 2.8 New Schema: ImpactDelta (`shared/schemas/policy.py`)

```python
@dataclass
class ImpactDelta:
    """
    Per-wealth-class impact deltas applied each tick by a policy.

    Range constraints (enforced by LLM prompt, validated at runtime):
        money_delta: -50 to +50 (£/tick)
        food_delta: -0.20 to +0.20
        safety_delta: -0.20 to +0.20
        social_delta: -0.10 to +0.10
        anger_spike: 0.0 to +0.30
        new_tax_rate: 0.05-0.60 (optional, None if no change)
        welfare_on: True/False (optional, None if no change)
        food_event: -0.40 to +0.40 (optional, None if no change)
        reasoning: 1 sentence LLM reasoning (audit log)
    """
    money_delta: float = 0.0
    food_delta: float = 0.0
    safety_delta: float = 0.0
    social_delta: float = 0.0
    anger_spike: float = 0.0
    new_tax_rate: object = None  # Optional[float]
    welfare_on: object = None    # Optional[bool]
    food_event: object = None    # Optional[float]
    reasoning: str = ""
```

### 2.9 GovernmentPolicy Extension

```python
@dataclass
class GovernmentPolicy:
    """Runtime wrapper for a Policy, tracking applied effects."""
    policy: Policy = field(default_factory=Policy)
    applied_effects: dict = field(default_factory=dict)
    affected_agents: int = 0
    total_cost: float = 0.0
    effectiveness: float = 0.0
    # --- NEW: per-wealth-class impact deltas ---
    impact_deltas: dict = field(default_factory=dict)  # Dict[WealthClass, ImpactDelta]
```

### 2.10 New Constants (`shared/constants/defaults.py`)

Add these constants to the existing file:

```python
# --- Guide constants ---
GRID_SIZE: int = 20
N_AGENTS: int = 80
INTERACTION_RADIUS: int = 2

# Need decay rates (per tick)
FOOD_DECAY: float = 0.018
WATER_DECAY: float = 0.014
SLEEP_DECAY: float = 0.010
SEXUAL_TENSION_BUILD: float = 0.008  # builds, not decays
SAFETY_DECAY: float = 0.004
SOCIAL_DECAY: float = 0.009
FAMILY_BOND_DECAY: float = 0.005
ROMANTIC_BOND_DECAY: float = 0.006
SELF_ESTEEM_DECAY: float = 0.003
REPUTATION_DECAY: float = 0.001

# Emotion thresholds
HAPPY_THRESHOLD: float = 0.65
SAD_THRESHOLD: float = 0.35
ANGRY_UNLUST: float = 0.58
DESPAIR_UNLUST: float = 0.82

# Economy
BASE_FOOD_COST: float = 6.0
BASE_TAX_RATE: float = 0.20
UNEMPLOYMENT_RATE: float = 0.12
WELFARE_AMOUNT: float = 8.0
STEAL_CAP: float = 60.0      # max stolen per theft
STEAL_PERCENT: float = 0.18   # 18% of victim's money

# Unlust weights (from Guide formula)
UNLUST_WEIGHT_FOOD: float = 0.28
UNLUST_WEIGHT_WATER: float = 0.22
UNLUST_WEIGHT_SAFETY: float = 0.20
UNLUST_WEIGHT_SOCIAL: float = 0.12
UNLUST_WEIGHT_MONEY: float = 0.18
UNLUST_MONEY_THRESHOLD: float = 600.0  # money/600 in formula

# Despair mortality
DESPAIR_MORTALITY_RATE: float = 0.004  # 0.4% per tick
```

### 2.11 New File: Salary Ranges (`shared/constants/simulation_constants.py`)

```python
"""Simulation constants: salary ranges, Beta params, wealth class config."""

from shared.types.enums import JobType, WealthClass, EducationLevel

# Annual salary ranges (£/year) per Project Guide
SALARY_RANGES: dict = {
    JobType.ENGINEER: (55000, 95000),
    JobType.COMPUTER_SCIENTIST: (60000, 110000),
    JobType.PILOT: (50000, 90000),
    JobType.DOCTOR: (70000, 130000),
    JobType.THERAPIST: (45000, 80000),
    JobType.MECHANIC: (25000, 45000),
    JobType.ELECTRICIAN: (28000, 50000),
    JobType.CONSTRUCTION_PLANNER: (30000, 55000),
    JobType.CONSTRUCTION_WORKER: (12000, 22000),
    JobType.CLEANER: (10000, 18000),
    JobType.TAXI_DRIVER: (11000, 20000),
}

# Wealth class initial money ranges
WEALTH_CLASS_MONEY_RANGES: dict = {
    WealthClass.POOR: (100, 800),
    WealthClass.MIDDLE: (2000, 8000),
    WealthClass.RICH: (15000, 80000),
}

# Initial wealth class distribution
WEALTH_CLASS_DISTRIBUTION: dict = {
    WealthClass.POOR: 0.50,
    WealthClass.MIDDLE: 0.35,
    WealthClass.RICH: 0.15,
}

# Education probability by wealth class
EDUCATION_BY_WEALTH: dict = {
    WealthClass.POOR: {
        EducationLevel.LOWER: 0.80,
        EducationLevel.SECONDARY: 0.15,
        EducationLevel.HIGHER: 0.05,
    },
    WealthClass.MIDDLE: {
        EducationLevel.LOWER: 0.20,
        EducationLevel.SECONDARY: 0.50,
        EducationLevel.HIGHER: 0.30,
    },
    WealthClass.RICH: {
        EducationLevel.LOWER: 0.05,
        EducationLevel.SECONDARY: 0.25,
        EducationLevel.HIGHER: 0.70,
    },
}

# Property ownership probability by wealth class
PROPERTY_OWNERSHIP: dict = {
    WealthClass.POOR: 0.20,
    WealthClass.MIDDLE: 0.60,
    WealthClass.RICH: 0.95,
}

# Rent cost per tick by wealth class (if no property)
RENT_COST: dict = {
    WealthClass.POOR: 2.0,
    WealthClass.MIDDLE: 5.0,
    WealthClass.RICH: 15.0,
}

# Beta distribution parameters for traits
BETA_PARAMS: dict = {
    "creativity": (2, 2),
    "morality": (2, 2),
    "anger_tendency": (2, 3),  # skewed low
    "extraversion": (2, 2),
    "ambition": (2, 2),
    "resilience": (2, 2),
    "dominance_urge": (2, 2),
    "risk_tolerance": (2, 2),
}

# Wealth class derivation thresholds
WEALTH_CLASS_THRESHOLDS: dict = {
    WealthClass.POOR: 1000,
    WealthClass.MIDDLE: 15000,
    # Above 15000 = RICH
}

# News generation interval
NEWS_INTERVAL_TICKS: int = 10
```

### 2.12 DeterministicRNG Extension (`shared/utilities/deterministic_rng.py`)

Add a `beta` method to the existing `DeterministicRNG` class:

```python
def beta(self, a: float, b: float) -> float:
    """Sample from a Beta distribution.

    Args:
        a: Alpha parameter.
        b: Beta parameter.

    Returns:
        A float in [0, 1) sampled from Beta(a, b).
    """
    return float(self._generator.beta(a, b))
```

---

## 3. Agent Parameters & Initialization

### 3.1 Identity (fixed at birth)

| Parameter | Type | How Initialized |
|---|---|---|
| `id` | int | Sequential from 0 |
| `gender` | Gender | RNG choice: 50% MALE, 50% FEMALE |
| `culture` | Culture | RNG choice: 33% A, 33% B, 34% C |
| `born_tick` | int | 0 (all agents start as adults in v1) |

### 3.2 Traits (fixed, Beta-distributed)

All traits generated via `DeterministicRNG` using numpy Beta distribution:

```python
def generate_traits(rng: DeterministicRNG) -> AgentTraits:
    """Generate Beta-distributed traits for a new agent."""
    return AgentTraits(
        creativity=rng.beta(2, 2),
        morality=rng.beta(2, 2),
        anger_tendency=rng.beta(2, 3),  # skewed low
        extraversion=rng.beta(2, 2),
        ambition=rng.beta(2, 2),
        resilience=rng.beta(2, 2),
        dominance_urge=rng.beta(2, 2),
        risk_tolerance=rng.beta(2, 2),
    )
```

**Why Beta(2,2)?** Gives a bell curve peaking at 0.5 — most agents are average with
fewer extremes, matching real human populations. Beta(2,3) for anger_tendency skews
low — most agents are slow to anger.

### 3.3 Socioeconomic Status (initial)

```python
def generate_socioeconomic(rng: DeterministicRNG) -> tuple:
    """Generate initial socioeconomic status.

    Returns:
        Tuple of (wealth_class, money, employed, education, property).
    """
    # Wealth class: 50% poor, 35% middle, 15% rich
    wealth_class = rng.weighted_choice(
        list(WEALTH_CLASS_DISTRIBUTION.keys()),
        weights=list(WEALTH_CLASS_DISTRIBUTION.values()),
    )

    # Money: range based on wealth class
    low, high = WEALTH_CLASS_MONEY_RANGES[wealth_class]
    money = rng.uniform(low, high)

    # Employment: 88% employed, 12% unemployed
    employed = rng.random() < (1.0 - UNEMPLOYMENT_RATE)

    # Education: probability by wealth class
    education = rng.weighted_choice(
        list(EDUCATION_BY_WEALTH[wealth_class].keys()),
        weights=list(EDUCATION_BY_WEALTH[wealth_class].values()),
    )

    # Property: probability by wealth class
    property_owned = rng.random() < PROPERTY_OWNERSHIP[wealth_class]

    return wealth_class, money, employed, education, property_owned
```

### 3.4 Needs (initial)

All needs start at moderately satisfied levels:

```python
def generate_needs(rng: DeterministicRNG, property_owned: bool) -> AgentNeeds:
    """Generate initial needs for a new agent."""
    needs = AgentNeeds()
    needs.set_level(NeedType.FOOD, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.WATER, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.SLEEP, rng.uniform(0.6, 0.9))
    needs.set_level(NeedType.SEXUAL_TENSION, 0.0)  # builds over time
    needs.set_level(NeedType.SAFETY, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.FINANCIAL_SECURITY, 0.5)  # derived from money
    needs.set_level(NeedType.SHELTER, 1.0 if property_owned else 0.3)
    needs.set_level(NeedType.SOCIAL_CONNECTION, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.FAMILY_BOND, 0.5)  # no family system in v1
    needs.set_level(NeedType.ROMANTIC_BOND, 0.0)  # no marriage in v1
    needs.set_level(NeedType.SELF_ESTEEM, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.REPUTATION, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.INFERIORITY_GAP, 0.0)  # computed on interaction
    return needs
```

### 3.5 Grid Position

```python
grid_x = rng.integers(0, GRID_SIZE)
grid_y = rng.integers(0, GRID_SIZE)
```

### 3.6 Complete Agent Factory

```python
def create_agent(agent_id: int, rng: DeterministicRNG) -> AgentState:
    """Create a complete agent with all v1 parameters."""
    traits = generate_traits(rng)
    wealth_class, money, employed, education, property_owned = generate_socioeconomic(rng)
    needs = generate_needs(rng, property_owned)

    # Assign job if employed
    job_type = JobType.UNEMPLOYED
    base_salary = 0.0
    if employed:
        job_type = assign_job_by_education(education, rng)
        base_salary = get_salary_for_job(job_type, rng)

    # Gender and culture
    gender = Gender.MALE if rng.random() < 0.5 else Gender.FEMALE
    culture = rng.choice([Culture.A, Culture.B, Culture.C])

    # Health
    health = rng.uniform(0.7, 1.0)

    return AgentState(
        id=AgentId(str(agent_id)),
        traits=traits,
        needs=needs,
        emotions=AgentEmotions(happiness_score=0.5),
        resources=AgentResources(
            money=money,
            wealth=money,  # mirror for compat
            base_salary=base_salary,
            employed=employed,
            education=education,
            property=property_owned,
            health=health,
        ),
        employment_status=EmploymentStatus.EMPLOYED if employed else EmploymentStatus.UNEMPLOYED,
        wealth_class=wealth_class,
        gender=gender,
        culture=culture,
        born_tick=0,
        grid_x=rng.integers(0, GRID_SIZE),
        grid_y=rng.integers(0, GRID_SIZE),
        job_type=job_type,
    )
```

---

## 4. Needs System

### 4.1 Decay Rates (per tick)

| Need | Decay Formula | Replenished By | Death if 0? |
|---|---|---|---|
| FOOD | `0.018 × scarcity_multiplier` | buy_food (+0.30), share, beg (+0.08) | YES |
| WATER | `0.014 × scarcity_multiplier` | buy_food (+0.20, includes water) | YES |
| SLEEP | `0.010` | rest (+0.30), auto partial (+0.05/tick) | No — worsens emotion |
| SEXUAL_TENSION | `+0.008` (builds, not decays) | Marriage (deferred v2) | No — contributes to Unlust |
| SAFETY | `0.004 + crime_pressure` | Community, police policy, befriend | No |
| FINANCIAL_SECURITY | Derived: `min(1.0, money / 600)` | Employment + savings | No |
| SHELTER | Boolean (property or not) | Property, welfare housing | No |
| SOCIAL_CONNECTION | `0.009 × extraversion_factor` | befriend (+0.12), console (+0.05), share (+0.05) | No |
| FAMILY_BOND | `0.005` | Family (deferred v2) | No |
| ROMANTIC_BOND | `0.006` | Marriage (deferred v2) | No |
| SELF_ESTEEM | `0.003` | Positive interactions, good acts, job satisfaction | No |
| REPUTATION | `0.001` (passive) | Good acts (+0.02 to +0.05), community | No |
| INFERIORITY_GAP | Computed on interaction | Downward comparison | No |

**Scarcity multiplier:** `scarcity_multiplier = 2.0 - food_availability`

**Crime pressure:** `crime_pressure = world.crime_rate × 0.01` (adds to safety decay)

**Extraversion factor:** `1.2 if extraversion > 0.5 else 0.8` (extraverts decay slower,
introverts need less baseline — simplified: extraverts' social decays at 1.2x rate
because they need more social input, introverts at 0.8x)

### 4.2 Code Template: Needs Decay

```python
def decay_needs(agent: AgentState, world: SimulationState, rng: DeterministicRNG) -> None:
    """Decay all needs for one tick based on Guide formulas."""
    scarcity = 2.0 - world.food_availability
    crime_pressure = world.crime_rate * 0.01

    needs = agent.needs

    # Layer 1 - Physiological
    needs.set_level(NeedType.FOOD, needs.get_level(NeedType.FOOD) - FOOD_DECAY * scarcity)
    needs.set_level(NeedType.WATER, needs.get_level(NeedType.WATER) - WATER_DECAY * scarcity)
    needs.set_level(NeedType.SLEEP, needs.get_level(NeedType.SLEEP) - SLEEP_DECAY + 0.05)  # auto partial
    needs.set_level(NeedType.SEXUAL_TENSION, needs.get_level(NeedType.SEXUAL_TENSION) + SEXUAL_TENSION_BUILD)

    # Layer 2 - Safety & Security
    needs.set_level(NeedType.SAFETY, needs.get_level(NeedType.SAFETY) - SAFETY_DECAY - crime_pressure)
    needs.set_level(NeedType.FINANCIAL_SECURITY, min(1.0, agent.resources.money / UNLUST_MONEY_THRESHOLD))
    # SHELTER is boolean (derived from property), no decay

    # Layer 3 - Love & Belonging
    extraversion_factor = 1.2 if agent.traits.extraversion > 0.5 else 0.8
    needs.set_level(NeedType.SOCIAL_CONNECTION,
                     needs.get_level(NeedType.SOCIAL_CONNECTION) - SOCIAL_DECAY * extraversion_factor)
    needs.set_level(NeedType.FAMILY_BOND, needs.get_level(NeedType.FAMILY_BOND) - FAMILY_BOND_DECAY)
    needs.set_level(NeedType.ROMANTIC_BOND, needs.get_level(NeedType.ROMANTIC_BOND) - ROMANTIC_BOND_DECAY)

    # Layer 4 - Esteem
    needs.set_level(NeedType.SELF_ESTEEM, needs.get_level(NeedType.SELF_ESTEEM) - SELF_ESTEEM_DECAY)
    needs.set_level(NeedType.REPUTATION, needs.get_level(NeedType.REPUTATION) - REPUTATION_DECAY)
    # INFERIORITY_GAP computed on interaction, no passive decay

    # Derive wealth class from money each tick
    agent.wealth_class = derive_wealth_class(agent.resources.money)
    # Keep wealth field in sync with money
    agent.resources.wealth = agent.resources.money
```

### 4.3 Death Conditions

An agent dies if ANY of:

```python
def check_death(agent: AgentState, rng: DeterministicRNG) -> bool:
    """Check if agent should die this tick."""
    if not agent.is_alive:
        return False

    # Starvation
    if agent.needs.get_level(NeedType.FOOD) <= 0.0:
        return True

    # Dehydration
    if agent.needs.get_level(NeedType.WATER) <= 0.0:
        return True

    # Health failure
    if agent.resources.health <= 0.0:
        return True

    # Despair mortality (0.4% per tick)
    if agent.emotions.primary == EmotionType.DESPAIR:
        if rng.random() < DESPAIR_MORTALITY_RATE:
            return True

    # Old age (v1: not implemented since all agents start as adults with no max_age)
    # Deferred to v2

    return False
```

### 4.4 Wealth Class Derivation

```python
def derive_wealth_class(money: float) -> WealthClass:
    """Derive wealth class from current money amount."""
    if money < 1000:
        return WealthClass.POOR
    elif money < 15000:
        return WealthClass.MIDDLE
    else:
        return WealthClass.RICH
```

---

## 5. Unlust Engine

### 5.1 Formula (exact from Guide)

```
unlust = (max(0, 0.5 - food)        × 0.28)
       + (max(0, 0.5 - water)       × 0.22)
       + (max(0, 0.5 - safety)      × 0.20)
       + (max(0, 0.5 - social)      × 0.12)
       + (max(0, 1.0 - (money/600)) × 0.18)
```

Only counts **deficit below 0.5** — measures how far below satisfactory each need is.
Range: 0.0-1.0.

### 5.2 Code Template

```python
def compute_unlust(agent: AgentState) -> float:
    """Compute the Freudian Unlust score (0.0-1.0).

    Only counts deficit below 0.5 for each need.
    Money deficit is relative to the 600 threshold.

    Args:
        agent: The agent to compute Unlust for.

    Returns:
        Unlust score in [0.0, 1.0].
    """
    food = agent.needs.get_level(NeedType.FOOD)
    water = agent.needs.get_level(NeedType.WATER)
    safety = agent.needs.get_level(NeedType.SAFETY)
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    money_ratio = min(1.0, agent.resources.money / UNLUST_MONEY_THRESHOLD)

    unlust = (
        max(0.0, 0.5 - food) * UNLUST_WEIGHT_FOOD
        + max(0.0, 0.5 - water) * UNLUST_WEIGHT_WATER
        + max(0.0, 0.5 - safety) * UNLUST_WEIGHT_SAFETY
        + max(0.0, 0.5 - social) * UNLUST_WEIGHT_SOCIAL
        + max(0.0, 1.0 - money_ratio) * UNLUST_WEIGHT_MONEY
    )

    return min(1.0, max(0.0, unlust))
```

### 5.3 Unlust Ranges & Behavioral Effects

| Unlust Range | State | Effect on Behavior | Morality Applied? |
|---|---|---|---|
| 0.0 - 0.29 | Content | Rational decisions, prosocial available | Fully |
| 0.3 - 0.57 | Stressed | Emotional decisions dominate | Partially |
| 0.58 - 0.81 | Driven | Base instincts, anger/fear control, Thanatos begins | Only if morality > 0.6 |
| 0.82 - 1.0 | Desperate | Any action possible, morality bypassed, death risk | No |

### 5.4 Morality Gate

```python
def morality_active(unlust: float, morality: float) -> bool:
    """Check if morality gate is active for this agent.

    Args:
        unlust: Current Unlust score (0.0-1.0).
        morality: Agent's morality trait (0.0-1.0).

    Returns:
        True if morality should gate criminal/harmful actions.
    """
    if unlust < ANGRY_UNLUST:          # < 0.58
        return True                      # Fully moral
    elif unlust < DESPAIR_UNLUST:      # 0.58 - 0.82
        return morality > 0.6            # Partial — only if high morality
    else:                              # > 0.82
        return False                     # Morality completely bypassed
```

### 5.5 Thanatos Activation

When `unlust > 0.65 AND not morality_active()`: Thanatos drive activates, unlocking
`harm_other` and `steal` actions even if not at critical survival priority.

---

## 6. Emotion System

### 6.1 Five Emotion States

| Emotion | Trigger Condition | Timer (ticks) | Effects |
|---|---|---|---|
| HAPPY | happiness_score > 0.65 | None (exits when score drops) | Productivity +20%, creativity +30%, social +40% |
| NORMAL | 0.35 ≤ happiness_score ≤ 0.65 (default) | None | Baseline |
| SAD | happiness_score < 0.35 | 2 | Productivity -30%, creativity -20%, social -30% |
| ANGRY | unlust > 0.58 AND anger_tendency > 0.4 | 3 | Protest/fight/harm available, morality gate weakened |
| DESPAIR | unlust > 0.82 | 4 | Isolates, productivity near zero, 0.4%/tick death risk |

### 6.2 State Machine Code Template

```python
def update_emotion(agent: AgentState, rng: DeterministicRNG) -> None:
    """Update the agent's emotion state machine.

    Uses hysteresis: once in a state with a timer, the agent is locked
    until the timer expires. Resilience shortens the timer.
    """
    emotions = agent.emotions

    # If timer active, decrement and stay in current state
    if emotions.emotion_timer > 0:
        emotions.emotion_timer -= 1
        return  # Stay in current state

    # Re-evaluate (timer expired or was 0)
    unlust = agent.unlust
    happiness = emotions.happiness_score
    anger_tendency = agent.traits.anger_tendency
    resilience = agent.traits.resilience

    # Priority: despair > angry > sad > happy > normal
    if unlust > DESPAIR_UNLUST:  # 0.82
        emotions.primary = EmotionType.DESPAIR
        base_timer = 4
        emotions.emotion_timer = max(1, int(base_timer * (1.0 - resilience * 0.5)))
    elif unlust > ANGRY_UNLUST and anger_tendency > 0.4:  # 0.58
        emotions.primary = EmotionType.ANGRY
        base_timer = 3
        emotions.emotion_timer = max(1, int(base_timer * (1.0 - resilience * 0.5)))
    elif happiness < SAD_THRESHOLD:  # 0.35
        emotions.primary = EmotionType.SAD
        base_timer = 2
        emotions.emotion_timer = max(1, int(base_timer * (1.0 - resilience * 0.5)))
    elif happiness > HAPPY_THRESHOLD:  # 0.65
        emotions.primary = EmotionType.HAPPY
        emotions.emotion_timer = 0  # No timer — exits when score drops
    else:
        emotions.primary = EmotionType.NORMAL
        emotions.emotion_timer = 0
```

### 6.3 Resilience Effect on Timer

```
timer = base_timer × (1.0 - resilience × 0.5)
```

- `resilience=1.0` → timer halved
- `resilience=0.0` → full timer
- `resilience=0.5` → 75% of timer

### 6.4 Sleep as Emotional Reset

```python
def apply_sleep_reset(agent: AgentState) -> None:
    """Apply sleep-based emotional reset.

    Agents with unmet needs sleep less (insomnia), meaning
    negative states persist longer.
    """
    sleep_quality = (
        agent.needs.get_level(NeedType.SAFETY)
        * (1.0 - agent.unlust)
        * agent.traits.resilience
    )

    if sleep_quality > 0.5:
        # Good sleep — reset to normal immediately
        agent.emotions.primary = EmotionType.NORMAL
        agent.emotions.emotion_timer = 0
    elif sleep_quality > 0.3:
        # Moderate sleep — halve the timer
        agent.emotions.emotion_timer = agent.emotions.emotion_timer // 2
    # else: insomnia, no reset
```

### 6.5 Emotion Productivity Modifiers

```python
def emotion_productivity_mod(emotion: EmotionType) -> float:
    """Return the productivity multiplier for an emotion state."""
    return {
        EmotionType.HAPPY: 1.20,
        EmotionType.NORMAL: 1.00,
        EmotionType.SAD: 0.70,
        EmotionType.ANGRY: 0.90,
        EmotionType.DESPAIR: 0.40,
    }.get(emotion, 1.0)


def emotion_creativity_mod(emotion: EmotionType) -> float:
    """Return the creativity multiplier for an emotion state."""
    return {
        EmotionType.HAPPY: 1.30,
        EmotionType.NORMAL: 1.00,
        EmotionType.SAD: 0.80,
        EmotionType.ANGRY: 0.90,
        EmotionType.DESPAIR: 0.50,
    }.get(emotion, 1.0)


def emotion_social_mod(emotion: EmotionType) -> float:
    """Return the social action multiplier for an emotion state."""
    return {
        EmotionType.HAPPY: 1.40,
        EmotionType.NORMAL: 1.00,
        EmotionType.SAD: 0.70,
        EmotionType.ANGRY: 0.50,  # harmful interactions only
        EmotionType.DESPAIR: 0.20,  # isolation only
    }.get(emotion, 1.0)
```

### 6.6 Emotion Productivity Table Summary

| Emotion | Productivity | Creativity | Social |
|---|---|---|---|
| HAPPY | ×1.20 | ×1.30 | ×1.40 |
| NORMAL | ×1.00 | ×1.00 | ×1.00 |
| SAD | ×0.70 | ×0.80 | ×0.70 |
| ANGRY | ×0.90 | ×0.90 | ×0.50 (harmful only) |
| DESPAIR | ×0.40 | ×0.50 | ×0.20 (isolation only) |

---

## 7. Happiness Score

The Guide references `happiness_score` but does not define it. This formula is derived
from the Guide's context — a weighted sum of need satisfaction, Unlust inverse, health,
and employment:

```python
def compute_happiness(agent: AgentState) -> float:
    """Compute the composite happiness score (0.0-1.0).

    Weights reflect Maslow priority — physiological needs weighted highest,
    health is significant, Unlust inverse is a major factor.

    Args:
        agent: The agent to compute happiness for.

    Returns:
        Happiness score in [0.0, 1.0].
    """
    needs = agent.needs

    score = (
        needs.get_level(NeedType.FOOD) * 0.11
        + needs.get_level(NeedType.WATER) * 0.09
        + needs.get_level(NeedType.SAFETY) * 0.09
        + needs.get_level(NeedType.SOCIAL_CONNECTION) * 0.09
        + needs.get_level(NeedType.SLEEP) * 0.08
        + needs.get_level(NeedType.SELF_ESTEEM) * 0.08
        + needs.get_level(NeedType.FINANCIAL_SECURITY) * 0.08
        + agent.resources.health * 0.13
        + needs.get_level(NeedType.REPUTATION) * 0.05
        + (1.0 - agent.unlust) * 0.15
        + (0.05 if agent.resources.employed else 0.0)
    )

    return min(1.0, max(0.0, score))
```

**Weight rationale:**
- Physiological (food+water+sleep = 0.28) — highest, core survival
- Safety/Security (safety+financial = 0.17) — layer 2
- Social (social+reputation = 0.14) — layer 3/4
- Health (0.13) — direct wellbeing
- Unlust inverse (0.15) — Freudian dissatisfaction inverse
- Employment bonus (0.05) — social/safety

*Weights sum to 1.05 when employed; the excess is clamped to 1.0.*

---

## 8. Decision Architecture — E2B Hybrid

### 8.1 Overview

The decision-making is handled by **Gemma 4 E2B** — each agent's "brain." The
deterministic engine computes the agent's full state (needs, unlust, emotions,
economy, nearby agents) and sends it as a structured prompt. E2B returns
`{action, feeling, reason}`. The engine validates the action and executes it.

```
Agent State (deterministic)
    → Build structured prompt (~200 tokens)
    → Moral dilemma check (deterministic)
        → YES: 26B A4B with thinking mode (chain-of-thought reasoning)
        → NO: E2B brain (fast, simple reasoning)
    → Parse LLM JSON response
    → Validate action (exists? preconditions met?)
        → INVALID: deterministic fallback (3-level priority queue)
        → VALID: execute action
    → Execute action (deterministic state updates)
    → Store reasoning in AgentActionResult.metadata (explainability trace)
```

### 8.2 Staggered Re-Evaluation

Agents re-evaluate their decision every **3 ticks**, not every tick. Between
re-evaluations, they continue their last action. Stagger assignment:

```python
def should_evaluate_this_tick(agent: AgentState, current_tick: int) -> bool:
    """Check if this agent should re-evaluate its decision this tick.

    Agents are staggered so only 1/3 call the LLM per tick.
    """
    return current_tick % 3 == int(agent.id) % 3
```

Agents that are NOT scheduled this tick continue their last action:
```python
if not should_evaluate_this_tick(agent, tick_num):
    if agent.last_action != ActionType.IDLE:
        execute_action(agent, agent.last_action, world, all_agents, rng)
    continue
```

### 8.3 Agent State Prompt (for E2B)

The prompt must be compact (~200 input tokens) and structured so E2B can parse it:

```python
def build_agent_prompt(agent: AgentState, world: SimulationState,
                       nearby_counts: dict) -> str:
    """Build a structured prompt for the E2B agent brain.

    Includes ALL factors the agent should consider — even slight trait differences
    matter. The LLM sees the full picture.
    """
    needs = agent.needs
    traits = agent.traits

    prompt = f"""You are a person in a society simulation. Your situation:
hunger={needs.get_level(NeedType.FOOD):.2f} water={needs.get_level(NeedType.WATER):.2f}
sleep={needs.get_level(NeedType.SLEEP):.2f} safety={needs.get_level(NeedType.SAFETY):.2f}
social={needs.get_level(NeedType.SOCIAL_CONNECTION):.2f} esteem={needs.get_level(NeedType.SELF_ESTEEM):.2f}
money={agent.resources.money:.0f} employed={agent.resources.employed} job={agent.job_type.name}
mood={agent.emotions.primary.name.lower()} happiness={agent.emotions.happiness_score:.2f}
unlust={agent.unlust:.2f} health={agent.resources.health:.2f} reputation={needs.get_level(NeedType.REPUTATION):.2f}
morality={traits.morality:.2f} anger={traits.anger_tendency:.2f} ambition={traits.ambition:.2f}
extraversion={traits.extraversion:.2f} creativity={traits.creativity:.2f} resilience={traits.resilience:.2f}
dominance={traits.dominance_urge:.2f} risk={traits.risk_tolerance:.2f}
trust_govt={agent.trust_in_govt:.2f} crimes={agent.crimes_committed} good_acts={agent.good_acts}
nearby={nearby_counts['agents']} protesters_near={nearby_counts['protesters']} needy_near={nearby_counts['needy']}
tax_rate={world.tax_rate:.2f} welfare={world.welfare_enabled} food_avail={world.food_availability:.2f}

What do you do? Choose ONE:
work, buy_food, rest, seek_job, beg, befriend, console, isolate,
share, steal, harm_other, protest, complain, comply, idle

Respond EXACTLY: {{"action":"...","feeling":"...","reason":"one sentence"}}"""
    return prompt
```

**Key design choice:** Every trait and need is included with 2 decimal places. This
means even a `morality=0.52` vs `morality=0.48` difference is visible to E2B. The
LLM considers ALL factors — even slight changes in certain traits affect the decision.

### 8.4 LLM Response Parsing & Validation

```python
def parse_llm_response(response_text: str) -> dict | None:
    """Parse the LLM's JSON response.

    Expected format: {"action":"buy_food","feeling":"hungry","reason":"..."}

    Returns:
        Parsed dict if valid, None if unparseable.
    """
    import json
    try:
        # Extract JSON from response (E2B may add extra text)
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        data = json.loads(response_text[start:end])
        if "action" not in data:
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None


def validate_action(agent: AgentState, action_name: str,
                    world: SimulationState) -> ActionType | None:
    """Validate that the LLM-selected action is legal for this agent.

    Returns:
        ActionType if valid, None if invalid or unknown.
    """
    # Map string to enum (case-insensitive)
    action_map = {a.name.lower(): a for a in ActionType}
    action = action_map.get(action_name.lower().strip())
    if action is None:
        return None

    # Check preconditions
    if action == ActionType.BUY_FOOD:
        food_cost = BASE_FOOD_COST * (2.0 - world.food_availability)
        if agent.resources.money < food_cost:
            return None  # Can't afford food

    if action == ActionType.WORK and not agent.resources.employed:
        return None  # Can't work if unemployed

    if action == ActionType.SEEK_JOB and agent.resources.employed:
        return None  # Already employed

    if action in (ActionType.STEAL, ActionType.HARM_OTHER):
        # Check morality gate — but allow if Unlust has overridden morality
        if morality_active(agent.unlust, agent.traits.morality):
            return None  # Morality prevents this action

    return action
```

### 8.5 Moral Dilemma Detection

The deterministic engine flags certain situations as **moral dilemmas** — these
are routed to the 26B A4B model with thinking mode for deeper reasoning:

```python
def is_moral_dilemma(agent: AgentState, world: SimulationState) -> bool:
    """Check if this agent's situation constitutes a moral dilemma.

    Moral dilemmas are situations where simple reasoning is insufficient —
    the agent faces a genuine ethical conflict that benefits from
    chain-of-thought reasoning.
    """
    unlust = agent.unlust
    morality = agent.traits.morality

    # Dilemma 1: Starving but moral — steal to survive vs uphold values
    food = agent.needs.get_level(NeedType.FOOD)
    if food < 0.15 and morality > 0.5 and unlust > 0.5:
        return True

    # Dilemma 2: Angry but high morality — lash out vs restrain
    if (agent.emotions.primary == EmotionType.ANGRY
            and morality > 0.6
            and unlust > 0.58):
        return True

    # Dilemma 3: Despair with resources — give up vs persevere
    if (agent.emotions.primary == EmotionType.DESPAIR
            and agent.resources.money > 100):
        return True

    # Dilemma 4: High unlust + high dominance — power grab vs accept position
    if unlust > 0.65 and agent.traits.dominance_urge > 0.7:
        return True

    # Dilemma 5: Financial crisis with family/social bonds
    if (agent.resources.money < 50
            and agent.needs.get_level(NeedType.SOCIAL_CONNECTION) > 0.5
            and agent.social_connections):
        return True

    return False
```

### 8.6 Moral Reasoning Prompt (for 26B A4B with thinking mode)

When a moral dilemma is detected, the prompt is richer and includes the `<|think|>`
token for chain-of-thought reasoning:

```python
def build_moral_dilemma_prompt(agent: AgentState, world: SimulationState,
                               nearby_counts: dict) -> str:
    """Build a prompt for the 26B A4B moral reasoning model.

    Uses thinking mode for chain-of-thought reasoning.
    """
    return f"""<|think|>
You are a person facing a moral dilemma in a society simulation.

Your situation:
- Hunger: {agent.needs.get_level(NeedType.FOOD):.2f} (0=starving, 1=full)
- Money: £{agent.resources.money:.0f}
- Morality: {agent.traits.morality:.2f} (0=selfish, 1=saintly)
- Unlust: {agent.unlust:.2f} (0=content, 1=desperate)
- Emotion: {agent.emotions.primary.name.lower()}
- Anger tendency: {agent.traits.anger_tendency:.2f}
- Resilience: {agent.traits.resilience:.2f}
- Social connections: {len(agent.social_connections)} people
- Trust in government: {agent.trust_in_govt:.2f}
- Nearby people: {nearby_counts['agents']}, protesters: {nearby_counts['protesters']}
- World: tax={world.tax_rate:.0%}, food_avail={world.food_availability:.0%}, welfare={'on' if world.welfare_enabled else 'off'}

Think carefully about what this person would actually do, given their personality
and situation. Consider their moral values, their desperation, their relationships,
and the social context. What is the RIGHT choice for THIS person?

Choose ONE action: work, buy_food, rest, seek_job, beg, befriend, console, isolate,
share, steal, harm_other, protest, complain, comply, idle

Respond EXACTLY: {{"action":"...","feeling":"...","reason":"2-3 sentences explaining the moral reasoning"}}"""
```

### 8.7 Deterministic Fallback (3-Level Priority Queue)

When LLM is unavailable or returns invalid output:

```python
def deterministic_fallback(agent: AgentState, world: SimulationState,
                           rng: DeterministicRNG) -> ActionType:
    """Simplified 3-level priority queue for when LLM is unavailable.

    This is a safety net — much simpler than the 7-level queue.
    The LLM is the primary decision-maker.
    """
    food = agent.needs.get_level(NeedType.FOOD)
    water = agent.needs.get_level(NeedType.WATER)
    money = agent.resources.money
    is_moral = morality_active(agent.unlust, agent.traits.morality)

    # Level 1 — Critical Survival
    if food < 0.08 or water < 0.08:
        food_cost = BASE_FOOD_COST * (2.0 - world.food_availability)
        if money >= food_cost:
            return ActionType.BUY_FOOD
        elif not is_moral:
            return ActionType.STEAL
        else:
            return ActionType.BEG

    # Level 2 — Employment / Money
    if not agent.resources.employed:
        return ActionType.SEEK_JOB
    if money < 120:
        return ActionType.WORK if agent.resources.employed else ActionType.BEG

    # Level 3 — Default
    if agent.emotions.primary == EmotionType.DESPAIR:
        return ActionType.ISOLATE
    if agent.emotions.primary == EmotionType.ANGRY and not is_moral:
        return ActionType.PROTEST
    return ActionType.WORK if agent.resources.employed else ActionType.REST
```

### 8.8 Decision Flow Code Template

```python
async def make_decision(
    agent: AgentState,
    world: SimulationState,
    all_agents: list,
    ai_router: IAIRouter,
    rng: DeterministicRNG,
) -> tuple[ActionType, dict]:
    """Make a decision for an agent using the E2B hybrid architecture.

    Returns:
        Tuple of (selected action, metadata dict with reasoning trace).
    """
    nearby_counts = compute_nearby_counts(agent, all_agents)

    # Check for moral dilemma → 26B A4B
    if is_moral_dilemma(agent, world):
        if ai_router.is_available():
            prompt = build_moral_dilemma_prompt(agent, world, nearby_counts)
            try:
                response_text = await ai_router.moral_reasoning(prompt)
                parsed = parse_llm_response(response_text)
                if parsed:
                    action = validate_action(agent, parsed["action"], world)
                    if action:
                        return action, {
                            "source": "26b_moral_reasoning",
                            "thinking_mode": True,
                            "reasoning": parsed.get("reason", ""),
                            "feeling": parsed.get("feeling", ""),
                        }
            except Exception:
                pass  # Fall through to E2B or fallback

    # Standard decision → E2B brain
    if ai_router.is_available():
        prompt = build_agent_prompt(agent, world, nearby_counts)
        try:
            response_text = await ai_router.agent_decide(prompt)
            parsed = parse_llm_response(response_text)
            if parsed:
                action = validate_action(agent, parsed["action"], world)
                if action:
                    return action, {
                        "source": "e2b_brain",
                        "thinking_mode": False,
                        "reasoning": parsed.get("reason", ""),
                        "feeling": parsed.get("feeling", ""),
                    }
        except Exception:
            pass  # Fall through to deterministic

    # Deterministic fallback
    action = deterministic_fallback(agent, world, rng)
    return action, {
        "source": "deterministic_fallback",
        "thinking_mode": False,
        "reasoning": "LLM unavailable or invalid response",
        "feeling": agent.emotions.primary.name.lower(),
    }
```

### 8.9 Explainability Trace

Every decision records:
- **source**: `e2b_brain` / `26b_moral_reasoning` / `deterministic_fallback`
- **thinking_mode**: whether chain-of-thought was used
- **reasoning**: the LLM's stated reason (or fallback explanation)
- **feeling**: the agent's self-reported emotional state

This is stored in `AgentActionResult.metadata` and made available to the dashboard.

---

## 9. Action System

### 9.1 Action Definitions (14 actions)

| Action | Preconditions | Primary Effect | Side Effects |
|---|---|---|---|
| **WORK** | employed == True | money += salary × (1-tax) × prod_mod | social += 0.015 |
| **BUY_FOOD** | money >= food_cost | food += 0.30, water += 0.20 | money -= food_cost |
| **REST** | sleep < 0.2 OR despair | sleep += 0.30 | May break angry state (30% chance) |
| **SEEK_JOB** | employed == False | Chance to become employed | None |
| **BEG** | money < 50 | Small money from nearby generous agents | reputation -= 0.02 |
| **BEFRIEND** | other not enemy, rep > 0.25 | social += 0.12 (self) | social += 0.10 (other), Adler |
| **CONSOLE** | morality > 0.55, nearby sad | social += 0.05, good_acts++ | other: social += 0.08, timer reset |
| **ISOLATE** | emotion == DESPAIR | social -= 0.02 | None |
| **SHARE** | morality > 0.68, money > 250 | money -= 6%, happiness += 0.04 | other: money + food boost |
| **STEAL** | morality inactive, nearby agent | money += stolen, food += 0.08, crimes++ | victim: money -=, safety -=, angry |
| **HARM_OTHER** | unlust > 0.65, morality inactive | crimes++, reputation -= 0.10 | victim: safety -= 0.18, angry |
| **PROTEST** | unlust > 0.45, sad/angry | protest_count++, social += 0.06 | Spreads 25% to nearby |
| **COMPLAIN** | trust_in_govt < 0.4 | reputation += 0.02 | Spreads discontent (mild) |
| **COMPLY** | trust_in_govt > 0.6 | Absorbs policy effect | None |
| **IDLE** | (fallback) | None | None |

### 9.2 Action Execution Code Template

```python
def execute_action(
    agent: AgentState,
    action: ActionType,
    world: SimulationState,
    all_agents: list,
    rng: DeterministicRNG,
) -> AgentActionResult:
    """Execute a selected action and return the result.

    Args:
        agent: The agent performing the action.
        action: The action to execute.
        world: Current world state.
        all_agents: All living agents (for interactions).
        rng: Deterministic RNG.

    Returns:
        AgentActionResult with action, outcome, and score_delta.
    """
    result = AgentActionResult(
        agent_id=agent.id,
        action=action.name,
        outcome="",
        score_delta=0.0,
    )

    if action == ActionType.WORK:
        _do_work(agent, world, result)
    elif action == ActionType.BUY_FOOD:
        _do_buy_food(agent, world, result)
    elif action == ActionType.REST:
        _do_rest(agent, rng, result)
    elif action == ActionType.SEEK_JOB:
        _do_seek_job(agent, world, rng, result)
    elif action == ActionType.BEG:
        _do_beg(agent, all_agents, world, rng, result)
    elif action == ActionType.BEFRIEND:
        _do_befriend(agent, all_agents, world, rng, result)
    elif action == ActionType.CONSOLE:
        _do_console(agent, all_agents, world, rng, result)
    elif action == ActionType.ISOLATE:
        _do_isolate(agent, result)
    elif action == ActionType.SHARE:
        _do_share(agent, all_agents, world, rng, result)
    elif action == ActionType.STEAL:
        _do_steal(agent, all_agents, world, rng, result)
    elif action == ActionType.HARM_OTHER:
        _do_harm_other(agent, all_agents, world, rng, result)
    elif action == ActionType.PROTEST:
        _do_protest(agent, world, result)
    elif action == ActionType.COMPLAIN:
        _do_complain(agent, all_agents, world, rng, result)
    elif action == ActionType.COMPLY:
        result.outcome = "complied"
    else:
        result.outcome = "idle"

    return result
```

### 9.3 Individual Action Implementations

```python
def _do_work(agent: AgentState, world: SimulationState, result) -> None:
    """Work action: earn salary minus tax, modified by productivity and creativity."""
    salary = agent.resources.base_salary * (1.0 - world.tax_rate)
    productivity = emotion_productivity_mod(agent.emotions.primary)
    creativity_mod = 1.0 + (agent.traits.creativity - 0.5) * 0.4  # ±20% from creativity
    income = salary * productivity * creativity_mod

    agent.resources.money += income
    agent.resources.wealth = agent.resources.money  # mirror for compat

    # Mild workplace social contact
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.015)

    result.outcome = f"earned £{income:.2f}"
    result.score_delta = income


def _do_buy_food(agent: AgentState, world: SimulationState, result) -> None:
    """Buy food action: spend money, increase food and water needs."""
    scarcity = 2.0 - world.food_availability
    food_cost = BASE_FOOD_COST * scarcity

    if agent.resources.money < food_cost:
        # Not enough money — can't buy food
        result.outcome = "insufficient_funds"
        result.score_delta = -0.1
        return

    agent.resources.money -= food_cost
    agent.resources.wealth = agent.resources.money

    food = agent.needs.get_level(NeedType.FOOD)
    water = agent.needs.get_level(NeedType.WATER)
    agent.needs.set_level(NeedType.FOOD, food + 0.30)
    agent.needs.set_level(NeedType.WATER, water + 0.20)

    result.outcome = f"bought food for £{food_cost:.2f}"
    result.score_delta = 0.3


def _do_rest(agent: AgentState, rng: DeterministicRNG, result) -> None:
    """Rest action: increase sleep, may break angry state."""
    sleep = agent.needs.get_level(NeedType.SLEEP)
    agent.needs.set_level(NeedType.SLEEP, sleep + 0.30)

    # 30% chance to break out of angry state
    if agent.emotions.primary == EmotionType.ANGRY:
        if rng.random() < 0.30:
            agent.emotions.primary = EmotionType.NORMAL
            agent.emotions.emotion_timer = 0

    result.outcome = "rested"
    result.score_delta = 0.2


def _do_seek_job(agent: AgentState, world: SimulationState, rng: DeterministicRNG, result) -> None:
    """Seek job action: chance to become employed based on unemployment rate and ambition."""
    chance = 0.08 * (1.0 - world.unemployment_rate) * (0.5 + agent.traits.ambition)

    if rng.random() < chance:
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.job_type = assign_job_by_education(agent.resources.education, rng)
        agent.resources.base_salary = get_salary_for_job(agent.job_type, rng)
        result.outcome = f"got job: {agent.job_type.name}"
        result.score_delta = 0.5
    else:
        result.outcome = "still_looking"
        result.score_delta = 0.0


def _do_beg(agent: AgentState, all_agents: list, world: SimulationState,
            rng: DeterministicRNG, result) -> None:
    """Beg action: receive small money from nearby generous agents."""
    nearby = get_nearby_agents(agent, all_agents)
    generous = [a for a in nearby if a.traits.morality > 0.6]

    total_received = 0.0
    for g in generous:
        if g.resources.money > 10:
            donation = min(g.resources.money * 0.02, 5.0)
            g.resources.money -= donation
            g.resources.wealth = g.resources.money
            total_received += donation

    agent.resources.money += total_received
    agent.resources.wealth = agent.resources.money

    # Dignity/reputation reduces slightly
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep - 0.02)

    result.outcome = f"received £{total_received:.2f}"
    result.score_delta = total_received


def _do_befriend(agent: AgentState, all_agents: list, world: SimulationState,
                 rng: DeterministicRNG, result) -> None:
    """Befriend action: increase social connection for both agents, trigger Adler."""
    nearby = get_nearby_agents(agent, all_agents)
    if not nearby:
        result.outcome = "no_one_nearby"
        return

    # Filter: not enemy, reputation > 0.25, compatible culture or 25% random
    eligible = [
        a for a in nearby
        if a.id not in agent.enemies
        and agent.needs.get_level(NeedType.REPUTATION) > 0.25
    ]
    if not eligible:
        result.outcome = "no_eligible_targets"
        return

    other = rng.choice(eligible)

    # 55% chance of successful befriend (extraversion affects this)
    if rng.random() < 0.55:
        # Self: social += 0.12
        social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
        agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.12)

        # Other: social += 0.10
        other_social = other.needs.get_level(NeedType.SOCIAL_CONNECTION)
        other.needs.set_level(NeedType.SOCIAL_CONNECTION, other_social + 0.10)

        # Add to social connections if not already
        if other.id not in agent.social_connections:
            agent.social_connections.append(other.id)
        if agent.id not in other.social_connections:
            other.social_connections.append(agent.id)

        # Trigger Adler comparison for both
        adler_comparison(agent, other, world)
        adler_comparison(other, agent, world)

        # Reputation gain for both
        agent.needs.set_level(NeedType.REPUTATION,
                              agent.needs.get_level(NeedType.REPUTATION) + 0.02)
        other.needs.set_level(NeedType.REPUTATION,
                              other.needs.get_level(NeedType.REPUTATION) + 0.02)

        result.outcome = f"befriended {other.id}"
        result.score_delta = 0.12
    else:
        result.outcome = "rejected"


def _do_console(agent: AgentState, all_agents: list, world: SimulationState,
                rng: DeterministicRNG, result) -> None:
    """Console action: help a sad nearby agent, increase both social."""
    nearby = get_nearby_agents(agent, all_agents)
    sad_agents = [a for a in nearby
                  if a.emotions.primary in (EmotionType.SAD, EmotionType.DESPAIR)]

    if not sad_agents:
        result.outcome = "no_sad_nearby"
        return

    other = rng.choice(sad_agents)

    # Self: social += 0.05, good_acts++
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.05)
    agent.good_acts += 1

    # Other: social += 0.08, emotion_timer reset
    other_social = other.needs.get_level(NeedType.SOCIAL_CONNECTION)
    other.needs.set_level(NeedType.SOCIAL_CONNECTION, other_social + 0.08)
    other.emotions.emotion_timer = 0  # Can recover faster

    result.outcome = f"consoled {other.id}"
    result.score_delta = 0.1


def _do_isolate(agent: AgentState, result) -> None:
    """Isolate action: further reduce social connection (despair state)."""
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social - 0.02)
    result.outcome = "isolated"
    result.score_delta = -0.02


def _do_share(agent: AgentState, all_agents: list, world: SimulationState,
              rng: DeterministicRNG, result) -> None:
    """Share action: give 6% of money to a nearby needy agent."""
    nearby = get_nearby_agents(agent, all_agents)
    needy = [a for a in nearby if a.resources.money < 50]

    if not needy:
        result.outcome = "no_needy_nearby"
        return

    other = rng.choice(needy)

    # Give 6% of self's money
    amount = agent.resources.money * 0.06
    agent.resources.money -= amount
    agent.resources.wealth = agent.resources.money
    other.resources.money += amount
    other.resources.wealth = other.resources.money

    # Happiness boost
    agent.emotions.happiness_score = min(1.0, agent.emotions.happiness_score + 0.04)

    # Food boost for other
    other_food = other.needs.get_level(NeedType.FOOD)
    other.needs.set_level(NeedType.FOOD, other_food + 0.05)

    agent.good_acts += 1
    # Reputation gain
    agent.needs.set_level(NeedType.REPUTATION,
                          agent.needs.get_level(NeedType.REPUTATION) + 0.03)

    result.outcome = f"shared £{amount:.2f} with {other.id}"
    result.score_delta = 0.04


def _do_steal(agent: AgentState, all_agents: list, world: SimulationState,
              rng: DeterministicRNG, result) -> None:
    """Steal action: take up to 18% of victim's money, capped at £60."""
    nearby = get_nearby_agents(agent, all_agents)
    if not nearby:
        result.outcome = "no_victim_nearby"
        return

    victim = rng.choice(nearby)

    # Steal min(18% of victim money, £60)
    stolen = min(victim.resources.money * STEAL_PERCENT, STEAL_CAP)
    if stolen <= 0:
        result.outcome = "victim_has_no_money"
        return

    agent.resources.money += stolen
    agent.resources.wealth = agent.resources.money
    victim.resources.money -= stolen
    victim.resources.wealth = victim.resources.money

    # Food boost for thief
    food = agent.needs.get_level(NeedType.FOOD)
    agent.needs.set_level(NeedType.FOOD, food + 0.08)

    agent.crimes_committed += 1
    agent.notoriety = min(1.0, agent.notoriety + 0.05)

    # Reputation drop
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep - 0.06)

    # Victim: safety drop
    victim_safety = victim.needs.get_level(NeedType.SAFETY)
    victim.needs.set_level(NeedType.SAFETY, victim_safety - 0.12)

    # Victim becomes angry/scared
    if victim.emotions.primary not in (EmotionType.ANGRY, EmotionType.DESPAIR):
        victim.emotions.primary = EmotionType.ANGRY
        victim.emotions.emotion_timer = 2

    result.outcome = f"stole £{stolen:.2f} from {victim.id}"
    result.score_delta = stolen


def _do_harm_other(agent: AgentState, all_agents: list, world: SimulationState,
                   rng: DeterministicRNG, result) -> None:
    """Harm other action: reduce victim's safety, make them angry."""
    nearby = get_nearby_agents(agent, all_agents)
    if not nearby:
        result.outcome = "no_victim_nearby"
        return

    victim = rng.choice(nearby)

    agent.crimes_committed += 1
    agent.notoriety = min(1.0, agent.notoriety + 0.05)

    # Reputation drop
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep - 0.10)

    # Victim: safety drop
    victim_safety = victim.needs.get_level(NeedType.SAFETY)
    victim.needs.set_level(NeedType.SAFETY, victim_safety - 0.18)

    # Victim becomes angry
    if victim.emotions.primary not in (EmotionType.ANGRY, EmotionType.DESPAIR):
        victim.emotions.primary = EmotionType.ANGRY
        victim.emotions.emotion_timer = 3

    # Small health risk to agent
    agent.resources.health = max(0.0, agent.resources.health - 0.01)

    result.outcome = f"harmed {victim.id}"
    result.score_delta = -0.1


def _do_protest(agent: AgentState, world: SimulationState, result) -> None:
    """Protest action: increase protest count, boost social solidarity."""
    agent.protest_count += 1

    # Solidarity boost
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.06)

    # Reputation boost (protesting is socially visible)
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep + 0.01)

    # Trust in government drops
    agent.trust_in_govt = max(0.0, agent.trust_in_govt - 0.02)

    result.outcome = "protested"
    result.score_delta = 0.06


def _do_complain(agent: AgentState, all_agents: list, world: SimulationState,
                  rng: DeterministicRNG, result) -> None:
    """Complain action: spread discontent to nearby agents (mild contagion)."""
    # Reputation slight gain (being vocal)
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep + 0.02)

    # Spread discontent to nearby agents (mild)
    nearby = get_nearby_agents(agent, all_agents)
    for other in nearby:
        if rng.random() < 0.15:  # 15% spread chance
            other.trust_in_govt = max(0.0, other.trust_in_govt - 0.01)

    result.outcome = "complained"
    result.score_delta = 0.02
```

---

## 10. Economy System

### 10.1 Job Categories & Salaries

| Job | Category | Education | Salary Range (£/year) | Salary/tick (£) |
|---|---|---|---|---|
| Engineer | Technical | HIGHER | 55,000-95,000 | ~150-260 |
| Computer Scientist | Technical | HIGHER | 60,000-110,000 | ~164-301 |
| Pilot | Technical | HIGHER | 50,000-90,000 | ~137-246 |
| Doctor | Technical | HIGHER | 70,000-130,000 | ~191-356 |
| Therapist | Technical | HIGHER | 45,000-80,000 | ~123-219 |
| Mechanic | Technical-Hard | SECONDARY | 25,000-45,000 | ~68-123 |
| Electrician | Technical-Hard | SECONDARY | 28,000-50,000 | ~76-137 |
| Construction Planner | Technical-Hard | SECONDARY | 30,000-55,000 | ~82-150 |
| Construction Worker | Manual | LOWER | 12,000-22,000 | ~33-60 |
| Cleaner | Manual | LOWER | 10,000-18,000 | ~27-49 |
| Taxi Driver | Manual | LOWER | 11,000-20,000 | ~30-55 |

**1 tick = 1 day.** Salary/tick = annual / 365.

### 10.2 Job Assignment & Salary

```python
def assign_job_by_education(education: EducationLevel, rng: DeterministicRNG) -> JobType:
    """Assign a random job based on education level."""
    jobs = JOBS_BY_EDUCATION[education]
    return rng.choice(jobs)


def get_salary_for_job(job: JobType, rng: DeterministicRNG) -> float:
    """Generate a random salary within the job's range (per tick)."""
    low, high = SALARY_RANGES[job]
    annual = rng.uniform(low, high)
    return annual / 365.0  # per tick (1 tick = 1 day)
```

### 10.3 Money Flow Summary

| Flow | Trigger | Amount |
|---|---|---|
| Income (work) | work action | `base_salary × (1 - tax_rate) × productivity_mod × creativity_mod` |
| Food expenditure | buy_food action | `BASE_FOOD_COST × (2.0 - food_availability)` |
| Rent | every tick if no property | `RENT_COST[wealth_class]` |
| Welfare | every tick if welfare_enabled AND unemployed | `welfare_amount` (£8 default) |
| Stolen | another agent steals | `min(victim.money × 0.18, £60)` |
| Shared | share action | `6% of giver's money` |
| Beg donation | beg action | `min(giver.money × 0.02, £5.0)` per generous agent |

### 10.4 Rent Application (each tick)

```python
def apply_rent(agent: AgentState, world: SimulationState) -> None:
    """Apply rent cost if agent doesn't own property."""
    if not agent.resources.property:
        rent = RENT_COST[agent.wealth_class]
        agent.resources.money = max(0.0, agent.resources.money - rent)
        agent.resources.wealth = agent.resources.money
```

---

## 11. World System

### 11.1 Grid

- `GRID_SIZE = 20` (20×20 grid, 400 cells)
- `INTERACTION_RADIUS = 2` (agents within 2 cells interact)
- Each cell can hold multiple agents
- Grid wraps around (toroidal) — agents that walk off one edge appear on the other

### 11.2 Nearby Agents

```python
def get_nearby_agents(agent: AgentState, all_agents: list) -> list:
    """Return all living agents within INTERACTION_RADIUS of the given agent.

    Uses Euclidean distance on a toroidal grid (wraps around).
    """
    nearby = []
    for other in all_agents:
        if other.id == agent.id or not other.is_alive:
            continue
        dist = toroidal_distance(
            agent.grid_x, agent.grid_y,
            other.grid_x, other.grid_y,
            GRID_SIZE,
        )
        if dist <= INTERACTION_RADIUS:
            nearby.append(other)
    return nearby


def toroidal_distance(x1: int, y1: int, x2: int, y2: int, grid_size: int) -> float:
    """Euclidean distance on a toroidal (wrapping) grid."""
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    # Wrap to shortest distance
    dx = min(dx, grid_size - dx)
    dy = min(dy, grid_size - dy)
    return (dx * dx + dy * dy) ** 0.5
```

### 11.3 Nearby Counts (for utility scoring)

```python
def compute_nearby_counts(agent: AgentState, all_agents: list) -> dict:
    """Compute counts of nearby agent types for utility scoring.

    Returns:
        Dict with keys: 'agents', 'protesters', 'needy', 'sad', 'generous'
    """
    nearby = get_nearby_agents(agent, all_agents)
    return {
        "agents": len(nearby),
        "protesters": sum(1 for a in nearby if a.emotions.primary == EmotionType.ANGRY),
        "needy": sum(1 for a in nearby if a.resources.money < 50),
        "sad": sum(1 for a in nearby
                    if a.emotions.primary in (EmotionType.SAD, EmotionType.DESPAIR)),
        "generous": sum(1 for a in nearby if a.traits.morality > 0.6),
    }
```

### 11.4 Agent Movement

```python
def move_agent(agent: AgentState, rng: DeterministicRNG) -> None:
    """Move agent 1-2 random walk steps. Angry agents move more (restlessness)."""
    steps = 1 + rng.integers(0, 2)  # 1 or 2 steps
    if agent.emotions.primary == EmotionType.ANGRY:
        steps += 1  # Angry agents move more

    for _ in range(steps):
        dx = int(rng.integers(-1, 2))  # -1, 0, or 1
        dy = int(rng.integers(-1, 2))
        agent.grid_x = (agent.grid_x + dx) % GRID_SIZE  # Toroidal wrapping
        agent.grid_y = (agent.grid_y + dy) % GRID_SIZE
```

### 11.5 World State Variables

| Variable | Range | Default | Notes |
|---|---|---|---|
| food_availability | 0.0-1.0 | 1.0 | Scarcity = 2.0 - food_availability |
| water_availability | 0.0-1.0 | 1.0 | |
| crime_rate | 0.0-1.0 | computed | Total crimes / (alive × 8) |
| protest_intensity | 0.0-1.0 | computed | Total protests / (alive × 4) |
| unemployment_rate | 0.0-1.0 | 0.12 | |
| tax_rate | 0.0-1.0 | 0.20 | |
| welfare_enabled | bool | False | |
| welfare_amount | float | 8.0 | £/tick |

### 11.6 World Metrics Update

```python
def update_world_metrics(world: SimulationState, all_agents: list) -> None:
    """Recompute world-level metrics from all living agents."""
    living = [a for a in all_agents if a.is_alive]
    alive_count = len(living)

    if alive_count == 0:
        return

    # Crime rate: total crimes / (alive × 8)
    total_crimes = sum(a.crimes_committed for a in living)
    world.crime_rate = min(1.0, total_crimes / (alive_count * 8))

    # Protest intensity: total protests / (alive × 4)
    total_protests = sum(a.protest_count for a in living)
    world.protest_intensity = min(1.0, total_protests / (alive_count * 4))

    # Unemployment rate
    unemployed = sum(1 for a in living if not a.resources.employed)
    world.unemployment_rate = unemployed / alive_count

    # Systemic averages
    world.unlust = sum(a.unlust for a in living) / alive_count
    world.morality = sum(a.traits.morality for a in living) / alive_count

    world.population = alive_count
    world.time_step = TickNumber(world.time_step + 1)
```

---

## 12. Policy System

### 12.1 Dual Model: Impact Deltas + Policy Weights

When a policy is enacted:
1. User types policy in natural language (e.g., "raise income tax by 10% and fund welfare")
2. LLM (Gemma) receives: policy text + existing PolicyWeights + current world state + population summary
3. LLM outputs: modified PolicyWeights + ImpactDeltas per wealth class + world state changes + reasoning
4. Policy stored with BOTH weights and deltas
5. Each tick: deltas applied directly to agents; weights modify utility scores

### 12.2 Impact Delta Application (each tick)

```python
def apply_policy_effects(
    agent: AgentState,
    policy: GovernmentPolicy,
    world: SimulationState,
    world_changed: dict,
) -> None:
    """Apply a policy's impact deltas to an agent.

    Args:
        agent: The agent to apply effects to.
        policy: The government policy with impact deltas.
        world: Mutable world state (world-level changes applied once).
        world_changed: Dict tracking which world changes have been applied
                       (prevents applying the same world change multiple times).
    """
    delta = policy.impact_deltas.get(agent.wealth_class)
    if delta is None:
        return

    # Direct agent deltas
    agent.resources.money += delta.money_delta
    agent.resources.wealth = agent.resources.money
    agent.needs.set_level(NeedType.FOOD,
                           agent.needs.get_level(NeedType.FOOD) + delta.food_delta)
    agent.needs.set_level(NeedType.SAFETY,
                           agent.needs.get_level(NeedType.SAFETY) + delta.safety_delta)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION,
                           agent.needs.get_level(NeedType.SOCIAL_CONNECTION) + delta.social_delta)
    # Anger spike increases Unlust temporarily (applied before recompute)
    agent.unlust = min(1.0, agent.unlust + delta.anger_spike)

    # World state changes (applied once per policy, not per agent)
    policy_key = id(policy)
    if delta.new_tax_rate is not None and not world_changed.get(f"{policy_key}_tax"):
        world.tax_rate = delta.new_tax_rate
        world_changed[f"{policy_key}_tax"] = True
    if delta.welfare_on is not None and not world_changed.get(f"{policy_key}_welfare"):
        world.welfare_enabled = delta.welfare_on
        world_changed[f"{policy_key}_welfare"] = True
    if delta.food_event is not None and not world_changed.get(f"{policy_key}_food"):
        world.food_availability = max(0.0, min(1.0, world.food_availability + delta.food_event))
        world_changed[f"{policy_key}_food"] = True
```

### 12.3 Policy Weights in Utility Scoring

```python
def apply_policy_weights(base_scores: dict, policy_weights: PolicyWeights) -> dict:
    """Modify utility scores based on active policy weights.

    Policy weights shift the utility landscape:
    - economic_freedom > 0: boosts WORK, reduces SHARE
    - social_welfare > 0: boosts SHARE, CONSOLE, reduces STEAL
    - public_order > 0: reduces PROTEST, STEAL, HARM_OTHER
    """
    modified = base_scores.copy()
    for action, score in modified.items():
        modifier = 0.0
        if action == ActionType.WORK:
            modifier += policy_weights.economic_freedom * 0.1
        elif action == ActionType.SHARE:
            modifier += policy_weights.social_welfare * 0.15
        elif action == ActionType.CONSOLE:
            modifier += policy_weights.social_welfare * 0.1
        elif action == ActionType.STEAL:
            modifier -= policy_weights.social_welfare * 0.1
            modifier -= policy_weights.public_order * 0.15
        elif action == ActionType.HARM_OTHER:
            modifier -= policy_weights.public_order * 0.2
        elif action == ActionType.PROTEST:
            modifier -= policy_weights.public_order * 0.1
        modified[action] = score + modifier
    return modified
```

### 12.4 Deterministic Fallback (keyword matching)

```python
FALLBACK_KEYWORD_POLICIES: dict = {
    "tax increase": {
        "weights": {"economic_freedom": -0.3, "public_order": 0.1},
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=-2.0, anger_spike=0.05),
            WealthClass.MIDDLE: ImpactDelta(money_delta=-10.0, anger_spike=0.02),
            WealthClass.RICH: ImpactDelta(money_delta=-50.0),
        },
        "world": {"new_tax_rate": 0.30},
    },
    "tax cut": {
        "weights": {"economic_freedom": 0.3},
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=1.0),
            WealthClass.MIDDLE: ImpactDelta(money_delta=5.0),
            WealthClass.RICH: ImpactDelta(money_delta=50.0),
        },
        "world": {"new_tax_rate": 0.10},
    },
    "welfare": {
        "weights": {"social_welfare": 0.4},
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=8.0, safety_delta=0.05, anger_spike=-0.1),
            WealthClass.MIDDLE: ImpactDelta(money_delta=-2.0),
            WealthClass.RICH: ImpactDelta(money_delta=-5.0, anger_spike=0.03),
        },
        "world": {"welfare_on": True},
    },
    "food subsidy": {
        "deltas": {
            WealthClass.POOR: ImpactDelta(food_delta=0.1),
            WealthClass.MIDDLE: ImpactDelta(food_delta=0.05),
            WealthClass.RICH: ImpactDelta(food_delta=0.0),
        },
        "world": {"food_event": 0.15},
    },
    "police": {
        "deltas": {
            WealthClass.POOR: ImpactDelta(safety_delta=0.05),
            WealthClass.MIDDLE: ImpactDelta(safety_delta=0.05),
            WealthClass.RICH: ImpactDelta(safety_delta=0.05),
        },
    },
}


def policy_fallback(policy_text: str) -> tuple:
    """Deterministic keyword-matching policy translator.

    Returns:
        Tuple of (PolicyWeights, Dict[WealthClass, ImpactDelta], world_changes).
    """
    text_lower = policy_text.lower()
    for keyword, config in FALLBACK_KEYWORD_POLICIES.items():
        if keyword in text_lower:
            weights = PolicyWeights(**config.get("weights", {}))
            deltas = config.get("deltas", {})
            world_changes = config.get("world", {})
            return weights, deltas, world_changes

    # Default: no effect
    return PolicyWeights(), {}, {}
```

---

## 13. Adler Comparison Engine

### 13.1 When It Triggers

The Adler comparison triggers on any agent-to-agent interaction:
`befriend`, `steal`, `console`, `harm_other`, `share`, `beg`.

### 13.2 Maslow Score (for comparison)

```python
def compute_maslow_score(agent: AgentState) -> float:
    """Compute a weighted Maslow score for Adler comparisons.

    Lower layers weighted higher — physiological needs matter more
    than esteem for comparison purposes.
    """
    return (
        agent.needs.get_level(NeedType.FOOD) * 0.25
        + agent.needs.get_level(NeedType.WATER) * 0.20
        + agent.needs.get_level(NeedType.SAFETY) * 0.15
        + agent.needs.get_level(NeedType.SLEEP) * 0.10
        + agent.needs.get_level(NeedType.SOCIAL_CONNECTION) * 0.10
        + agent.needs.get_level(NeedType.SELF_ESTEEM) * 0.08
        + agent.needs.get_level(NeedType.FINANCIAL_SECURITY) * 0.07
        + agent.needs.get_level(NeedType.REPUTATION) * 0.05
    )
```

### 13.3 Comparison Logic

```python
def adler_comparison(agent: AgentState, other: AgentState, world: SimulationState) -> None:
    """Perform Adler inferiority comparison between two agents.

    Upward comparison (other better off) increases inferiority_gap, Unlust.
    Downward comparison (agent better off) boosts self_esteem, reduces Unlust.
    """
    agent_score = compute_maslow_score(agent)
    other_score = compute_maslow_score(other)
    gap = other_score - agent_score  # positive = other is better off

    if gap > 0.15:  # Upward comparison — other significantly better off
        # Inferiority gap increases
        current_gap = agent.needs.get_level(NeedType.INFERIORITY_GAP)
        agent.needs.set_level(NeedType.INFERIORITY_GAP, current_gap + gap * 0.1)

        # Self-esteem decreases
        self_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
        agent.needs.set_level(NeedType.SELF_ESTEEM, self_esteem - gap * 0.05)

        # Unlust increase (direct)
        agent.unlust = min(1.0, agent.unlust + gap * 0.03)

        # Dominance urge boost (triggers status-seeking behavior)
        # (not a need, but affects behavior in v2+ for now just tracked)

    elif gap < -0.15:  # Downward comparison — agent better off
        # Self-esteem increases
        self_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
        agent.needs.set_level(NeedType.SELF_ESTEEM, self_esteem + 0.03)

        # Inferiority gap decreases
        current_gap = agent.needs.get_level(NeedType.INFERIORITY_GAP)
        agent.needs.set_level(NeedType.INFERIORITY_GAP, current_gap - 0.02)

        # Slight Unlust decrease
        agent.unlust = max(0.0, agent.unlust - 0.02)

    # gap ≈ 0: no significant change
```

---

## 14. Tick Loop

### 14.1 10-Step Tick Loop (E2B Hybrid)

```python
async def tick(self) -> TickResult:
    """Execute one simulation tick — the heart of the engine.

    Uses staggered LLM calls: only 1/3 of agents re-evaluate per tick
    (agent_id % 3 == current_tick % 3). Others continue their last action.
    """
    import asyncio
    start_time = time.time()
    tick_num = self._current_tick

    # Step 1: Publish TickStartedEvent
    self._event_bus.publish(TickStartedEvent(
        id=EventId(str(uuid4())), tick=tick_num
    ))

    living_agents = self._agent_registry.get_all_agents()
    self._world_state.population = len(living_agents)

    # Step 2: Apply policy effects
    world_changed = {}
    for policy in self._policy_engine.get_active_policies():
        for agent in living_agents:
            apply_policy_effects(agent, policy, self._world_state, world_changed)

    # Step 3: Need decay
    for agent in living_agents:
        decay_needs(agent, self._world_state, self._rng)

    # Step 4: Welfare application + rent
    if self._world_state.welfare_enabled:
        for agent in living_agents:
            if not agent.resources.employed:
                agent.resources.money += self._world_state.welfare_amount
                agent.resources.wealth = agent.resources.money
    for agent in living_agents:
        apply_rent(agent, self._world_state)

    # Step 5: Emotion update (Unlust -> happiness -> emotion state machine)
    for agent in living_agents:
        agent.unlust = compute_unlust(agent)
        agent.emotions.happiness_score = compute_happiness(agent)
        apply_sleep_reset(agent)
        update_emotion(agent, self._rng)

    # Step 6: Action selection + execution (STAGGERED LLM)
    scheduled = self._tick_scheduler.get_execution_order()
    actions_this_tick = []
    llm_call_count = 0
    moral_dilemma_count = 0
    fallback_count = 0

    # Partition agents: those who re-evaluate this tick vs those who continue
    evaluate_agents = []
    continue_agents = []

    for agent in scheduled:
        if not agent.is_alive:
            continue
        if should_evaluate_this_tick(agent, tick_num):
            evaluate_agents.append(agent)
        else:
            continue_agents.append(agent)

    # Continue agents: repeat last action
    for agent in continue_agents:
        if agent.last_action != ActionType.IDLE:
            result = execute_action(
                agent, agent.last_action, self._world_state, living_agents, self._rng
            )
            actions_this_tick.append(result)
            self._event_bus.publish(AgentActedEvent(
                agent_id=agent.id, action=agent.last_action.name, outcome=result.outcome
            ))

    # Evaluate agents: collect prompts, batch LLM calls
    # First pass: identify moral dilemmas vs standard decisions
    standard_prompts = []
    standard_agents = []
    moral_prompts = []
    moral_agents = []

    for agent in evaluate_agents:
        nearby_counts = compute_nearby_counts(agent, living_agents)

        if is_moral_dilemma(agent, self._world_state):
            moral_prompts.append(build_moral_dilemma_prompt(agent, self._world_state, nearby_counts))
            moral_agents.append(agent)
            moral_dilemma_count += 1
        else:
            standard_prompts.append(build_agent_prompt(agent, self._world_state, nearby_counts))
            standard_agents.append(agent)

    # Batch E2B call for standard decisions
    if standard_prompts and self._ai_router.is_available():
        llm_call_count += 1
        try:
            responses = await self._ai_router.agent_decide_batch(standard_prompts)
            for agent, response_text in zip(standard_agents, responses):
                parsed = parse_llm_response(response_text)
                if parsed:
                    action = validate_action(agent, parsed["action"], self._world_state)
                    if action:
                        agent.last_action = action
                        agent.last_reasoning = parsed.get("reason", "")
                        metadata = {
                            "source": "e2b_brain",
                            "reasoning": parsed.get("reason", ""),
                            "feeling": parsed.get("feeling", ""),
                        }
                        result = execute_action(
                            agent, action, self._world_state, living_agents, self._rng
                        )
                        result.metadata = metadata
                        actions_this_tick.append(result)
                        self._event_bus.publish(AgentActedEvent(
                            agent_id=agent.id, action=action.name, outcome=result.outcome
                        ))
                        continue
                # Fallback
                action = deterministic_fallback(agent, self._world_state, self._rng)
                agent.last_action = action
                fallback_count += 1
                result = execute_action(agent, action, self._world_state, living_agents, self._rng)
                result.metadata = {"source": "deterministic_fallback", "reasoning": "LLM invalid"}
                actions_this_tick.append(result)
        except Exception:
            for agent in standard_agents:
                action = deterministic_fallback(agent, self._world_state, self._rng)
                agent.last_action = action
                fallback_count += 1
                result = execute_action(agent, action, self._world_state, living_agents, self._rng)
                actions_this_tick.append(result)
    else:
        # No LLM available — all use fallback
        for agent in standard_agents:
            action = deterministic_fallback(agent, self._world_state, self._rng)
            agent.last_action = action
            fallback_count += 1
            result = execute_action(agent, action, self._world_state, living_agents, self._rng)
            actions_this_tick.append(result)

    # Batch 26B A4B call for moral dilemmas (with thinking mode)
    if moral_prompts and self._ai_router.is_available():
        llm_call_count += 1
        try:
            responses = await self._ai_router.moral_reasoning_batch(moral_prompts)
            for agent, response_text in zip(moral_agents, responses):
                parsed = parse_llm_response(response_text)
                if parsed:
                    action = validate_action(agent, parsed["action"], self._world_state)
                    if action:
                        agent.last_action = action
                        agent.last_reasoning = parsed.get("reason", "")
                        metadata = {
                            "source": "26b_moral_reasoning",
                            "thinking_mode": True,
                            "reasoning": parsed.get("reason", ""),
                            "feeling": parsed.get("feeling", ""),
                        }
                        result = execute_action(
                            agent, action, self._world_state, living_agents, self._rng
                        )
                        result.metadata = metadata
                        actions_this_tick.append(result)
                        self._event_bus.publish(AgentActedEvent(
                            agent_id=agent.id, action=action.name, outcome=result.outcome
                        ))
                        self._event_bus.publish(AmbiguityDetectedEvent(
                            agent_id=agent.id, top_score=0.0, second_score=0.0
                        ))
                        continue
                # Fallback
                action = deterministic_fallback(agent, self._world_state, self._rng)
                agent.last_action = action
                fallback_count += 1
                result = execute_action(agent, action, self._world_state, living_agents, self._rng)
                actions_this_tick.append(result)
        except Exception:
            for agent in moral_agents:
                action = deterministic_fallback(agent, self._world_state, self._rng)
                agent.last_action = action
                fallback_count += 1
                result = execute_action(agent, action, self._world_state, living_agents, self._rng)
                actions_this_tick.append(result)
    else:
        for agent in moral_agents:
            action = deterministic_fallback(agent, self._world_state, self._rng)
            agent.last_action = action
            fallback_count += 1
            result = execute_action(agent, action, self._world_state, living_agents, self._rng)
            actions_this_tick.append(result)

    # Step 7: Agent movement
    for agent in living_agents:
        if agent.is_alive:
            move_agent(agent, self._rng)

    # Step 8: Death check
    for agent in living_agents:
        if check_death(agent, self._rng):
            agent.is_alive = False
            self._event_bus.publish(AgentDeceasedEvent(
                agent_id=agent.id, cause="starvation"
            ))

    # Step 9: World metrics update
    all_living = self._agent_registry.get_all_agents()
    update_world_metrics(self._world_state, all_living)
    self._metrics_collector.record_tick(tick_num, self._world_state, all_living)

    # Step 10: State hash + periodic LLM features + publish TickCompletedEvent
    state_hash = compute_state_hash(self._world_state, self._agent_registry)
    duration_ms = int((time.time() - start_time) * 1000)

    # Periodic: 31B governance advisory + news (every 10 ticks)
    if tick_num > 0 and tick_num % NEWS_INTERVAL_TICKS == 0:
        if self._ai_router.is_available():
            # Governance advisory
            try:
                advisory = await self._ai_router.governance_advisory(
                    self._world_state, self._policy_engine.get_active_policies()
                )
                llm_call_count += 1
                self._event_bus.publish(NewsGeneratedEvent(
                    headline=advisory.get("recommendation", ""),
                    category="governance",
                    importance=0.8,
                ))
            except Exception:
                pass

            # News generation
            try:
                events = self._event_bus.get_event_history()[-50:]
                news = await self._ai_router.generate_news(events, self._world_state)
                llm_call_count += 1
                self._event_bus.publish(NewsGeneratedEvent(
                    headline=news.headline, category=news.category,
                    importance=news.importance
                ))
            except Exception:
                pass

    self._event_bus.publish(TickCompletedEvent(
        duration_ms=duration_ms, agent_count=len(all_living),
        ambiguity_count=moral_dilemma_count
    ))

    self._current_tick = TickNumber(tick_num + 1)

    return TickResult(
        tick=tick_num,
        agent_actions=actions_this_tick,
        state_changes={},
        events_generated=len(self._event_bus.get_event_history()),
        ambiguity_count=moral_dilemma_count,
        ai_calls=llm_call_count,
        duration_ms=duration_ms,
        state_hash=state_hash,
    )
```

### 14.2 TickScheduler — Deterministic Ordering

```python
def schedule_agents(self, agents: list) -> None:
    """Store agents in deterministic execution order (sorted by agent ID)."""
    self._execution_order = sorted(agents, key=lambda a: a.get_id())

def get_execution_order(self) -> list:
    """Return the predetermined execution order."""
    return list(self._execution_order)
```

### 14.3 State Hash

```python
def compute_state_hash(world: SimulationState, registry) -> str:
    """Compute a deterministic SHA-256 hash of the current state.

    Only includes deterministic state (excludes LLM reasoning).
    """
    import hashlib
    import json

    state = {
        "tick": int(world.time_step),
        "food_availability": round(world.food_availability, 6),
        "crime_rate": round(world.crime_rate, 6),
        "protest_intensity": round(world.protest_intensity, 6),
        "unemployment_rate": round(world.unemployment_rate, 6),
        "tax_rate": round(world.tax_rate, 6),
        "welfare_enabled": world.welfare_enabled,
        "agents": sorted([
            {
                "id": str(a.id),
                "money": round(a.resources.money, 4),
                "food": round(a.needs.get_level(NeedType.FOOD), 6),
                "water": round(a.needs.get_level(NeedType.WATER), 6),
                "safety": round(a.needs.get_level(NeedType.SAFETY), 6),
                "emotion": a.emotions.primary.name,
                "unlust": round(a.unlust, 6),
                "happiness": round(a.emotions.happiness_score, 6),
                "health": round(a.resources.health, 6),
                "alive": a.is_alive,
            }
            for a in registry.get_all_agents()
            if a.is_alive
        ], key=lambda x: x["id"]),
    }
    return hashlib.sha256(
        json.dumps(state, sort_keys=True).encode()
    ).hexdigest()[:16]
```

---

## 15. Metrics & Events

### 15.1 World-Level Metrics (per tick)

| Metric | Computation | Governance Meaning |
|---|---|---|
| avg_happiness | mean(happiness_score) across living agents | Primary wellbeing indicator ("approval rating") |
| avg_unlust | mean(unlust) across living agents | Leading indicator — rises before visible behavior changes |
| crime_rate | total_crimes / (alive × 8) | Societal instability |
| protest_intensity | total_protests / (alive × 4) | Political unrest |
| unemployment_rate | unemployed / alive | Economic health |
| alive_count | count(is_alive == True) | Ultimate survival metric |
| food_availability | direct world state value | Environmental health |
| emotion_proportions | {emotion: count / alive for each emotion} | Population mood distribution |
| action_frequencies | {action: count / total for each action} | What the population is doing |

### 15.2 Wealth-Stratified Metrics

Every metric is also computed per wealth class (poor/middle/rich):

```python
def compute_stratified_metrics(all_agents: list) -> dict:
    """Compute metrics broken down by wealth class."""
    living = [a for a in all_agents if a.is_alive]

    result = {}
    for wc in WealthClass:
        class_agents = [a for a in living if a.wealth_class == wc]
        if not class_agents:
            result[wc.name] = {}
            continue

        result[wc.name] = {
            "count": len(class_agents),
            "avg_happiness": sum(a.emotions.happiness_score for a in class_agents) / len(class_agents),
            "avg_unlust": sum(a.unlust for a in class_agents) / len(class_agents),
            "avg_money": sum(a.resources.money for a in class_agents) / len(class_agents),
            "crime_rate": sum(a.crimes_committed for a in class_agents) / (len(class_agents) * 8),
            "employment_rate": sum(1 for a in class_agents if a.resources.employed) / len(class_agents),
        }

    return result
```

### 15.3 Events Published

| Event | When | Key Data |
|---|---|---|
| TickStartedEvent | Start of tick | tick number |
| TickCompletedEvent | End of tick | duration_ms, agent_count, ambiguity_count |
| AgentActedEvent | After each agent acts | agent_id, action, outcome |
| AgentDeceasedEvent | When an agent dies | agent_id, cause |
| PolicyEnactedEvent | When a policy is applied | policy_id, policy_name |
| AmbiguityDetectedEvent | When LLM tie-break is triggered | agent_id, top_score, second_score |
| NewsGeneratedEvent | Every 10 ticks (if LLM available) | headline, category, importance |

---

## 16. LLM Integration — Multi-Model Gemma 4 on AMD

### 16.1 Three-Model Deployment

We run **three Gemma 4 models simultaneously** on one AMD GPU (198GB VRAM)
using vLLM multi-instance:

| Instance | Model | Role | VRAM (Q4 QAT) | Port | vLLM Args |
|---|---|---|---|---|---|
| 1 | `gemma-4-e2b-it-qat` | Agent brains (×3 replicas) | ~1 GB × 3 = ~3 GB | 8001 | `--gpu-memory-utilization 0.05` |
| 2 | `gemma-4-26b-a4b-it-qat` | Moral reasoning (thinking mode) | ~16.5 GB | 8002 | `--gpu-memory-utilization 0.10` |
| 3 | `gemma-4-31b-it-qat` | Governance advisor + policy | ~20.3 GB | 8003 | `--gpu-memory-utilization 0.15` |
| **Total** | | | **~40 GB** | | **~30% of 198 GB** |

**Launch sequence (MUST be sequential — vLLM calculates util on free VRAM):**
```bash
# Instance 1: E2B (agent brains)
vllm serve google/gemma-4-e2b-it-qat \
  --port 8001 --gpu-memory-utilization 0.05 \
  --max-model-len 4096 --dtype auto &
sleep 15

# Instance 2: 26B A4B (moral reasoning)
vllm serve google/gemma-4-26b-a4b-it-qat \
  --port 8002 --gpu-memory-utilization 0.10 \
  --max-model-len 8192 --dtype auto &
sleep 30

# Instance 3: 31B (governance advisor)
vllm serve google/gemma-4-31b-it-qat \
  --port 8003 --gpu-memory-utilization 0.15 \
  --max-model-len 8192 --dtype auto &
sleep 30
```

**Fireworks AI fallback** (if no GPU available):
```yaml
ai:
  agent_brain:
    provider: "fireworks"
    model: "accounts/fireworks/models/gemma-4-e4b"
    base_url: "https://api.fireworks.ai/inference/v1"
  moral_reasoning:
    provider: "fireworks"
    model: "accounts/fireworks/models/gemma-4-26b-a4b-it"
    base_url: "https://api.fireworks.ai/inference/v1"
  governance_advisor:
    provider: "fireworks"
    model: "accounts/fireworks/models/gemma-4-31b-it"
    base_url: "https://api.fireworks.ai/inference/v1"
```

### 16.2 IAIRouter Extension

The `IAIRouter` interface needs new methods for the E2B hybrid:

```python
class IAIRouter(ABC):
    """Extended for E2B hybrid architecture."""

    @abstractmethod
    async def agent_decide(self, prompt: str) -> str:
        """Send a single agent state prompt to E2B, get raw text response."""

    @abstractmethod
    async def agent_decide_batch(self, prompts: list[str]) -> list[str]:
        """Send batched agent prompts to E2B replicas, get batched responses."""

    @abstractmethod
    async def moral_reasoning(self, prompt: str) -> str:
        """Send moral dilemma prompt to 26B A4B with thinking mode."""

    @abstractmethod
    async def moral_reasoning_batch(self, prompts: list[str]) -> list[str]:
        """Batched moral reasoning calls."""

    @abstractmethod
    async def governance_advisory(self, world_state: SimulationState,
                                   active_policies: list) -> dict:
        """Send world state to 31B, get policy recommendation + reasoning."""

    @abstractmethod
    async def translate_policy(self, policy_text: str,
                                existing_weights: PolicyWeights) -> tuple[PolicyWeights, dict]:
        """Translate natural language policy to ImpactDeltas + PolicyWeights."""

    @abstractmethod
    async def generate_news(self, events: list, world_state: SimulationState) -> NewsEvent:
        """Generate news article from recent events."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM is available."""
```

### 16.3 Prompt Design — Agent Brain (E2B)

**Design constraints:** E2B is small (2.3B effective). Prompts must be:
- Structured (not narrative — E2B struggles with long prose)
- Compact (~200 input tokens, ~50 output tokens)
- JSON output format (easy to parse)
- All relevant factors included with numeric values

**Prompt template** (see Section 8.3 for full code):
```
You are a person in a society simulation. Your situation:
hunger=0.12 water=0.85 sleep=0.40 safety=0.72
social=0.31 esteem=0.55
money=45 employed=true job=CLEANER
mood=angry happiness=0.28
unlust=0.62 health=0.88 reputation=0.45
morality=0.72 anger=0.55 ambition=0.40
extraversion=0.30 creativity=0.60 resilience=0.50
dominance=0.35 risk=0.25
trust_govt=0.38 crimes=0 good_acts=3
nearby=4 protesters_near=2 needy_near=1
tax_rate=0.20 welfare=true food_avail=0.82

What do you do? Choose ONE:
work, buy_food, rest, seek_job, beg, befriend, console, isolate,
share, steal, harm_other, protest, complain, comply, idle

Respond EXACTLY: {"action":"...","feeling":"...","reason":"one sentence"}
```

**Why this works:** E2B sees every factor — even slight trait differences
(morality 0.52 vs 0.48) affect its decision. The format is simple enough for
a 2.3B model to parse reliably.

### 16.4 Prompt Design — Moral Reasoning (26B A4B)

Uses `<|think|>` token for chain-of-thought reasoning. Richer prompt with
moral context. See Section 8.6 for full code.

The 26B A4B model has ELO 1441 and handles ethical reasoning well:
- "I'm starving (food=0.05) but my morality is 0.75. I have £3. There's
  an unattended food stall. Do I steal?"
- "I'm furious (unlust=0.72, anger=0.65) but morality=0.70. The government
  raised taxes again. Do I protest or restrain myself?"

**Output format:**
```json
{"action":"buy_food","feeling":"desperate but principled","reason":"I'm starving but my morals forbid stealing. I'll spend my last £3 on food."}
```

### 16.5 Prompt Design — Governance Advisor (31B)

The 31B model (ELO 1452) observes the simulation and **proactively advises**:

```python
def build_governance_prompt(world: SimulationState,
                             active_policies: list,
                             metrics_history: list) -> str:
    return f"""<|think|>
You are a governance advisor for a society simulation. Analyze the current
state and recommend policy actions.

Current world state (tick {world.time_step}):
- Population: {world.population}
- Avg happiness: {world.psychology.average_happiness:.2f}
- Avg unlust: {world.unlust:.2f}
- Crime rate: {world.crime.overall_crime_rate:.2%}
- Unemployment: {world.economy.unemployment_rate:.2%}
- Food availability: {world.food_availability:.2f}
- Tax rate: {world.tax_rate:.0%}
- Welfare: {'enabled' if world.welfare_enabled else 'disabled'}

Active policies: {[p.name for p in active_policies]}

Recent trends (last 10 ticks):
- Happiness: {trend_happiness}
- Crime: {trend_crime}
- Protests: {trend_protests}

Analyze: What's working? What's failing? What policy should be enacted
or revoked? Consider the welfare of ALL social classes.

Respond EXACTLY:
{{"assessment":"2-3 sentences","recommendation":"specific policy action","watch_items":["concern1","concern2"]}}"""
```

### 16.6 Prompt Design — Policy Translation (31B)

When the user (or governance advisor) proposes a policy in natural language:

```python
def build_policy_prompt(policy_text: str, world: SimulationState) -> str:
    return f"""<|think|>
You are a policy analyst. Translate this policy into simulation impacts.

Policy: "{policy_text}"

Current state: tax={world.tax_rate:.0%}, unemployment={world.economy.unemployment_rate:.2%},
food_avail={world.food_availability:.2f}, welfare={'on' if world.welfare_enabled else 'off'}

Analyze the impact on each wealth class (poor/middle/rich) and the world.
Each delta is a per-tick effect. money_delta in pounds, others are 0-1 scale changes.

Respond EXACTLY:
{{"poor":{{"money_delta":-10,"food_delta":0.05,"safety_delta":0.02,"social_delta":0.0,"anger_spike":0.0}},
"middle":{{"money_delta":-20,"food_delta":0.0,"safety_delta":0.02,"social_delta":0.0,"anger_spike":0.0}},
"rich":{{"money_delta":-100,"food_delta":0.0,"safety_delta":0.02,"social_delta":0.0,"anger_spike":0.05}},
"world_changes":{{"new_tax_rate":0.25,"welfare_on":true,"food_event":null}},
"weights":{{"economic_freedom":0.3,"social_welfare":0.7,"environmental_protection":0.5,"public_order":0.6,"innovation":0.4,"cultural_preservation":0.3}},
"reasoning":"2-3 sentences explaining the expected effects"}}"""
```

### 16.7 Prompt Design — News Generation (E2B or 12B)

Every 10 ticks, generate a news article from recent events:

```python
def build_news_prompt(events: list, world: SimulationState) -> str:
    event_summary = "\n".join(
        f"- Tick {e.tick}: {e.event_type} ({e.data})"
        for e in events[-20:]
    )
    return f"""You are a journalist in a simulated society. Write a brief news article.

Recent events:
{event_summary}

Current state: happiness={world.psychology.average_happiness:.2f},
crime={world.crime.overall_crime_rate:.2%}, unemployment={world.economy.unemployment_rate:.2%}

Write a 2-3 sentence news headline and summary.

Respond EXACTLY:
{{"headline":"...","body":"2-3 sentences","category":"economy|crime|social|politics"}}"""
```

### 16.8 VLLMRouter Implementation

```python
class VLLMRouter:
    """vLLM router for multi-model Gemma 4 deployment.

    Routes requests to three separate vLLM instances running on different ports.
    All models are configurable via AIConfig — swap any model without code changes.
    """

    def __init__(self, config: AIConfig):
        self._e2b_client = httpx.AsyncClient(
            base_url=config.agent_brain.base_url,
            timeout=config.agent_brain.timeout
        )
        self._moral_client = httpx.AsyncClient(
            base_url=config.moral_reasoning.base_url,
            timeout=config.moral_reasoning.timeout
        )
        self._gov_client = httpx.AsyncClient(
            base_url=config.governance_advisor.base_url,
            timeout=config.governance_advisor.timeout
        )
        self._config = config
        self._available = True

    async def agent_decide_batch(self, prompts: list[str]) -> list[str]:
        """Send batched prompts to E2B vLLM instance.

        vLLM handles batching internally — we send individual requests
        and vLLM batches them at the engine level.
        """
        tasks = [self._e2b_client.post("/v1/completions", json={
            "model": self._config.agent_brain.model,
            "prompt": p,
            "temperature": self._config.agent_brain.temperature,
            "max_tokens": self._config.agent_brain.max_tokens,
        }) for p in prompts]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        results = []
        for r in responses:
            if isinstance(r, Exception):
                results.append("")
            else:
                data = r.json()
                results.append(data["choices"][0]["text"])
        return results

    async def moral_reasoning_batch(self, prompts: list[str]) -> list[str]:
        """Send batched moral dilemma prompts to 26B A4B."""
        tasks = [self._moral_client.post("/v1/completions", json={
            "model": self._config.moral_reasoning.model,
            "prompt": p,
            "temperature": self._config.moral_reasoning.temperature,
            "max_tokens": self._config.moral_reasoning.max_tokens,
        }) for p in prompts]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        results = []
        for r in responses:
            if isinstance(r, Exception):
                results.append("")
            else:
                data = r.json()
                results.append(data["choices"][0]["text"])
        return results

    async def governance_advisory(self, world_state, active_policies) -> dict:
        """Send world state to 31B for governance advisory."""
        prompt = build_governance_prompt(world_state, active_policies, [])
        response = await self._gov_client.post("/v1/completions", json={
            "model": self._config.governance_advisor.model,
            "prompt": prompt,
            "temperature": self._config.governance_advisor.temperature,
            "max_tokens": self._config.governance_advisor.max_tokens,
        })
        data = response.json()
        text = data["choices"][0]["text"]
        return parse_llm_response(text) or {}

    def is_available(self) -> bool:
        return self._available
```

### 16.9 Deterministic Fallbacks

Every LLM use case has a deterministic fallback:

| Use Case | Fallback Strategy |
|---|---|
| Agent decision (E2B) | 3-level priority queue (see Section 8.7) |
| Moral reasoning (26B) | Same priority queue, but with morality gate check |
| Policy translation (31B) | Keyword matching table (see Section 12.4) |
| Governance advisory (31B) | Simple threshold alerts (crime>15%, unlust>0.7, etc.) |
| News generation | Template-based: "Tick {N}: {event_type} occurred." |

### 16.10 Model Swappability

All models are configurable — the team can swap any model without code changes:

```yaml
ai:
  agent_brain:
    model: "gemma-4-e2b-it-qat"     # can swap to e4b, 12b, or any model
    provider: "vllm"                  # or "fireworks" or "mock"
    base_url: "http://localhost:8001"
    temperature: 0.0
    max_tokens: 64
    thinking_mode: false

  moral_reasoning:
    model: "gemma-4-26b-a4b-it-qat"  # can swap to 31b, or any model
    provider: "vllm"
    base_url: "http://localhost:8002"
    temperature: 0.2
    max_tokens: 256
    thinking_mode: true

  governance_advisor:
    model: "gemma-4-31b-it-qat"      # can swap to any model
    provider: "vllm"
    base_url: "http://localhost:8003"
    temperature: 0.3
    max_tokens: 512
    thinking_mode: true
```

The `IAIRouter` implementation routes to the correct model based on config.
Swapping models is a config change, not a code change.

---

## 17. Determinism & Testing

### 17.1 RNG Usage

ALL randomness uses `DeterministicRNG` (seeded numpy Generator). NEVER `random.*`
or unseeded numpy.

### 17.2 LLM Determinism

- E2B agent brain uses temperature 0.0 — near-deterministic for same input
- 26B A4B moral reasoning uses temperature 0.2 with thinking mode — near-deterministic
- 31B governance/policy uses temperature 0.3 — near-deterministic
- LLM responses are treated as external inputs (per ADR-002)
- State hash excludes LLM reasoning (only includes deterministic state)
- If LLM unavailable, deterministic fallback ensures full reproducibility
- Staggered re-evaluation (every 3 ticks) means 2/3 of agents continue last action — reduces LLM variance impact

### 17.3 Test Categories

| Test Category | What to Test | Files |
|---|---|---|
| Determinism | Same seed = same state hash after N ticks (without LLM) | `test_determinism.py` |
| Needs decay | Exact decay rates, scarcity multiplier, crime pressure | `test_needs.py` |
| Unlust engine | Formula with known inputs, morality gate, all 4 ranges | `test_unlust.py` |
| Emotion state machine | All 5 states, timer logic, resilience effect, sleep reset | `test_emotion.py` |
| E2B hybrid decision | Prompt building, response parsing, validation, fallback | `test_decision.py` |
| Moral dilemma detection | All 5 dilemma conditions, correct routing to 26B | `test_moral_dilemma.py` |
| Staggered scheduling | agent_id % 3 offset, continue last action between evals | `test_stagger.py` |
| Actions | Each of 14 actions, effects on agent/world/other agents | `test_actions.py` |
| Economy | Salary calculation, food cost, welfare, rent, wealth class derivation | `test_economy.py` |
| Policy | Delta application, weight modification, keyword fallback | `test_policy.py` |
| Adler | Upward comparison (Unlust up), downward (self_esteem up) | `test_adler.py` |
| Grid | Movement, nearby agents, toroidal wrapping | `test_grid.py` |
| Death | All 4 death conditions | `test_death.py` |
| LLM integration | Mock router, E2B batch, 26B batch, 31B advisory, fallbacks | `test_llm_integration.py` |
| Metrics | All 9 metrics, wealth stratification | `test_metrics.py` |
| Tick loop | Full integration, 80 agents, 100 ticks, staggered LLM | `test_tick_loop.py` |

### 17.4 Coverage Requirements

- **90% branch coverage** minimum (CI-enforced, highest bar in project)
- All tests must verify determinism (same seed = same result)
- Use `tools/mocks/mock_ai_router.py` for testing without vLLM

---

## 18. Implementation Order

### Phase 1: Foundation (Day 1 morning)

1. Schema extensions (enums, dataclass fields, new ImpactDelta)
2. Constants (all Guide constants in `shared/constants/`)
3. DeterministicRNG extensions (beta distribution method)
4. Agent initialization (Beta-distributed traits, needs, socioeconomic status)
5. Grid initialization

### Phase 2: Core Systems (Day 1 afternoon)

6. Needs decay system (all 13 needs, decay rates, scarcity multiplier)
7. Unlust engine (exact formula, morality_active function)
8. Happiness score (composite formula)
9. Emotion state machine (5 states, timers, resilience, sleep reset)
10. Death conditions

### Phase 3: Decision & Actions (Day 2 morning)

11. Moral dilemma detection (5 conditions)
12. E2B agent prompt builder (structured state → compact prompt)
13. 26B moral reasoning prompt builder (with `<|think|>` token)
14. LLM response parsing & validation (JSON parse, action validation)
15. Deterministic fallback (3-level priority queue)
16. Action execution (all 14 actions with effects)
17. Adler comparison engine
18. TickScheduler deterministic ordering + staggered offsets

### Phase 4: World & Economy (Day 2 afternoon)

19. World state management (food/water/tax/welfare)
20. Economy (jobs, salaries, food cost, welfare, rent, wealth class mobility)
21. Grid movement
22. Tick loop (10 steps, staggered LLM batched calls, wired together)
23. Metrics collection
24. State hash computation

### Phase 5: LLM Integration (Day 3 morning)

25. VLLMRouter implementation (3 instances: E2B, 26B, 31B)
26. IAIRouter extension (agent_decide_batch, moral_reasoning_batch, governance_advisory)
27. Batched E2B calls (asyncio.gather to vLLM, internal batching)
28. Batched 26B A4B calls (thinking mode)
29. 31B governance advisory (every 10 ticks)
30. 31B policy translation (on-demand)
31. News generation (every 10 ticks)
32. Deterministic fallbacks for all 5 use cases
33. AIConfig with full model swappability

### Phase 6: Testing & Docker (Day 3 afternoon)

34. Unit tests (90% branch coverage)
35. Determinism tests (same seed = same hash without LLM)
36. Integration test (full tick loop, 80 agents, 100 ticks, mock LLM)
37. Docker containerization (3 vLLM instances + simulation + backend)
38. Demo preparation (live dashboard, policy enactment, agent thoughts)
---

## 19. File Manifest

### 19.1 Files to Create

| Path | Purpose |
|---|---|
| `shared/constants/simulation_constants.py` | Beta params, salary ranges, job configs, wealth class config |
| `shared/interfaces/i_ai_router.py` | **MODIFY** — add agent_decide_batch, moral_reasoning_batch, governance_advisory |
| `simulation/agents/agent_factory.py` | Agent initialization with Beta-distributed traits |
| `simulation/agents/needs_calculator.py` | Needs decay/replenishment logic |
| `simulation/agents/unlust_engine.py` | Unlust computation + morality gate |
| `simulation/agents/emotion_engine.py` | Emotion state machine |
| `simulation/agents/decision_engine.py` | E2B hybrid: prompt builders, dilemma detection, parsing, validation, fallback |
| `simulation/agents/action_executor.py` | Action execution (all 14 actions) |
| `simulation/agents/adler_engine.py` | Comparison engine |
| `simulation/world/grid.py` | Grid system, nearby agents, movement |
| `simulation/world/economy.py` | Jobs, salaries, money flow |
| `simulation/world/metrics_calculator.py` | World metrics computation |
| `simulation/policies/policy_effects.py` | Delta application, weight modification |
| `simulation/policies/policy_fallback.py` | Deterministic keyword-matching fallback |
| `simulation/engine/llm_integration.py` | VLLMRouter, batched calls, staggered scheduling |
| `simulation/engine/config_loader.py` | 3-tier config system (YAML load + runtime overrides) |
| `simulation/config/default_config.yaml` | Default configuration file (all tweakable values) |
| `tests/unit/simulation/test_needs.py` | Needs decay tests |
| `tests/unit/simulation/test_unlust.py` | Unlust engine tests |
| `tests/unit/simulation/test_emotion.py` | Emotion state machine tests |
| `tests/unit/simulation/test_decision.py` | E2B hybrid decision tests (prompt building, parsing, validation) |
| `tests/unit/simulation/test_moral_dilemma.py` | Moral dilemma detection tests |
| `tests/unit/simulation/test_stagger.py` | Staggered scheduling tests |
| `tests/unit/simulation/test_actions.py` | Action execution tests |
| `tests/unit/simulation/test_economy.py` | Economy tests |
| `tests/unit/simulation/test_policy.py` | Policy tests |
| `tests/unit/simulation/test_adler.py` | Adler comparison tests |
| `tests/unit/simulation/test_grid.py` | Grid system tests |
| `tests/unit/simulation/test_determinism.py` | Determinism verification tests |
| `tests/unit/simulation/test_llm_integration.py` | LLM integration tests with mock router |
| `tests/unit/simulation/test_metrics.py` | Metrics tests |
| `tests/unit/simulation/test_tick_loop.py` | Full tick loop integration tests |
| `docker/vllm-docker-compose.yml` | 3 vLLM instances (E2B, 26B, 31B) on one GPU |



### 19.2 Files to Modify

| Path | Changes |
|---|---|
| `shared/types/enums.py` | Replace enum values with Guide-aligned ones (ActionType 15, NeedType 13, EmotionType 5, WealthClass 3 + new Gender/Culture/EducationLevel/JobType) |
| `shared/schemas/agent_state.py` | Extend AgentTraits (7 traits), AgentResources, AgentEmotions, AgentState (last_action, last_reasoning, gender, culture, born_tick, unlust, good_acts, crimes_committed, notoriety, trust_in_govt, protest_count, grid_x, grid_y, job_type, spouse, enemies, community_id) |
| `shared/schemas/simulation_state.py` | Add world state fields (food_availability, water_availability, crime_rate, protest_intensity, unemployment_rate, tax_rate, welfare_enabled, welfare_amount) |
| `shared/schemas/policy.py` | Add ImpactDelta, extend GovernmentPolicy with impact_deltas |
| `shared/schemas/tick_result.py` | Add metadata field to AgentActionResult |
| `shared/constants/defaults.py` | Add Guide constants (decay rates, emotion thresholds, economy constants) |
| `shared/utilities/deterministic_rng.py` | Add `beta()`, `weighted_choice()`, `integers()` methods |
| `shared/interfaces/i_ai_router.py` | Add agent_decide_batch, moral_reasoning_batch, governance_advisory methods |
| `simulation/engine/simulation_engine.py` | Implement tick loop with staggered LLM, async |
| `simulation/agents/agent.py` | Implement all IAgent methods |
| `simulation/policies/policy_engine.py` | Implement get_aggregate_weights, calculate_policy_effect |
| `simulation/scheduler/tick_scheduler.py` | Implement deterministic sorting + staggered offset tracking |
| `simulation/metrics/metrics_collector.py` | Implement record_tick |
| `simulation/world/world_state.py` | Implement update_state with validation |
| `models/router/ai_router.py` | Implement VLLMRouter with 3 model instances |
| `models/router/config.py` | Extend AIConfig with agent_brain/moral_reasoning/governance_advisor sections |
| `prompts/tie-break.md` | Replace with E2B agent brain prompt + 26B moral reasoning prompt |
| `prompts/policy-translation.md` | Update for 31B with thinking mode + ImpactDelta output |
| `prompts/narrative-generation.md` | Update for news generation with events |
| `prompts/system-prompts.md` | Add governance advisor system prompt |
| `tests/unit/simulation/test_engine.py` | Implement real tests (replace stubs) |
| `tests/unit/simulation/test_agents.py` | Implement real tests (replace stubs) |
| `tests/conftest.py` | Update fixtures to match new schemas |
| `simulation/README.md` | Update TODO list + architecture description |
| `simulation/requirements.txt` | Add httpx, pyyaml if not present |
---

## 20. Code Templates

### 20.1 DeterministicRNG Extension

```python
# In shared/utilities/deterministic_rng.py — ADD these methods:

def beta(self, a: float, b: float) -> float:
    """Sample from a Beta distribution.

    Args:
        a: Alpha parameter.
        b: Beta parameter.

    Returns:
        Float in [0, 1) from Beta(a, b).
    """
    return float(self._generator.beta(a, b))

def weighted_choice(self, items: list, weights: list) -> object:
    """Choose an item with weighted probabilities.

    Args:
        items: List of items to choose from.
        weights: Corresponding weights (relative probabilities).

    Returns:
        Selected item.
    """
    return self._generator.choice(items, p=weights / sum(weights))

def integers(self, low: int, high: int) -> int:
    """Return a random integer in [low, high).

    Args:
        low: Inclusive lower bound.
        high: Exclusive upper bound.

    Returns:
        Random integer.
    """
    return int(self._generator.integers(low, high))
```

### 20.2 DecisionRequest Builder

```python
def build_decision_request(
    agent: AgentState,
    candidates: list,
    scores: dict,
    world: SimulationState,
) -> DecisionRequest:
    """Build a DecisionRequest for LLM tie-breaking.

    Args:
        agent: The agent making the decision.
        candidates: List of candidate ActionType values.
        scores: Dict mapping ActionType to utility score.
        world: Current world state.

    Returns:
        DecisionRequest ready to send to the LLM.
    """
    options = [
        DecisionOption(
            action=action,
            label=action.name,
            utility_scores=scores,
            base_score=scores[action],
        )
        for action in candidates
    ]

    return DecisionRequest(
        agent_id=agent.id,
        state=agent,
        unlust=agent.unlust,
        morality=agent.traits.morality,
        options=options,
        context={
            "world": {
                "food_availability": world.food_availability,
                "crime_rate": world.crime_rate,
                "tax_rate": world.tax_rate,
                "unemployment_rate": world.unemployment_rate,
            },
            "emotion": agent.emotions.primary.name,
            "happiness": agent.emotions.happiness_score,
        },
    )
```

### 20.3 AgentActionResult Extension

The existing `AgentActionResult` needs a `metadata` field for the explainability trace:

```python
@dataclass
class AgentActionResult:
    """Result of an agent's action execution."""
    agent_id: AgentId
    action: str
    outcome: str
    score_delta: float
    metadata: dict = field(default_factory=dict)  # NEW: explainability trace
```

---

## Appendix A: Configuration Constants Reference

| Constant | Default | Effect of Increasing | Effect of Decreasing |
|---|---|---|---|
| GRID_SIZE | 20 | More spread out, less interaction | Denser, more interaction |
| N_AGENTS | 80 | More diverse, longer compute | Faster, less meaningful |
| INTERACTION_RADIUS | 2 | More agents interact | More isolated |
| FOOD_DECAY | 0.018 | Need food more often | Longer survival without eating |
| WATER_DECAY | 0.014 | Faster water crisis | Slower water crisis |
| SAFETY_DECAY | 0.004 | Safety degrades faster | More stable baseline |
| SOCIAL_DECAY | 0.009 | Get lonely faster | Social needs less urgent |
| HAPPY_THRESHOLD | 0.65 | Harder to be happy | Easier to be happy |
| SAD_THRESHOLD | 0.35 | Easier to fall into sadness | More resilient against sadness |
| ANGRY_UNLUST | 0.58 | Slower anger escalation | Faster anger escalation |
| DESPAIR_UNLUST | 0.82 | Despair harder to reach | Despair easier |
| BASE_FOOD_COST | 6.0 | Food expensive, poor struggle | Food cheap, poverty less deadly |
| BASE_TAX_RATE | 0.20 | More revenue, less income | Less revenue, more take-home |
| UNEMPLOYMENT_RATE | 0.12 | More unemployment stress | Near-full employment |

---

## Appendix B: Quick Reference — Formula Summary

### Unlust
```
unlust = (max(0, 0.5-food) × 0.28) + (max(0, 0.5-water) × 0.22)
       + (max(0, 0.5-safety) × 0.20) + (max(0, 0.5-social) × 0.12)
       + (max(0, 1.0-(money/600)) × 0.18)
```

### Happiness
```
happiness = food×0.11 + water×0.09 + safety×0.09 + social×0.09
         + sleep×0.08 + self_esteem×0.08 + financial×0.08
         + health×0.13 + reputation×0.05 + (1-unlust)×0.15
         + (0.05 if employed else 0)
```

### Scarcity
```
scarcity_multiplier = 2.0 - food_availability
food_cost = BASE_FOOD_COST × scarcity_multiplier
```

### Income
```
income = base_salary × (1 - tax_rate) × productivity_mod × creativity_mod
creativity_mod = 1.0 + (creativity - 0.5) × 0.4
```

### Emotion Timer (with resilience)
```
timer = base_timer × (1.0 - resilience × 0.5)
```

### Sleep Quality
```
sleep_quality = safety × (1 - unlust) × resilience
```

### Steal
```
stolen = min(victim.money × 0.18, £60)
```

### Job Seeking
```
chance = 0.08 × (1 - unemployment_rate) × (0.5 + ambition)
```

### Crime Rate
```
crime_rate = total_crimes / (alive_count × 8)
```

### Protest Intensity
```
protest_intensity = total_protests / (alive_count × 4)
```

### Staggered LLM Scheduling
```
agent_tick_offset = agent_id % 3
should_evaluate = (current_tick % 3) == agent_tick_offset
# 1/3 of agents re-evaluate each tick; 2/3 continue last_action
```

### Moral Dilemma Escalation
```
if is_moral_dilemma(agent_state):
    action = 26B_A4B_reasoning(prompt)   # thinking mode, temp 0.2
else:
    action = E2B_brain(prompt)            # temp 0.0
# Fallback: 3-level priority queue (see Section 8.7)
```

---

*End of Implementation Guide — v2.0*

*This document is the single source of truth for simulation engine implementation.
Follow it strictly. Do not invent formulas or parameters not defined here.
All values are configurable — see Section 17 for the full config system.*