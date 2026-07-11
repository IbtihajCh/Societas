"""
Default Configuration Values
=============================

Default values for simulation configuration parameters.
"""

DEFAULT_POPULATION_SIZE: int = 1000
"""Default initial population size."""

DEFAULT_SIMULATION_SEED: int = 42
"""Default random seed for deterministic simulation."""

DEFAULT_TICK_RATE_MS: int = 1000
"""Default tick rate in milliseconds."""

DEFAULT_MAX_TICKS: int = 10000
"""Default maximum number of ticks."""

DEFAULT_AGENT_LIFESPAN_TICKS: int = 5000
"""Default agent lifespan in ticks."""

DEFAULT_INITIAL_WEALTH: float = 100.0
"""Default initial wealth for new agents."""

DEFAULT_AMBIGUITY_THRESHOLD: float = 0.05
"""Default threshold for decision ambiguity detection."""

DEFAULT_DETERMINISTIC_WEIGHT: float = 0.7
"""Default weight for deterministic scores in hybrid fusion."""

DEFAULT_GEMMA_WEIGHT: float = 0.3
"""Default weight for Gemma scores in hybrid fusion."""

DEFAULT_LOG_LEVEL: str = "INFO"
"""Default logging level."""

DEFAULT_API_PORT: int = 8000
"""Default backend API port."""

DEFAULT_FRONTEND_PORT: int = 3000
"""Default frontend port."""

DEFAULT_VLLM_PORT: int = 8001
"""Default vLLM server port."""

DEFAULT_VLLM_MODEL: str = "google/gemma-2-9b-it"
"""Default vLLM model identifier."""

# === Emotion thresholds (per Project Guide) ===
HAPPY_THRESHOLD: float = 0.65
SAD_THRESHOLD: float = 0.35
ANGRY_UNLUST_THRESHOLD: float = 0.45
"""Lowered from 0.58 (v2 engine calibration 2026-07-11). At 0.58, max observed unlust is ~0.37
so ANGRY emotion was unreachable. At 0.45, ANGRY fires in stress conditions."""
DESPAIR_UNLUST_THRESHOLD: float = 0.55
"""Lowered from 0.82 (v2 engine calibration 2026-07-11). INVARIANT: must be > UNLUST_MORALITY_GATE.
At 0.82, max observed unlust is ~0.37 so DESPAIR was unreachable. At 0.55, DESPAIR fires."""
ANGRY_TENDENCY_THRESHOLD: float = 0.4

# === Emotion timers (ticks) ===
SAD_TIMER: int = 2
ANGRY_TIMER: int = 3
DESPAIR_TIMER: int = 4

# === Unlust engine weights ===
UNLUST_FOOD_WEIGHT: float = 0.28
UNLUST_WATER_WEIGHT: float = 0.22
UNLUST_SAFETY_WEIGHT: float = 0.20
UNLUST_SOCIAL_WEIGHT: float = 0.12
UNLUST_FINANCIAL_WEIGHT: float = 0.18
UNLUST_FINANCIAL_DIVISOR: float = 600.0
UNLUST_MORALITY_GATE: float = 0.38
"""Lowered from 0.58 (v2 engine calibration 2026-07-11). INVARIANT: must be < DESPAIR_UNLUST_THRESHOLD.
At 0.58, zone 2 (unlust >= 0.58 and unlust < DESPAIR) was unreachable because DESPAIR was 0.82.
At 0.38, zone 2 is reachable and morality-driven actions can fire."""
UNLUST_NEED_THRESHOLD: float = 0.7

# === Need decay rates (base, before scarcity modifier) ===
FOOD_DECAY_RATE: float = 0.012
"""Reduced from 0.018. At 0.018 * scarcity=1.15 = 0.0207/tick, food depletes
from 0.5 to death in 23 ticks — leaves no margin for wealth-stratified cost."""
WATER_DECAY_RATE: float = 0.008
"""Reduced from 0.010. At 0.010, water dies in 44 ticks for the average agent,
which is shorter than food (35 ticks). Water should last longer than food."""
SLEEP_DECAY_RATE: float = 0.02
"""Reduced from 0.04. With natural recovery of 0.02, net change is 0 — agents
don't accumulate sleep debt unless they're doing nothing. At 0.04, 50 ticks
without rest = death which is unrealistic."""
SEXUAL_TENSION_GROWTH_RATE: float = 0.008
SAFETY_DECAY_RATE: float = 0.004
SOCIAL_DECAY_RATE: float = 0.009
FAMILY_DECAY_RATE: float = 0.005
ROMANTIC_DECAY_RATE: float = 0.006
SELF_ESTEEM_DECAY_RATE: float = 0.003
REPUTATION_DECAY_RATE: float = 0.001

