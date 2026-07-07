"""
Shared Events Module
====================

Provides event definitions for the event bus system.
"""

from shared.events.simulation_events import (
    SimulationEvent,
    TickStartedEvent,
    TickCompletedEvent,
    AgentActedEvent,
    AgentCreatedEvent,
    AgentDeceasedEvent,
    PolicyEnactedEvent,
    AmbiguityDetectedEvent,
)
from shared.events.policy_events import (
    PolicyEvent,
    PolicyCreatedEvent,
    PolicyUpdatedEvent,
    PolicyRevokedEvent,
)
from shared.events.news_events import (
    NewsEvent,
    NewsGeneratedEvent,
    SpotlightGeneratedEvent,
)

__all__ = [
    "SimulationEvent",
    "TickStartedEvent",
    "TickCompletedEvent",
    "AgentActedEvent",
    "AgentCreatedEvent",
    "AgentDeceasedEvent",
    "PolicyEnactedEvent",
    "AmbiguityDetectedEvent",
    "PolicyEvent",
    "PolicyCreatedEvent",
    "PolicyUpdatedEvent",
    "PolicyRevokedEvent",
    "NewsEvent",
    "NewsGeneratedEvent",
    "SpotlightGeneratedEvent",
]
