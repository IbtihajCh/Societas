"""
Policy Events
=============

Event definitions for policy-related events.
"""

from dataclasses import dataclass, field
from typing import Dict

from shared.types.aliases import EventId, TickNumber


@dataclass
class PolicyEvent:
    """
    Base class for policy events.
    
    Attributes:
        id: Unique event identifier
        tick: Tick when the event occurred
        event_type: Type of event
        policy_id: ID of the affected policy
        data: Event-specific data
    """
    
    id: EventId
    tick: TickNumber
    event_type: str = ""
    policy_id: str = ""
    data: Dict[str, object] = field(default_factory=dict)


@dataclass
class PolicyCreatedEvent(PolicyEvent):
    """Event fired when a new policy is created."""
    
    event_type: str = "policy_created"


@dataclass
class PolicyUpdatedEvent(PolicyEvent):
    """Event fired when a policy is updated."""
    
    event_type: str = "policy_updated"


@dataclass
class PolicyRevokedEvent(PolicyEvent):
    """Event fired when a policy is revoked."""
    
    event_type: str = "policy_revoked"
