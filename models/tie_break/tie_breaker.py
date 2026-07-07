"""
Tie Breaker
===========

Resolves ambiguous decisions using AI.
"""

from shared.schemas.decision import DecisionRequest, DecisionResponse
from models.router.config import AIConfig


class TieBreaker:
    """
    Resolves ambiguous agent decisions using AI.
    
    Uses the tie-break prompt to make nuanced decisions
    when deterministic scoring results in ambiguity.
    
    Attributes:
        config: AI configuration
    """
    
    def __init__(self, config: AIConfig):
        """
        Initialize the tie breaker.
        
        Args:
            config: AI configuration
        """
        self.config = config
    
    def resolve(self, request: DecisionRequest) -> DecisionResponse:
        """
        Resolve an ambiguous decision.
        
        Args:
            request: DecisionRequest with agent state and options
            
        Returns:
            DecisionResponse with resolved decision
            
        TODO: Implement tie-breaking
            - Load tie-break.md prompt
            - Render template with request data
            - Call vLLM API with temperature 0.2
            - Parse JSON response
            - Validate output schema
            - Return DecisionResponse
        """
        # TODO: Implement
        return DecisionResponse()
