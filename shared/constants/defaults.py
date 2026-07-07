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
