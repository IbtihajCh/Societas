"""
Agent Interface
===============

Abstract interface for agent behavior.
"""

from abc import ABC, abstractmethod
from typing import Optional

from shared.types.aliases import AgentId
from shared.types.enums import ActionType
from shared.schemas.agent_state import AgentState


class IAgent(ABC):
    """
    Abstract interface for agent behavior.
    
    Defines the contract for agent decision-making and behavior.
    """
    
    @abstractmethod
    def evaluate_needs(self) -> None:
        """Evaluate and update agent needs based on current state."""
        ...
    
    @abstractmethod
    def calculate_utility_scores(self) -> None:
        """Calculate utility scores for all possible actions."""
        ...
    
    @abstractmethod
    def select_action(self) -> ActionType:
        """
        Select the best action based on utility scores.
        
        Returns:
            The selected ActionType
        """
        ...
    
    @abstractmethod
    def execute_action(self, action: ActionType) -> None:
        """
        Execute the selected action and update agent state.
        
        Args:
            action: The action to execute
        """
        ...
    
    @abstractmethod
    def get_state(self) -> AgentState:
        """
        Get the current agent state.
        
        Returns:
            Current AgentState
        """
        ...
    
    @abstractmethod
    def get_id(self) -> AgentId:
        """
        Get the agent's unique identifier.
        
        Returns:
            AgentId
        """
        ...
    
    @abstractmethod
    def is_alive(self) -> bool:
        """
        Check if the agent is still alive.
        
        Returns:
            True if alive, False otherwise
        """
        ...
