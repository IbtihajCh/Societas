"""
Decision Schema
===============

Defines decision request and response schemas for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import AgentId, ConfidenceScore
from shared.types.enums import ActionType


@dataclass
class DecisionOption:
    """
    A single option in a decision request.
    
    Represents one possible action with its associated utility scores.
    
    Attributes:
        action: The action type
        label: Human-readable label
        utility_scores: Utility scores by dimension
        base_score: Base deterministic score
    """
    
    action: ActionType
    label: str = ""
    utility_scores: Dict[str, float] = field(default_factory=dict)
    base_score: float = 0.0


@dataclass
class DecisionRequest:
    """
    A request for decision resolution.
    
    Sent when an agent's decision is ambiguous and requires
    AI tie-breaking. Contains the agent state and available options.
    
    Attributes:
        agent_id: ID of the agent making the decision
        state: Current agent state description
        unlust: Current systemic dissatisfaction level
        morality: Current morality level
        options: List of available decision options
        context: Additional context information
    """
    
    agent_id: AgentId
    state: str = ""
    unlust: float = 0.0
    morality: float = 0.5
    options: List[DecisionOption] = field(default_factory=list)
    context: Dict[str, object] = field(default_factory=dict)


@dataclass
class DecisionResponse:
    """
    A resolved decision outcome.
    
    Contains the chosen action, confidence level, and reasoning.
    
    Attributes:
        action: The chosen action type
        confidence: Confidence in the decision (0.0 to 1.0)
        reason: Human-readable reasoning for the decision
        scores: Final utility scores after resolution
        metadata: Additional response metadata
    """
    
    action: ActionType
    confidence: ConfidenceScore = ConfidenceScore(0.5)
    reason: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, object] = field(default_factory=dict)
