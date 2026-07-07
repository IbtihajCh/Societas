"""
Simulation Events
=================

Event definitions for the simulation event bus system.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from shared.types.aliases import AgentId, EventId, TickNumber


@dataclass
class SimulationEvent:
    """
    Base class for all simulation events.
    
    Attributes:
        id: Unique event identifier
        tick: Tick when the event occurred
        event_type: Type of event
        data: Event-specific data
    """
    
    id: EventId
    tick: TickNumber
    event_type: str = ""
    data: Dict[str, object] = field(default_factory=dict)


@dataclass
class TickStartedEvent(SimulationEvent):
    """Event fired when a simulation tick begins."""
    
    event_type: str = "tick_started"


@dataclass
class TickCompletedEvent(SimulationEvent):
    """
    Event fired when a simulation tick completes.
    
    Attributes:
        duration_ms: Duration of the tick in milliseconds
        agent_count: Number of agents processed
        ambiguity_count: Number of ambiguous decisions
    """
    
    event_type: str = "tick_completed"
    duration_ms: float = 0.0
    agent_count: int = 0
    ambiguity_count: int = 0


@dataclass
class AgentActedEvent(SimulationEvent):
    """
    Event fired when an agent takes an action.
    
    Attributes:
        agent_id: ID of the acting agent
        action: Action taken
        outcome: Outcome description
    """
    
    event_type: str = "agent_acted"
    agent_id: AgentId = field(default_factory=lambda: AgentId(""))
    action: str = ""
    outcome: str = ""


@dataclass
class AgentCreatedEvent(SimulationEvent):
    """
    Event fired when a new agent is created.
    
    Attributes:
        agent_id: ID of the new agent
        persona: Agent persona
    """
    
    event_type: str = "agent_created"
    agent_id: AgentId = field(default_factory=lambda: AgentId(""))
    persona: str = ""


@dataclass
class AgentDeceasedEvent(SimulationEvent):
    """
    Event fired when an agent dies.
    
    Attributes:
        agent_id: ID of the deceased agent
        cause: Cause of death
    """
    
    event_type: str = "agent_deceased"
    agent_id: AgentId = field(default_factory=lambda: AgentId(""))
    cause: str = ""


@dataclass
class PolicyEnactedEvent(SimulationEvent):
    """
    Event fired when a policy is enacted.
    
    Attributes:
        policy_id: ID of the enacted policy
        policy_name: Name of the policy
    """
    
    event_type: str = "policy_enacted"
    policy_id: str = ""
    policy_name: str = ""


@dataclass
class AmbiguityDetectedEvent(SimulationEvent):
    """
    Event fired when decision ambiguity is detected.
    
    Attributes:
        agent_id: ID of the agent with ambiguous decision
        top_score: Score of top action
        second_score: Score of second-best action
    """
    
    event_type: str = "ambiguity_detected"
    agent_id: AgentId = field(default_factory=lambda: AgentId(""))
    top_score: float = 0.0
    second_score: float = 0.0
