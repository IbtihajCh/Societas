from dataclasses import dataclass, field
from typing import List

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState


@dataclass
class SimulationSaveData:
    agents: List[AgentState]
    world: SimulationState
    tick: int
    rng_state: dict
    timestamp: str
    version: str = "1.2"


@dataclass
class SimulationSaveMetadata:
    save_id: str
    tick: int
    population: int
    timestamp: str
    tick_rate: float
