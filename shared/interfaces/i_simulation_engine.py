"""
Simulation Engine Interface
============================

Abstract interface for the simulation engine. Defines the lifecycle contract:
start() MUST be called before tick().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from shared.interfaces.i_ai_router import IAIRouter
from shared.types.aliases import AgentId, TickNumber
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.metrics import SimulationMetrics
from shared.schemas.tick_result import TickResult
from shared.schemas.policy import Policy


class ISimulationEngine(ABC):
    """
    Abstract interface for the SOCIETAS simulation engine.
    
    Defines the contract that all simulation engine implementations
    must fulfill. The simulation engine is responsible for managing
    the world state, processing ticks, and coordinating subsystems.
    
    Lifecycle:
        1. Call start() to initialize agents, seed RNG, and optionally connect AI router.
        2. Call tick() repeatedly to advance the simulation.
        3. Call reset() to return to initial state.
        
        start() MUST be called before tick() — raises RuntimeError otherwise.
    """
    
    @abstractmethod
    def tick(self) -> TickResult:
        """
        Advance the simulation by one tick.
        
        Processes all agent decisions, updates world state,
        and returns the results of the tick.
        
        Returns:
            TickResult containing all changes and events from the tick
        """
        ...
    
    @abstractmethod
    def reset(self, seed: Optional[int] = None) -> None:
        """
        Reset the simulation to initial state.
        
        Args:
            seed: Optional random seed for deterministic replay
        """
        ...
    
    @abstractmethod
    def apply_policy(self, policy: Policy) -> None:
        """
        Apply a government policy to the simulation.
        
        Args:
            policy: The policy to apply
        """
        ...
    
    @abstractmethod
    def revoke_policy(self, policy_id: str) -> None:
        """
        Revoke an active government policy.
        
        Args:
            policy_id: ID of the policy to revoke
        """
        ...
    
    @abstractmethod
    def get_state(self) -> SimulationState:
        """
        Get the current world state.
        
        Returns:
            Current SimulationState
        """
        ...
    
    @abstractmethod
    def get_metrics(self) -> SimulationMetrics:
        """
        Get aggregated simulation metrics.
        
        Returns:
            Current SimulationMetrics
        """
        ...
    
    @abstractmethod
    def get_agent(self, agent_id: AgentId) -> Optional[AgentState]:
        """
        Get the state of a specific agent.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            AgentState if found, None otherwise
        """
        ...
    
    @abstractmethod
    def get_agents(self) -> List[AgentState]:
        """
        Get all active agents.
        
        Returns:
            List of all active AgentState objects
        """
        ...
    
    @abstractmethod
    def get_current_tick(self) -> TickNumber:
        """
        Get the current tick number.
        
        Returns:
            Current TickNumber
        """
        ...
    
    @abstractmethod
    def stop(self) -> None:
        """
        Stop the simulation execution.
        
        Sets the running state to False. Does not reset
        or clear any simulation state.
        """
        ...

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the simulation is currently running.
        
        Returns:
            True if running, False otherwise
        """
        ...

    @abstractmethod
    def start(self, ai_router: Optional[IAIRouter] = None) -> None:
        """Initialize the simulation: create agents, seed RNG, optionally set AI router.

        MUST be called before tick(). Raises RuntimeError if tick() is called
        before start().

        Args:
            ai_router: Optional AI router for LLM-driven decisions. If None,
                uses deterministic fallback for all decisions.
        """
        ...

    @abstractmethod
    def set_ai_router(self, router: IAIRouter) -> None:
        """Set or replace the AI router mid-simulation.

        Allows hot-swapping between MockAIRouter and VLLMRouter without restarting.

        Args:
            router: The AI router to use for subsequent ticks.
        """
        ...
