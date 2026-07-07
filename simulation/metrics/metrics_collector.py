"""
Metrics Collector
=================

Collects and aggregates simulation metrics.
"""

from shared.schemas.metrics import SimulationMetrics, MetricDataPoint
from shared.types.aliases import TickNumber


class MetricsCollector:
    """
    Collects and aggregates simulation metrics over time.
    
    Maintains time-series data for key simulation indicators.
    
    Attributes:
        _metrics: Current metrics state
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._metrics = SimulationMetrics()
    
    def get_metrics(self) -> SimulationMetrics:
        """
        Get aggregated simulation metrics.
        
        Returns:
            Current SimulationMetrics
        """
        return self._metrics
    
    def record_tick(self, tick: TickNumber, data: dict) -> None:
        """
        Record metrics for a tick.
        
        Args:
            tick: Tick number
            data: Dictionary of metric values
            
        TODO: Implement metric recording
            - Append data points to time series
            - Update summary statistics
        """
        self._metrics.current_tick = tick
        # TODO: Record individual metrics
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics = SimulationMetrics()