# === Sleep replenishment ===
SLEEP_REPLENISH_RATE: float = 0.05
SLEEP_RESET_THRESHOLD: float = 0.5
SLEEP_HALF_TIMER_THRESHOLD: float = 0.3
SLEEP_RECOVERY_REST: float = 0.35
"""Sleep recovery from the rest action."""
SLEEP_RECOVERY_NATURAL: float = 0.02
"""Natural sleep recovery per tick even without action."""
SLEEP_DEATH_THRESHOLD: float = 0.05
"""Sleep level below which the agent risks health damage."""
INSOMNIA_STRESS_THRESHOLD: float = 0.6
"""Unlust above this (combined with low safety) can cause insomnia."""
INSOMNIA_SAFETY_THRESHOLD: float = 0.3
"""Safety below this (combined with high unlust) can cause insomnia."""
INSOMNIA_INCREASE_RATE: float = 0.03
"""Insomnia increase per tick when conditions are met."""
INSOMNIA_DECAY_RATE: float = 0.02
"""Insomnia decay per tick when conditions are not met."""
INSOMNIA_MAX: float = 1.0
"""Maximum insomnia severity."""

# === Death ===
DESPAIR_MORTALITY_RATE: float = 0.004
FOOD_DEATH_THRESHOLD: float = 0.02
WATER_DEATH_THRESHOLD: float = 0.02
HEALTH_DEATH_THRESHOLD: float = 0.02
JOB_LOSS_RATE: float = 0.002
JOB_LOSS_ECON_SENSITIVITY: float = 2.0
JOB_SEEK_ECON_SENSITIVITY: float = 1.5
INFLATION_DECAY_RATE: float = 0.002
DEBT_INTEREST_RATE: float = 0.01
ECONOMIC_HARDSHIP_DEATH_RATE: float = 0.001
"""Tuned 2026-07-11 for population stability."""

# === Economy ===
BASE_FOOD_COST: float = 10.0
DEFAULT_TAX_RATE: float = 0.15
DEFAULT_WELFARE_AMOUNT: float = 8.0
BASE_UNEMPLOYMENT_RATE: float = 0.10

# === Wealth-class multipliers (POOR, MIDDLE, RICH) ===
SALARY_MULTIPLIER_POOR: float = 0.6
SALARY_MULTIPLIER_MIDDLE: float = 1.0
SALARY_MULTIPLIER_RICH: float = 1.3
FOOD_COST_MULTIPLIER_POOR: float = 1.3   # poor pay more for food (food deserts)
FOOD_COST_MULTIPLIER_MIDDLE: float = 1.0
FOOD_COST_MULTIPLIER_RICH: float = 0.8   # rich have cheaper food access

# === World ===
FOOD_AVAILABILITY_DEFAULT: float = 0.85
WATER_AVAILABILITY_DEFAULT: float = 0.90
SCARCITY_BASE: float = 2.0

# === Grid ===
GRID_SIZE: int = 20
INTERACTION_RADIUS: int = 2

# === Happiness weights (must sum to ~1.0) ===
HAPPINESS_FOOD_WEIGHT: float = 0.11
HAPPINESS_WATER_WEIGHT: float = 0.09
HAPPINESS_SAFETY_WEIGHT: float = 0.09
HAPPINESS_SOCIAL_WEIGHT: float = 0.09
HAPPINESS_SLEEP_WEIGHT: float = 0.08
HAPPINESS_SELF_ESTEEM_WEIGHT: float = 0.08
HAPPINESS_FINANCIAL_WEIGHT: float = 0.08
HAPPINESS_HEALTH_WEIGHT: float = 0.13
HAPPINESS_REPUTATION_WEIGHT: float = 0.05
HAPPINESS_UNLUST_WEIGHT: float = 0.15
HAPPINESS_EMPLOYED_BONUS: float = 0.05

# === Sibling dynamics ===
SIBLING_JEALOUSY_WEALTH_WEIGHT: float = 0.4
SIBLING_JEALOUSY_SUCCESS_WEIGHT: float = 0.3
SIBLING_JEALOUSY_DECAY_RATE: float = 0.02
SIBLING_BOND_INCREASE_RATE: float = 0.01
SIBLING_BOND_DECREASE_RATE: float = 0.03
SIBLING_AFFECT_UNLUST_WEIGHT: float = 0.15
SIBLING_SUPPORT_PROBABILITY: float = 0.05

