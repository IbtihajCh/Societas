"""
Simulation Metrics Schema
=========================

Defines the simulation metrics schema for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import TickNumber


@dataclass
class MetricDataPoint:
    """
    A single data point in a time series metric.
    
    Attributes:
        tick: Tick number
        value: Metric value
        label: Optional label
    """
    
    tick: TickNumber
    value: float
    label: str = ""


@dataclass
class SimulationMetrics:
    """
    Aggregated simulation metrics for reporting and visualization.
    
    Contains time-series data and summary statistics for the
    simulation's key indicators.
    
    Attributes:
        current_tick: Current simulation tick
        population_history: Population over time
        economic_history: Economic indicators over time
        crime_history: Crime rates over time
        happiness_history: Happiness levels over time
        policy_impact: Impact measurements for active policies
        summary: Summary statistics
        custom_metrics: Additional custom metrics
    """
    
    current_tick: TickNumber = TickNumber(0)
    population_history: List[MetricDataPoint] = field(default_factory=list)
    economic_history: List[MetricDataPoint] = field(default_factory=list)
    crime_history: List[MetricDataPoint] = field(default_factory=list)
    happiness_history: List[MetricDataPoint] = field(default_factory=list)
    policy_impact: Dict[str, List[MetricDataPoint]] = field(default_factory=dict)
    summary: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, List[MetricDataPoint]] = field(default_factory=dict)
