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
ANGRY_UNLUST_THRESHOLD: float = 0.58
DESPAIR_UNLUST_THRESHOLD: float = 0.82
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
UNLUST_MORALITY_GATE: float = 0.58
UNLUST_NEED_THRESHOLD: float = 0.7

# === Need decay rates (base, before scarcity modifier) ===
FOOD_DECAY_RATE: float = 0.018
WATER_DECAY_RATE: float = 0.014
SLEEP_DECAY_RATE: float = 0.010
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
ECONOMIC_HARDSHIP_DEATH_RATE: float = 0.003

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

# === Metrics ===
NEWS_INTERVAL_TICKS: int = 10

# --- Grid constants ---
GRID_SIZE: int = 20
"""Size of the N×N toroidal grid. Agents wrap around edges."""

INTERACTION_RADIUS: int = 2
"""Maximum Euclidean distance for agent-to-agent interaction on the grid."""
