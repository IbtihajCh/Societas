"""
Metrics DTO
===========

Data Transfer Objects for metrics-related API communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from shared.types.aliases import TickNumber


@dataclass
class MetricPointDTO:
    """
    DTO for a single metric data point.
    
    Attributes:
        tick: Tick number
        value: Metric value
    """
    
    tick: TickNumber
    value: float


@dataclass
class MetricsResponseDTO:
    """
    DTO for metrics response.
    
    Attributes:
        current_tick: Current tick number
        population: Population time series
        economy: Economic metrics time series
        crime: Crime metrics time series
        happiness: Happiness metrics time series
        summary: Summary statistics
    """
    
    current_tick: TickNumber = TickNumber(0)
    population: List[MetricPointDTO] = field(default_factory=list)
    economy: List[MetricPointDTO] = field(default_factory=list)
    crime: List[MetricPointDTO] = field(default_factory=list)
    happiness: List[MetricPointDTO] = field(default_factory=list)
    summary: Dict[str, float] = field(default_factory=dict)
