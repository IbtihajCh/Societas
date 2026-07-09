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
        unlust: Unlust time series
        morality: Morality time series
        protest_intensity: Protest intensity time series
        action_frequencies: Frequency of each action type
        emotion_distribution: Distribution of emotions across agents
        summary: Summary statistics
    """
    
    current_tick: TickNumber = TickNumber(0)
    population: List[MetricPointDTO] = field(default_factory=list)
    economy: List[MetricPointDTO] = field(default_factory=list)
    crime: List[MetricPointDTO] = field(default_factory=list)
    happiness: List[MetricPointDTO] = field(default_factory=list)
    unlust: List[MetricPointDTO] = field(default_factory=list)
    morality: List[MetricPointDTO] = field(default_factory=list)
    protest_intensity: List[MetricPointDTO] = field(default_factory=list)
    action_frequencies: Dict[str, int] = field(default_factory=dict)
    emotion_distribution: Dict[str, int] = field(default_factory=dict)
    summary: Dict[str, float] = field(default_factory=dict)
