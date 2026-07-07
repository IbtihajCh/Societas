"""
SOCIETAS Simulation Engine
===========================

Core deterministic simulation engine for SOCIETAS.

This module implements the agent-based simulation with:
- Autonomous agents with psychological traits
- Economic systems (employment, wealth, markets)
- Needs fulfillment and psychology
- Crime and enforcement
- Policy application
- Deterministic tick-based execution

All simulation logic is deterministic and does NOT use LLMs.
AI escalation happens through the backend when ambiguity is detected.
"""

from simulation.engine.simulation_engine import SimulationEngine
from simulation.engine.config import SimulationConfig

__version__ = "0.1.0"
__all__ = [
    "SimulationEngine",
    "SimulationConfig",
]
