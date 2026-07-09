"""
Shared Schemas Module
=====================

Provides all data schemas used across the SOCIETAS simulation platform.
"""

from shared.schemas.agent_state import (
    AgentState,
    AgentTraits,
    AgentNeeds,
    AgentEmotions,
    AgentResources,
    AgentDecisionScores,
)
from shared.schemas.simulation_state import SimulationState
from shared.schemas.economy_state import EconomyState
from shared.schemas.crime_state import CrimeState
from shared.schemas.needs_state import NeedsState
from shared.schemas.psychology_state import PsychologyState
from shared.schemas.policy import Policy, GovernmentPolicy, PolicyWeights, ImpactDelta
from shared.schemas.decision import DecisionRequest, DecisionResponse, DecisionOption
from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.schemas.metrics import SimulationMetrics, MetricDataPoint
from shared.schemas.dashboard_state import DashboardState
from shared.schemas.tick_result import TickResult, AgentActionResult
from shared.schemas.population_stats import PopulationStatistics

__all__ = [
    "AgentState",
    "AgentTraits",
    "AgentNeeds",
    "AgentEmotions",
    "AgentResources",
    "AgentDecisionScores",
    "SimulationState",
    "EconomyState",
    "CrimeState",
    "NeedsState",
    "PsychologyState",
    "Policy",
    "GovernmentPolicy",
    "PolicyWeights",
    "ImpactDelta",
    "DecisionRequest",
    "DecisionResponse",
    "DecisionOption",
    "NewsEvent",
    "SpotlightNarration",
    "SimulationMetrics",
    "MetricDataPoint",
    "DashboardState",
    "TickResult",
    "AgentActionResult",
    "PopulationStatistics",
]
