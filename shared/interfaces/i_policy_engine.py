"""
Policy Engine Interface
=======================

Abstract interface for policy application.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from shared.schemas.policy import Policy, GovernmentPolicy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.interfaces.i_ai_router import IAIRouter


class IPolicyEngine(ABC):
    """
    Abstract interface for the policy engine.
    
    Defines the contract for policy management and effect application.
    """
    
    @abstractmethod
    def apply_policy(
        self,
        policy: Policy,
        ai_router: Optional[IAIRouter] = None,
        world_state: Optional[SimulationState] = None,
    ) -> None:
        """
        Apply a policy to the simulation.
        
        When ai_router is available and the policy has a description, the
        description is translated into structured PolicyWeights and ImpactDeltas.
        Falls back to rule-based keyword matching when the AI router is unavailable.
        
        Args:
            policy: The policy to apply
            ai_router: Optional AI router for LLM-based policy translation
            world_state: Optional world state for translation context
        """
        ...
    
    @abstractmethod
    def revoke_policy(self, policy_id: str) -> None:
        """
        Revoke an active policy.
        
        Args:
            policy_id: ID of the policy to revoke
        """
        ...
    
    @abstractmethod
    def get_active_policies(self) -> List[GovernmentPolicy]:
        """
        Get all active policies.
        
        Returns:
            List of active GovernmentPolicy objects
        """
        ...
    
    @abstractmethod
    def get_policy(self, policy_id: str) -> Optional[GovernmentPolicy]:
        """
        Get a specific policy.
        
        Args:
            policy_id: ID of the policy to retrieve
            
        Returns:
            GovernmentPolicy if found, None otherwise
        """
        ...
    
    @abstractmethod
    def get_aggregate_weights(self) -> PolicyWeights:
        """
        Get the aggregate policy weights from all active policies.
        
        Returns:
            Combined PolicyWeights from all active policies
        """
        ...
    
    @abstractmethod
    def calculate_policy_effect(self, policy: Policy, agent_context: dict) -> dict:
        """
        Calculate the effect of a policy on a specific agent.
        
        Args:
            policy: The policy to evaluate
            agent_context: Agent context for effect calculation
            
        Returns:
            Dictionary of effect values
        """
        ...
