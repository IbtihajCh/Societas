"""
Simulation State Schema
=======================

Defines the world state container for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import TickNumber
from shared.schemas.economy_state import EconomyState
from shared.schemas.crime_state import CrimeState
from shared.schemas.needs_state import NeedsState
from shared.schemas.psychology_state import PsychologyState


@dataclass
class SimulationState:
    """
    Complete world state for the SOCIETAS simulation.
    
    Contains all global state variables that describe the current
    state of the simulated world. Updated each tick by the simulation engine.
    
    Attributes:
        time_step: Current simulation tick number
        population: Current total population
        economic_health: Overall economic health (0.0 to 1.0)
        social_cohesion: Social cohesion index (0.0 to 1.0)
        environmental_quality: Environmental quality index (0.0 to 1.0)
        public_order: Public order/safety index (0.0 to 1.0)
        innovation_index: Innovation/progress index (0.0 to 1.0)
        unlust: Systemic dissatisfaction level (0.0 to 1.0)
        morality: Average societal morality (0.0 to 1.0)
        economy: Detailed economic state
        crime: Detailed crime state
        needs: Aggregated needs fulfillment state
        psychology: Aggregated psychological state
        active_policy_ids: List of currently active policy IDs
        metadata: Additional state metadata
    """
    
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
    active_policy_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)
    # Extended world state fields per Project Guide and ADR-005:
    food_availability: float = 0.85
    water_availability: float = 0.90
    crime_rate: float = 0.05
    protest_intensity: float = 0.0
    unemployment_rate: float = 0.10
    tax_rate: float = 0.15
    welfare_enabled: bool = False
    welfare_amount: float = 8.0
    national_debt: float = 0.0
    remittance_income: float = 0.08
    energy_price: float = 0.60
    job_demand: Dict[str, int] = field(default_factory=dict)
    job_salary_multipliers: Dict[str, float] = field(default_factory=dict)
    active_env_events: List[dict] = field(default_factory=list)
    media_state: dict = field(default_factory=lambda: {
        "articles": [],
        "trust_in_media": 0.6,
        "sensationalism": 0.3,
        "fake_news_level": 0.0,
        "sentiment_gov": 0.0,
        "sentiment_economy": 0.0,
    })