# === Adler comparison ===
ADLER_GAP_THRESHOLD: float = 0.15
ADLER_INFERIORITY_GAIN_PER_GAP: float = 0.1
ADLER_SELF_ESTEEM_CHANGE_PER_GAP: float = 0.05
ADLER_UNLUST_CHANGE_PER_GAP: float = 0.03
ADLER_DOMINANCE_CHANGE_PER_GAP: float = 0.02
ADLER_SUPERIORITY_GAIN: float = 0.02

# === Decision ===
DECISION_STAGGER_INTERVAL: int = 3
MORAL_DILEMMA_FOOD_THRESHOLD: float = 0.15
MORAL_DILEMMA_MORALITY_THRESHOLD: float = 0.5
MORAL_DILEMMA_UNLUST_THRESHOLD: float = 0.5

# === Agent actions ===
SEEK_JOB_BASE_CHANCE: float = 0.08
BEG_MAX_AMOUNT: float = 5.0
STEAL_PERCENTAGE_CAP: float = 0.18
STEAL_AMOUNT_CAP: float = 60.0
SHARE_PERCENTAGE: float = 0.06
REPUTATION_CHANGE_GOOD: float = 0.02
REPUTATION_CHANGE_CRIMINAL: float = -0.06
REPUTATION_CHANGE_KILL: float = -0.30
REPUTATION_DECAY_RATE: float = 0.001
REPUTATION_CRIME_PENALTY: float = 0.02
"""Additional reputation penalty per tick per crime committed (cumulative)."""
REPUTATION_GOOD_BONUS: float = 0.01
"""Additional reputation bonus per tick per good act performed (cumulative)."""
GOSSIP_SPREAD_CHANCE: float = 0.1
"""Chance per tick that a nearby agent learns this agent's reputation via gossip."""
REPUTATION_KNOWN_DECAY: float = 0.05
"""Decay rate for known reputations in gossip storage."""

# === Community system ===
COMMUNITY_RECLUSTER_INTERVAL: int = 10
LEADER_SAFETY_BONUS: float = 0.1
LEADER_REPUTATION_GAIN: float = 0.02
CREATIVE_HAPPINESS_BONUS: float = 0.08
"""How often (in ticks) communities are reclustered."""
COMMUNITY_MIN_SIZE: int = 3
"""Minimum agents in a community cluster."""
COMMUNITY_MAX_SIZE: int = 15
"""Maximum agents in a community cluster."""

# === Riot events ===
RIOT_PROTEST_THRESHOLD: float = 0.3
"""Protest intensity needed for riot conditions."""
RIOT_UNLUST_THRESHOLD: float = 0.5
"""Systemic unhappiness threshold for riot conditions."""
RIOT_FOOD_THRESHOLD: float = 0.3
"""Food availability below this enables riot conditions."""
RIOT_JOIN_CHANCE: float = 0.3
"""Probability an eligible agent joins a riot."""

# === Environmental Events ===
ENV_CYCLE_MIN_INTERVAL: int = 15
"""Minimum ticks between environmental events."""
ENV_CYCLE_MAX_INTERVAL: int = 40
"""Maximum ticks between environmental events."""
ENV_FAMINE_CHANCE: float = 0.15
"""Probability of a famine event when a cycle triggers."""
ENV_DROUGHT_CHANCE: float = 0.15
"""Probability of a drought event when a cycle triggers."""
ENV_ABUNDANCE_CHANCE: float = 0.10
"""Probability of an abundance (bountiful harvest) event."""
ENV_MILD_SHORTAGE_CHANCE: float = 0.25
"""Probability of a mild shortage event."""
ENV_FAMINE_DROP: float = 0.4
"""Total food availability drop during a famine event."""
ENV_DROUGHT_DROP: float = 0.4
"""Total water availability drop during a drought event."""
ENV_ABUNDANCE_FOOD_BOOST: float = 0.15
"""Food availability boost during an abundance event."""
ENV_ABUNDANCE_WATER_BOOST: float = 0.10
"""Water availability boost during an abundance event."""
ENV_MILD_DROP_MIN: float = 0.05
"""Minimum food/water drop during a mild shortage."""
ENV_MILD_DROP_MAX: float = 0.10
"""Maximum food/water drop during a mild shortage."""
ENV_FAMINE_DURATION: int = 10
"""Total duration of a famine event in ticks."""
ENV_DROUGHT_DURATION: int = 10
"""Total duration of a drought event in ticks."""
ENV_MILD_DURATION: int = 5
"""Duration of a mild shortage event in ticks."""
ENV_EVENT_PHASE_IN: int = 3
"""Number of ticks to phase in an event's effect."""
ENV_REGRESSION_RATE: float = 0.005
"""Per-tick regression rate toward default food/water availability."""
ENV_FOOD_DEFAULT: float = 0.85
"""Default (baseline) food availability."""
ENV_WATER_DEFAULT: float = 0.90
"""Default (baseline) water availability."""
ENV_NEED_DECAY_FOOD_MULTIPLIER: float = 1.2
"""Food decay multiplier during crisis (food_availability < 0.4)."""
ENV_NEED_DECAY_WATER_MULTIPLIER: float = 1.2
"""Water decay multiplier during crisis (water_availability < 0.4)."""

