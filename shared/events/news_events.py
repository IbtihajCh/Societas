"""
News Events
===========

Event definitions for news and narration events.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from shared.types.aliases import EventId, TickNumber


@dataclass
class NewsEvent:
    """
    Base class for news events.
    
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
class NewsGeneratedEvent(NewsEvent):
    """
    Event fired when a news article is generated.
    
    Attributes:
        headline: News headline
        category: News category
        importance: Importance level
    """
    
    event_type: str = "news_generated"
    headline: str = ""
    category: str = "general"
    importance: float = 0.5


@dataclass
class SpotlightGeneratedEvent(NewsEvent):
    """
    Event fired when a spotlight narration is generated.
    
    Attributes:
        agent_id: ID of the spotlighted agent
        title: Narration title
        mood: Narration mood
    """
    
    event_type: str = "spotlight_generated"
    agent_id: str = ""
    title: str = ""
    mood: str = "neutral"
