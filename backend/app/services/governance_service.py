from typing import Any, Dict, List, Optional

from shared.interfaces.i_simulation_engine import ISimulationEngine
from simulation.policies.policy_suggester import analyze_world, generate_suggestions, prioritize_suggestions


class GovernanceService:
    def __init__(self, engine: Optional[ISimulationEngine] = None):
        self._engine = engine

    def get_suggestions(self) -> List[Dict[str, Any]]:
        if self._engine is None:
            return []
        world = self._engine.get_state()
        agents = self._engine.get_agents()
        analysis = analyze_world(world, agents, [])
        suggestions = generate_suggestions(analysis, world, None)
        return prioritize_suggestions(suggestions, world)