# === Metrics ===
NEWS_INTERVAL_TICKS: int = 10

# === Age lifecycle ===
AGE_CHILD_MAX: int = 18
"""Maximum age for the child bracket (inclusive)."""

AGE_YOUNG_ADULT_MAX: int = 40
"""Maximum age for the young adult bracket (inclusive)."""

AGE_MIDDLE_ADULT_MAX: int = 65
"""Maximum age for the middle adult bracket (inclusive)."""

AGE_ELDERLY_MAX: int = 1000
"""Maximum age for the elderly bracket — effectively no cap."""

AGE_MORTALITY_BASE: float = 0.0001
"""Base per-tick mortality probability for all agents. Reduced from 0.001
because 0.001/tick is ~36% per year which is far too high."""

AGE_MORTALITY_ELDERLY: float = 0.001
"""Additional per-tick mortality probability for elderly agents. Reduced
from 0.008 (combined with base = 0.009/tick, ~97% per year).
Tuned 2026-07-11 for population stability."""

DEATH_INHERITANCE_FRACTION: float = 0.7
"""Fraction of a parent's wealth passed to children on death."""

BIRTH_CHANCE_BASE: float = 0.005
"""Goldilocks rate (v2 engine calibration 2026-07-11). Sweep [0.0001-0.01] showed 0.005 produces
stable population: 62/80 at 500t, 30/80 at 1000t. Below 0.005 leads to extinction; above leads to explosion.
0.0001 was extinction; 0.005 is the stable middle ground."""
"""Base per-tick probability of giving birth for eligible agents. Reduced
from 0.0002 (still produced 200+ births in 200 ticks = 3.5x pop growth).
Tuned 2026-07-11 for population stability."""

MIN_ADULT_AGE_FOR_BIRTH: int = 18
"""Minimum age for an agent to be eligible for reproduction."""

MAX_REPRODUCTION_AGE: int = 50
"""Maximum age for an agent to be eligible for reproduction."""

AGE_PROGRESSION_INTERVAL: float = 0.1
"""Years of aging per tick (0.1 = 200 ticks ≈ 20 simulated years). 1.0 was
catastrophic: a 40-year-old reached elderly (66) by tick 26."""

# --- Marriage constants ---
MARRIAGE_BASE_PROBABILITY: float = 0.05
"""Base per-tick probability of marriage for eligible agents."""

MARRIAGE_AGE_MIN: int = 19
"""Minimum age for an agent to be eligible for marriage."""

MARRIAGE_AGE_MAX: int = 65
"""Maximum age for an agent to be eligible for marriage."""

MARRIAGE_MAX_AGE_GAP: int = 15
"""Maximum absolute age gap for a compatible marriage pair."""

MARRIAGE_WEALTH_COMPAT: float = 0.3
"""Relative wealth tolerance for wealth compatibility between partners."""

MARRIAGE_GRID_PROXIMITY: int = 3
"""Maximum grid distance (Chebyshev) for marriage eligibility."""

# === Family support ===
PARENT_EDUCATION_SUPPORT: float = 15.0
"""Money per tick parent gives to child in education."""

CHILD_ELDERLY_SUPPORT: float = 8.0
"""Money per tick child gives to elderly parent."""

SUPPORT_FAMILY_EDUCATION_AGE_MAX: int = 25
"""Parents support until child is 25."""

SUPPORT_FAMILY_PARENT_AGE_MIN: int = 65
"""Children support parents when 65+."""

SUPPORT_FAMILY_PROBABILITY: float = 0.10
"""Chance per tick if eligible."""

SUPPORT_FAMILY_UNLUST_RELIEF: float = 0.02
"""Unlust reduction for both parties."""

