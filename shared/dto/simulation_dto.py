"""
Simulation DTO
==============

Data Transfer Objects for simulation-related API communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
