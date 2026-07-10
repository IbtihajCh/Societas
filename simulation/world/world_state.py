"""
World State Manager
===================

Manages the global world state for the simulation.
"""

from shared.schemas.simulation_state import SimulationState
from shared.schemas.economy_state import EconomyState
from shared.schemas.crime_state import CrimeState
from shared.schemas.needs_state import NeedsState
from shared.schemas.psychology_state import PsychologyState


class WorldStateManager:
    """
    Manages the global world state for the simulation.
    
    Coordinates updates to economy, crime, needs, and psychology states.
    
    Attributes:
        _state: Current world state
    """
    
    def __init__(self):
        """Initialize world state with default values."""
        self._state = SimulationState(
            economy=EconomyState(),
            crime=CrimeState(),
            needs=NeedsState(),
            psychology=PsychologyState(),
        )
    
    def get_state(self) -> SimulationState:
        """
        Get the current world state.
        
        Returns:
            Current SimulationState
        """
        return self._state
    
    def update_state(self, **kwargs) -> None:
        """
        Update world state variables.
        
        Args:
            **kwargs: State variables to update
            
        TODO: Implement state update logic
            - Validate updates
            - Apply changes to state
            - Trigger dependent updates
        """
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
    
    def get_active_env_events(self) -> list[dict]:
        """Get the list of currently active environmental events.

        Returns:
            List of event dicts with type, severity, duration, etc.
        """
        return self._state.active_env_events

    def set_active_env_events(self, events: list[dict]) -> None:
        """Replace the active environmental events list.

        Args:
            events: New list of event dicts.
        """
        self._state.active_env_events = events

    def reset(self) -> None:
        """Reset world state to initial values."""
        self._state = SimulationState(
            economy=EconomyState(),
            crime=CrimeState(),
            needs=NeedsState(),
            psychology=PsychologyState(),
        )
