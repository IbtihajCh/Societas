"""
News Event Schema
=================

Defines the news event schema for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import EventId, TickNumber


@dataclass
class NewsEvent:
    """
    A news event or article generated from simulation events.
    
    Represents a news dispatch generated from simulation events,
    providing narrative context for the dashboard.
    
    Attributes:
        id: Unique event identifier
        tick: Tick when the event occurred
        headline: News headline
        dateline: Date/location line
        body: Full article body text
        bylines: List of mentioned agents/entities
        category: News category
        importance: Importance level (0.0 to 1.0)
        related_events: List of related event IDs
        metadata: Additional event metadata
    """
    
    id: EventId
    tick: TickNumber = TickNumber(0)
    headline: str = ""
    dateline: str = ""
    body: str = ""
    bylines: List[str] = field(default_factory=list)
    category: str = "general"
    importance: float = 0.5
    related_events: List[EventId] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class SpotlightNarration:
    """
    A spotlight narration about a specific agent.
    
    Provides detailed narrative about an individual agent's
    experiences and decisions.
    
    Attributes:
        agent_id: ID of the spotlighted agent
        tick: Tick of the narration
        title: Narration title
        content: Full narration text
        mood: Overall mood of the narration
        key_events: List of key events mentioned
    """
    
    agent_id: str
    tick: TickNumber = TickNumber(0)
    title: str = ""
    content: str = ""
    mood: str = "neutral"
    key_events: List[str] = field(default_factory=list)
