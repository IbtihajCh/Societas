"""
Tick Result Schema
==================

Defines the tick result schema for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import TickNumber, AgentId, EventId


@dataclass
class AgentActionResult:
    """
    Result of an agent's action during a tick.
    
    Attributes:
        agent_id: ID of the acting agent
        action: Action taken
        outcome: Outcome description
        score_delta: Change in agent's state scores
    """
    
    agent_id: AgentId
    action: str = ""
    outcome: str = ""
    score_delta: Dict[str, float] = field(default_factory=dict)


@dataclass
class TickResult:
    """
    Result of a single simulation tick.
    
    Contains all changes and events that occurred during the tick.
    
    Attributes:
        tick: Tick number
        agent_actions: List of agent action results
        state_changes: Summary of state changes
        events_generated: List of generated event IDs
        ambiguity_count: Number of ambiguous decisions resolved
        ai_calls: Number of AI model calls made
        duration_ms: Tick processing duration in milliseconds
        state_hash: Hash of the resulting state (for determinism verification)
    """
    
    tick: TickNumber
    agent_actions: List[AgentActionResult] = field(default_factory=list)
    state_changes: Dict[str, float] = field(default_factory=dict)
    events_generated: List[EventId] = field(default_factory=list)
    ambiguity_count: int = 0
    ai_calls: int = 0
    duration_ms: float = 0.0
    state_hash: str = ""
