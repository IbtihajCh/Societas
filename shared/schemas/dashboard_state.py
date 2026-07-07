"""
Dashboard State Schema
======================

Defines the dashboard state schema for the SOCIETAS frontend.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import TickNumber
from shared.schemas.simulation_state import SimulationState
from shared.schemas.metrics import SimulationMetrics
from shared.schemas.news_event import NewsEvent
from shared.schemas.policy import GovernmentPolicy


@dataclass
class DashboardState:
    """
    Complete state payload for the frontend dashboard.
    
    Contains all data needed to render the dashboard UI,
    including simulation state, metrics, news, and policies.
    
    Attributes:
        simulation_state: Current simulation world state
        metrics: Aggregated simulation metrics
        recent_news: Recent news events
        active_policies: Currently active government policies
        tick: Current tick number
        is_running: Whether the simulation is currently running
        simulation_speed: Current simulation speed multiplier
        selected_agent_id: Currently selected agent (if any)
        notifications: Dashboard notifications
    """
    
    simulation_state: SimulationState = field(default_factory=SimulationState)
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)
    recent_news: List[NewsEvent] = field(default_factory=list)
    active_policies: List[GovernmentPolicy] = field(default_factory=list)
    tick: TickNumber = TickNumber(0)
    is_running: bool = False
    simulation_speed: float = 1.0
    selected_agent_id: Optional[str] = None
    notifications: List[str] = field(default_factory=list)
