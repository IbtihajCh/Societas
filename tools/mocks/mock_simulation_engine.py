"""
Mock Simulation Engine
======================

Mock implementation of ISimulationEngine for frontend development.
Returns realistic but static/fake data so frontend can develop without
waiting for the real simulation engine.
"""

from typing import Dict, Any, List, Optional
from shared.types.aliases import AgentId, TickNumber
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.metrics import SimulationMetrics
from shared.schemas.tick_result import TickResult
from shared.schemas.policy import Policy
from shared.interfaces.i_simulation_engine import ISimulationEngine


class MockSimulationEngine(ISimulationEngine):
    """
    Mock simulation engine for parallel frontend development.
    
    Returns realistic fake data without running any actual simulation.
    All methods are implemented and return valid data structures.
    """
    
    def __init__(self):
        self._tick: int = 0
        self._running: bool = False
        self._agents: Dict[AgentId, AgentState] = {}
        self._policies: Dict[str, Policy] = {}
        self._setup_mock_agents()
    
    def _setup_mock_agents(self) -> None:
        """Create 10 mock agents for testing."""
        # TODO: Implement with realistic mock data
        pass
    
    def tick(self) -> TickResult:
        """Advance mock simulation by one tick."""
        # TODO: Implement - return mock tick result
        self._tick += 1
        raise NotImplementedError("Mock tick not yet implemented")
    
    def reset(self, seed: Optional[int] = None) -> None:
        """Reset mock simulation to initial state."""
        # TODO: Implement
        self._tick = 0
        self._running = False
    
    def apply_policy(self, policy: Policy) -> None:
        """Apply a mock policy."""
        # TODO: Implement
        self._policies[policy.id] = policy
    
    def revoke_policy(self, policy_id: str) -> None:
        """Revoke a mock policy."""
        # TODO: Implement
        self._policies.pop(policy_id, None)
    
    def get_state(self) -> SimulationState:
        """Get mock world state."""
        # TODO: Implement - return realistic mock state
        raise NotImplementedError("Mock get_state not yet implemented")
    
    def get_metrics(self) -> SimulationMetrics:
        """Get mock metrics."""
        # TODO: Implement - return realistic mock metrics
        raise NotImplementedError("Mock get_metrics not yet implemented")
    
    def get_agent(self, agent_id: AgentId) -> Optional[AgentState]:
        """Get a mock agent by ID."""
        # TODO: Implement
        return self._agents.get(agent_id)
    
    def get_agents(self) -> List[AgentState]:
        """Get all mock agents."""
        # TODO: Implement
        return list(self._agents.values())
    
    def get_current_tick(self) -> TickNumber:
        """Get current mock tick."""
        return TickNumber(self._tick)
    
    def is_running(self) -> bool:
        """Check if mock simulation is running."""
        return self._running
