"""
AI Router Interface
===================

Abstract interface for AI model routing in the three-model Gemma 4 setup:

- Gemma 4 E2B (port 8001): Agent decisions (temp=0.0, batch-capable, ~27 calls/tick)
- Gemma 4 26B A4B (port 8002): Moral reasoning with thinking mode (temp=0.2, 1-2 calls/tick)
- Gemma 4 31B (port 8003): Governance advisory & policy translation (temp=0.3, thinking ON)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from shared.schemas.agent_state import AgentState
from shared.schemas.decision import DecisionRequest, DecisionResponse
from shared.schemas.policy import GovernmentPolicy, ImpactDelta, PolicyWeights
from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import WealthClass


class IAIRouter(ABC):
    """
    Abstract interface for the AI router in the three-model Gemma 4 architecture.
    
    Routes requests to the appropriate Gemma 4 model:
    - E2B (port 8001): Agent decisions (agent_decide, agent_decide_batch)
    - 26B A4B (port 8002): Moral reasoning (moral_reasoning, moral_reasoning_batch)
    - 31B (port 8003): Governance & policy (governance_advisory, translate_policy)
    
    All methods must remain deterministic given the same inputs (even LLM outputs
    are repeatable with temp=0.0 for E2B and fixed seeds for thinking models).
    """
    
    @abstractmethod
    def translate_policy(
        self,
        policy_text: str,
        existing_weights: PolicyWeights,
        world_state: SimulationState,
    ) -> Tuple[PolicyWeights, Dict[WealthClass, ImpactDelta], Dict[str, Any]]:
        """Translate a natural language policy into structured effects.

        Uses the 31B model to interpret policy text and generate:
        - Modified PolicyWeights
        - ImpactDeltas per wealth class
        - World-level changes (tax rate, welfare, food events)

        Args:
            policy_text: Natural language policy description.
            existing_weights: Current policy weights to modify.
            world_state: Current world state for context.

        Returns:
            Tuple of (new_weights, impact_deltas_by_class, world_changes_dict).
            The world_changes dict may contain: new_tax_rate, welfare_on, food_event.
        """
        ...
    
    @abstractmethod
    def tie_break(self, request: DecisionRequest) -> DecisionResponse:
        """
        Resolve an ambiguous decision using AI.
        
        Args:
            request: DecisionRequest with agent state and options
            
        Returns:
            DecisionResponse with resolved decision
        """
        ...
    
    @abstractmethod
    def generate_news(self, events: list, state_deltas: dict) -> NewsEvent:
        """
        Generate a news article from simulation events.
        
        Args:
            events: List of events to narrate
            state_deltas: Changes in world state
            
        Returns:
            Generated NewsEvent
        """
        ...
    
    @abstractmethod
    def generate_persona(self, traits: dict) -> str:
        """
        Generate a natural language persona from traits.
        
        Args:
            traits: Dictionary of trait values
            
        Returns:
            Natural language persona string
        """
        ...
    
    @abstractmethod
    def generate_narration(self, agent_id: str, events: list) -> SpotlightNarration:
        """
        Generate a spotlight narration for an agent.
        
        Args:
            agent_id: ID of the agent to spotlight
            events: Recent events for the agent
            
        Returns:
            Generated SpotlightNarration
        """
        ...
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the AI router is available.
        
        Returns:
            True if available, False otherwise
        """
        ...

    @abstractmethod
    def agent_decide(
        self,
        agent_state: AgentState,
        world: SimulationState,
        nearby_counts: Dict[str, int],
    ) -> Dict[str, Any]:
        """Ask the E2B model to decide an agent's action.

        Args:
            agent_state: Full agent state (needs, traits, emotions, resources, etc).
            world: Current world state (food availability, tax rate, etc).
            nearby_counts: Counts of nearby agents by category (agents, protesters, needy, sad, generous).

        Returns:
            Dict with keys: "action" (str matching ActionType), "feeling" (str), "reason" (str).
        """
        ...

    @abstractmethod
    def agent_decide_batch(
        self,
        requests: List[Tuple[AgentState, SimulationState, Dict[str, int]]],
    ) -> List[Dict[str, Any]]:
        """Batch version of agent_decide for efficient vLLM inference.

        Args:
            requests: List of (agent_state, world, nearby_counts) tuples.

        Returns:
            List of decision dicts, same order as input.
        """
        ...

    @abstractmethod
    def moral_reasoning(
        self,
        agent_state: AgentState,
        world: SimulationState,
        dilemma_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ask the 26B A4B model (with thinking mode) to reason through a moral dilemma.

        Args:
            agent_state: Full agent state.
            world: Current world state.
            dilemma_context: Context describing the dilemma (type, conflicting values).

        Returns:
            Dict with keys: "action" (str), "reasoning" (str), "feeling" (str).
        """
        ...

    @abstractmethod
    def moral_reasoning_batch(
        self,
        requests: List[Tuple[AgentState, SimulationState, Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Batch version of moral_reasoning.

        Args:
            requests: List of (agent_state, world, dilemma_context) tuples.

        Returns:
            List of reasoning dicts, same order as input.
        """
        ...

    @abstractmethod
    def governance_advisory(
        self,
        world_state: SimulationState,
        active_policies: List[GovernmentPolicy],
    ) -> Dict[str, Any]:
        """Ask the 31B model for proactive governance advice.

        Args:
            world_state: Current simulation world state.
            active_policies: Currently active government policies.

        Returns:
            Dict with keys: "assessment" (str), "recommendation" (str), "watch_items" (List[str]).
        """
        ...
