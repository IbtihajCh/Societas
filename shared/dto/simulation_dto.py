"""
Simulation DTO
==============

Data Transfer Objects for simulation-related API communication.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared.types.aliases import TickNumber


@dataclass
class SimulationStatusDTO:
    """
    DTO for simulation status.
    
    Attributes:
        tick: Current tick number
        is_running: Whether simulation is running
        speed: Current simulation speed
        population: Current population
        population: Current population
    """
    
    tick: TickNumber = TickNumber(0)
    is_running: bool = False
    speed: float = 1.0
    population: int = 0


@dataclass
class SimulationStartRequestDTO:
    """
    DTO for simulation start request.
    
    Attributes:
        population_size: Initial population size
        seed: Random seed for determinism
        speed: Simulation speed multiplier
        config: Additional configuration
    """
    
    population_size: int = 1000
    seed: Optional[int] = None
    speed: float = 1.0
    config: Dict[str, object] = field(default_factory=dict)
    enable_ai: bool = False


@dataclass
class SimulationStateResponseDTO:
    """
    DTO for simulation state response.
    
    Attributes:
        tick: Current tick number
        population: Current population
        economic_health: Economic health index
        social_cohesion: Social cohesion index
        environmental_quality: Environmental quality index
        public_order: Public order index
        innovation_index: Innovation index
        unlust: Systemic dissatisfaction
        morality: Average morality
        food_availability: Food availability level
        water_availability: Water availability level
        crime_rate: Current crime rate
        protest_intensity: Current protest intensity
        unemployment_rate: Current unemployment rate
        tax_rate: Current tax rate
        welfare_enabled: Whether welfare is enabled
        welfare_amount: Welfare benefit amount
    """
    
    tick: TickNumber = TickNumber(0)
    population: int = 0
    economic_health: float = 0.5
    social_cohesion: float = 0.5
    environmental_quality: float = 0.5
    public_order: float = 0.5
    innovation_index: float = 0.5
    unlust: float = 0.0
    morality: float = 0.5
    food_availability: float = 0.85
    water_availability: float = 0.90
    crime_rate: float = 0.05
    protest_intensity: float = 0.0
    unemployment_rate: float = 0.10
    tax_rate: float = 0.15
    welfare_enabled: bool = False
    welfare_amount: float = 8.0
    # Diagnostic metrics
    duration_ms: float = 0.0
    ai_calls: int = 0
    ambiguity_count: int = 0
    state_hash: str = ""
    action_counts: Dict[str, int] = field(default_factory=dict)
    wealth_stratified: Dict[str, float] = field(default_factory=dict)
    llm_log: List[Dict[str, Any]] = field(default_factory=list)
    news_articles: List[Dict[str, Any]] = field(default_factory=list)
