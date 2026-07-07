"""
Needs State Schema
==================

Defines the aggregated needs fulfillment state for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict

from shared.types.enums import NeedType


@dataclass
class NeedsState:
    """
    Aggregated needs fulfillment state of the population.
    
    Tracks how well the population's needs are being met on average.
    
    Attributes:
        average_need_levels: Average need levels across population by type
        fulfillment_rate: Overall need fulfillment rate (0.0 to 1.0)
        unmet_needs_count: Number of agents with critical unmet needs
        most_urgent_need: Most commonly unmet need type
        need_distribution: Distribution of need levels across population
    """
    
    average_need_levels: Dict[NeedType, float] = field(default_factory=dict)
    fulfillment_rate: float = 0.5
    unmet_needs_count: int = 0
    most_urgent_need: NeedType = NeedType.FOOD
    need_distribution: Dict[str, int] = field(default_factory=dict)
