"""
Mock AI Router
===============

Mock implementation of IAIRouter for simulation development.
Returns realistic but static responses without requiring vLLM.
"""

from typing import Dict, Any, Optional, List
from shared.schemas.decision import DecisionRequest, DecisionResponse, DecisionOption
from shared.schemas.policy import PolicyWeights
from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.interfaces.i_ai_router import IAIRouter


class MockAIRouter(IAIRouter):
    """
    Mock AI router for simulation development without vLLM.
    
    Returns deterministic, realistic responses for all AI operations.
    Useful for testing simulation logic without GPU requirements.
    """
    
    def __init__(self):
        self._available: bool = True
    
    def translate_policy(self, persona: str, goal: str, context: dict) -> PolicyWeights:
        """Return mock policy weights."""
        # TODO: Implement with realistic mock weights
        raise NotImplementedError("Mock translate_policy not yet implemented")
    
    def tie_break(self, request: DecisionRequest) -> DecisionResponse:
        """Return mock tie-break decision."""
        # TODO: Implement with realistic mock decision
        raise NotImplementedError("Mock tie_break not yet implemented")
    
    def generate_news(self, events: list, state_deltas: dict) -> NewsEvent:
        """Return mock news event."""
        # TODO: Implement with realistic mock news
        raise NotImplementedError("Mock generate_news not yet implemented")
    
    def generate_persona(self, traits: dict) -> str:
        """Return mock persona description."""
        # TODO: Implement with realistic mock persona
        raise NotImplementedError("Mock generate_persona not yet implemented")
    
    def generate_narration(self, agent_id: str, events: list) -> SpotlightNarration:
        """Return mock spotlight narration."""
        # TODO: Implement with realistic mock narration
        raise NotImplementedError("Mock generate_narration not yet implemented")
    
    def is_available(self) -> bool:
        """Check if mock router is available."""
        return self._available
