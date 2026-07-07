"""
Tick Scheduler
==============

Manages tick execution timing and ordering.
"""

from typing import List

from shared.types.aliases import TickNumber
from simulation.agents.agent import Agent


class TickScheduler:
    """
    Scheduler for tick execution.
    
    Determines the order in which agents are processed each tick.
    Ensures deterministic execution order.
    
    Attributes:
        _execution_order: List of agents in execution order
    """
    
    def __init__(self):
        """Initialize tick scheduler."""
        self._execution_order: List[Agent] = []
    
    def schedule_agents(self, agents: List[Agent]) -> None:
        """
        Schedule agents for execution in a tick.
        
        Args:
            agents: List of agents to schedule
            
        TODO: Implement scheduling logic
            - Sort agents by deterministic criteria
            - Store execution order
        """
        self._execution_order = agents
    
    def get_execution_order(self) -> List[Agent]:
        """
        Get the execution order for the current tick.
        
        Returns:
            List of agents in execution order
        """
        return self._execution_order
    
    def reset(self) -> None:
        """Reset the scheduler."""
        self._execution_order = []