# === Inter-Community Tension ===
TENSION_BASE_DECAY: float = 0.01
"""Per-tick decay applied to all inter-community tension scores."""
TENSION_WEALTH_GAP_WEIGHT: float = 0.3
"""Weight of wealth disparity in tension computation."""
TENSION_PROXIMITY_WEIGHT: float = 0.2
"""Weight of grid proximity in tension computation."""
TENSION_CRIME_ESCALATION: float = 0.1
"""Tension increase when a crime occurs between communities."""
CONFLICT_PROPERTY_DAMAGE_THRESHOLD: float = 0.5
"""Tension above which property damage / vandalism events can trigger."""
CONFLICT_HATE_CRIME_THRESHOLD: float = 0.6
"""Tension above which hate crime events can trigger."""
CONFLICT_GANG_RECRUIT_THRESHOLD: float = 0.3
"""Tension above which gang recruitment dynamics can activate."""

# --- Grid constants ---
GRID_SIZE: int = 20
"""Size of the N×N toroidal grid. Agents wrap around edges."""

INTERACTION_RADIUS: int = 2
"""Maximum Euclidean distance for agent-to-agent interaction on the grid."""

# === Rumor spreading ===
RUMOR_DOMINANCE_THRESHOLD: float = 0.6
"""Minimum dominance_urge needed to spread a rumor."""
RUMOR_MAGNITUDE_MIN: float = 0.05
"""Minimum reputation penalty from a rumor."""
RUMOR_MAGNITUDE_MAX: float = 0.15
"""Maximum reputation penalty from a rumor."""
RUMOR_DECAY_PER_TICK: float = 0.1
"""Fraction of rumor magnitude decayed per tick."""
RUMOR_PROPAGATION_CHANCE: float = 0.3
"""Chance per contact per tick that a rumor spreads."""
RUMOR_BFS_DEPTH: int = 3
"""Maximum BFS depth for rumor propagation through social connections."""

# === Gang system ===
GANG_FORMATION_MIN_MEMBERS: int = 5
"""Minimum agents in proximity to form a gang."""
GANG_FORMATION_PROBABILITY: float = 0.1
"""Probability that an eligible cluster forms a gang per tick."""
GANG_RECRUIT_BASE_CHANCE: float = 0.05
"""Base probability per tick of recruiting a marginalized agent."""
GANG_EXTORT_AMOUNT: float = 15.0
"""Amount of money taken per extortion action."""
GANG_POWER_MEMBER_WEIGHT: float = 0.1
"""Weight per member in gang power calculation."""
GANG_POWER_WEALTH_WEIGHT: float = 0.01
"""Weight per unit wealth in gang power calculation."""
GANG_MAX_NAME_LENGTH: int = 20
"""Maximum length of a generated gang name."""

# === Purpose/Meaning (Maslow Layer 5) ===
PURPOSE_ASSIGN_CHANCE: float = 0.05
"""Per-tick probability of assigning a purpose to an eligible agent."""

PURPOSE_FULFILLMENT_GAIN: float = 0.02
"""Gain in purpose_fulfillment per relevant action."""

PURPOSE_FULFILLMENT_DECAY: float = 0.002
"""Per-tick decay in purpose_fulfillment when no relevant action taken."""

PURPOSE_HAPPINESS_BONUS: float = 0.05
"""Happiness bonus for agents with high purpose fulfillment."""

PURPOSE_DESPAIR_RISK: float = 0.01
"""Additional despair risk for agents with low purpose fulfillment."""

EXISTENTIAL_DEATH_CHANCE: float = 0.001
"""Per-tick chance of death from existential despair when conditions are met."""

# === White-collar crime (fraud) ===
FRAUD_MIN_WEALTH: float = 200.0
"""Minimum wealth for fraud eligibility."""
FRAUD_MORALITY_MAX: float = 0.3
"""Maximum morality for fraud eligibility."""
FRAUD_GAIN_MIN: float = 30.0
"""Minimum money gained from fraud."""
FRAUD_GAIN_MAX: float = 80.0
"""Maximum money gained from fraud."""
FRAUD_FINE_MULTIPLIER: float = 0.5
"""Fraction of fraud gain paid as fine when detected."""
FRAUD_NOTORIETY_GAIN: float = 0.2
"""Notoriety gain from undetected fraud."""

# ── Media Engine ──────────────────────────────────────────
MEDIA_SENSATIONALISM_BASE: float = 0.3
"""Baseline sensationalism level for media articles."""
MEDIA_TRUST_BASE: float = 0.6
"""Baseline public trust in media (0.0 to 1.0)."""
MEDIA_FAKE_NEWS_CHANCE: float = 0.15
"""Probability per eligible tick that a fake news article is generated."""
MEDIA_SENTIMENT_DECAY: float = 0.02
"""Per-tick decay rate for media sentiment toward zero."""
