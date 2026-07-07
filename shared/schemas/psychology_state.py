"""
Psychology State Schema
=======================

Defines the aggregated psychological state for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict

from shared.types.enums import EmotionType


@dataclass
class PsychologyState:
    """
    Aggregated psychological state of the population.
    
    Tracks emotional and psychological well-being of the population.
    
    Attributes:
        average_morality: Average morality across population (0.0 to 1.0)
        average_happiness: Average happiness level (0.0 to 1.0)
        average_stress: Average stress level (0.0 to 1.0)
        emotional_distribution: Distribution of primary emotions
        mental_health_index: Overall mental health index (0.0 to 1.0)
        social_satisfaction: Average social satisfaction (0.0 to 1.0)
        life_satisfaction: Average life satisfaction (0.0 to 1.0)
    """
    
    average_morality: float = 0.5
    average_happiness: float = 0.5
    average_stress: float = 0.3
    emotional_distribution: Dict[EmotionType, int] = field(default_factory=dict)
    mental_health_index: float = 0.5
    social_satisfaction: float = 0.5
    life_satisfaction: float = 0.5
