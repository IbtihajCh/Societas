"""
Simulation Configuration
========================

Configuration parameters for the simulation engine.
"""

from dataclasses import dataclass
from typing import Optional

from shared.constants.defaults import (
    DEFAULT_POPULATION_SIZE,
    DEFAULT_SIMULATION_SEED,
    DEFAULT_TICK_RATE_MS,
    DEFAULT_MAX_TICKS,
    DEFAULT_AGENT_LIFESPAN_TICKS,
    DEFAULT_INITIAL_WEALTH,
    DEFAULT_AMBIGUITY_THRESHOLD,
)


@dataclass
class SimulationConfig:
    """
    Configuration for the simulation engine.
    
    Attributes:
        population_size: Initial number of agents
        seed: Random seed for deterministic simulation
        tick_rate_ms: Tick rate in milliseconds
        max_ticks: Maximum number of ticks to simulate
        agent_lifespan_ticks: Average agent lifespan in ticks
        initial_wealth: Starting wealth for new agents
        ambiguity_threshold: Threshold for decision ambiguity detection
        enable_ai_escalation: Whether to enable AI tie-breaking
        log_level: Logging level
    """
    
    population_size: int = DEFAULT_POPULATION_SIZE
    seed: Optional[int] = DEFAULT_SIMULATION_SEED
    tick_rate_ms: int = DEFAULT_TICK_RATE_MS
    max_ticks: int = DEFAULT_MAX_TICKS
    agent_lifespan_ticks: int = DEFAULT_AGENT_LIFESPAN_TICKS
    initial_wealth: float = DEFAULT_INITIAL_WEALTH
    ambiguity_threshold: float = DEFAULT_AMBIGUITY_THRESHOLD
    enable_ai_escalation: bool = True
    log_level: str = "INFO"
