"""
Shared Interfaces Module
========================

Provides abstract interfaces for subsystem contracts.
"""

from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.interfaces.i_agent import IAgent
from shared.interfaces.i_policy_engine import IPolicyEngine
from shared.interfaces.i_ai_router import IAIRouter
from shared.interfaces.i_event_bus import IEventBus
from shared.interfaces.i_data_repository import IDataRepository

__all__ = [
    "ISimulationEngine",
    "IAgent",
    "IPolicyEngine",
    "IAIRouter",
    "IEventBus",
    "IDataRepository",
]
