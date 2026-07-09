"""
Agents Module
=============

Agent implementation, management, and needs calculation.
"""

from simulation.agents.agent import Agent
from simulation.agents.agent_registry import AgentRegistry
from simulation.agents.needs_calculator import check_death, decay_needs, derive_wealth_class

__all__ = [
    "Agent",
    "AgentRegistry",
    "check_death",
    "decay_needs",
    "derive_wealth_class",
]
