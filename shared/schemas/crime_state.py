"""
Crime State Schema
==================

Defines the crime and enforcement state for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CrimeState:
    """
    Crime and law enforcement state of the simulated world.
    
    Tracks crime rates, enforcement effectiveness, and public safety.
    
    Attributes:
        overall_crime_rate: Overall crime rate (0.0 to 1.0)
        crime_by_type: Crime rates broken down by type
        enforcement_effectiveness: Law enforcement effectiveness (0.0 to 1.0)
        incarceration_rate: Percentage of population incarcerated (0.0 to 1.0)
        public_safety_index: Public perception of safety (0.0 to 1.0)
        crime_victims_total: Total number of crime victims
        crimes_reported: Total crimes reported this tick
        crimes_resolved: Total crimes resolved this tick
    """
    
    overall_crime_rate: float = 0.05
    crime_by_type: Dict[str, float] = field(default_factory=dict)
    enforcement_effectiveness: float = 0.7
    incarceration_rate: float = 0.01
    public_safety_index: float = 0.8
    crime_victims_total: int = 0
    crimes_reported: int = 0
    crimes_resolved: int = 0
