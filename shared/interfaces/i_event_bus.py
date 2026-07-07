"""
Event Bus Interface
===================

Abstract interface for the event bus system.
"""

from abc import ABC, abstractmethod
from typing import Callable, List

from shared.events.simulation_events import SimulationEvent


class IEventBus(ABC):
    """
    Abstract interface for the event bus.
    
    Defines the contract for event publishing and subscription.
    """
    
    @abstractmethod
    def publish(self, event: SimulationEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        ...
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[SimulationEvent], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        ...
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[SimulationEvent], None]) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        ...
    
    @abstractmethod
    def get_event_history(self, event_type: str = "") -> List[SimulationEvent]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Optional event type filter
            
        Returns:
            List of historical events
        """
        ...
    
    @abstractmethod
    def clear_history(self) -> None:
        """Clear the event history."""
        ...
