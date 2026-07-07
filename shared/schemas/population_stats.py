"""
Population Statistics Schema
============================

Defines the population statistics schema for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict

from shared.types.enums import WealthClass, EmploymentStatus, EmotionType


@dataclass
class PopulationStatistics:
    """
    Population-level statistics for the SOCIETAS simulation.
    
    Aggregated statistics about the population for reporting
    and analysis purposes.
    
    Attributes:
        total_population: Total number of agents
        wealth_distribution: Distribution across wealth classes
        employment_distribution: Distribution across employment statuses
        emotion_distribution: Distribution of primary emotions
        average_age: Average agent age
        average_morality: Average morality level
        average_happiness: Average happiness level
        crime_rate: Current crime rate
        birth_rate: Current birth rate
        death_rate: Current death rate
        migration_rate: Current migration rate
    """
    
    total_population: int = 0
    wealth_distribution: Dict[WealthClass, int] = field(default_factory=dict)
    employment_distribution: Dict[EmploymentStatus, int] = field(default_factory=dict)
    emotion_distribution: Dict[EmotionType, int] = field(default_factory=dict)
    average_age: float = 0.0
    average_morality: float = 0.5
    average_happiness: float = 0.5
    crime_rate: float = 0.0
    birth_rate: float = 0.0
    death_rate: float = 0.0
    migration_rate: float = 0.0
