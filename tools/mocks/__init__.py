"""
Mocks Package
==============

Mock implementations for parallel development.

Provides mock versions of core interfaces so teams can develop
independently without waiting for other modules to be complete.
"""

from tools.mocks.mock_simulation_engine import MockSimulationEngine
from tools.mocks.mock_ai_router import MockAIRouter

__all__ = [
    "MockSimulationEngine",
    "MockAIRouter",
]
