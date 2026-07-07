"""
AI Router Interface
===================

Abstract interface for AI model routing.
"""

from abc import ABC, abstractmethod
from typing import Optional

from shared.schemas.decision import DecisionRequest, DecisionResponse
from shared.schemas.policy import PolicyWeights
from shared.schemas.news_event import NewsEvent, SpotlightNarration


class IAIRouter(ABC):
    """
    Abstract interface for the AI router.
    
    Defines the contract for routing requests to appropriate AI models.
    """
    
    @abstractmethod
    def translate_policy(self, persona: str, goal: str, context: dict) -> PolicyWeights:
        """
        Translate an agent's policy goal into utility weights.
        
        Args:
            persona: Agent persona description
            goal: Agent's policy goal
            context: Additional context
            
        Returns:
            PolicyWeights representing the goal's utility modifiers
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
