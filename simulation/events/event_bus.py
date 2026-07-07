"""
Event Bus
=========

Internal event publishing and subscription system.
"""

from typing import Callable, Dict, List

from shared.events.simulation_events import SimulationEvent
from shared.interfaces.i_event_bus import IEventBus


class EventBus(IEventBus):
    """
    Event bus for publishing and subscribing to simulation events.
    
    Maintains event history and manages subscriber callbacks.
    
    Attributes:
        _subscribers: Dictionary mapping event types to handler lists
        _history: List of all published events
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable[[SimulationEvent], None]]] = {}
        self._history: List[SimulationEvent] = []
    
    def publish(self, event: SimulationEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        self._history.append(event)
        
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            handler(event)
    
    def subscribe(self, event_type: str, handler: Callable[[SimulationEvent], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable[[SimulationEvent], None]) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
    
    def get_event_history(self, event_type: str = "") -> List[SimulationEvent]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Optional event type filter
            
        Returns:
            List of historical events
        """
        if event_type:
            return [e for e in self._history if e.event_type == event_type]
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()
