import asyncio
from dataclasses import asdict
from typing import Optional

from shared.dto.simulation_dto import (
    SimulationStartRequestDTO,
    SimulationStateResponseDTO,
    SimulationStatusDTO,
)
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.schemas.simulation_state import SimulationState

from backend.app.repositories.simulation_repository import SimulationRepository
from simulation.engine.config import SimulationConfig
from simulation.engine.simulation_engine import SimulationEngine


class SimulationService:
    def __init__(
        self,
        engine: Optional[ISimulationEngine] = None,
        repository: Optional[SimulationRepository] = None,
    ):
        self._engine = engine
        self._repository = repository or SimulationRepository()

    async def get_status(self) -> SimulationStatusDTO:
        if self._engine is None:
            return SimulationStatusDTO()
        agents = self._engine.get_agents()
        return SimulationStatusDTO(
            tick=self._engine.get_current_tick(),
            is_running=self._engine.is_running(),
            speed=1.0,
            population=len(agents),
        )

    async def start_simulation(self, request: SimulationStartRequestDTO) -> SimulationStatusDTO:
        config = SimulationConfig(
            population_size=request.population_size,
            seed=request.seed,
        )
        self._engine = SimulationEngine(config=config)
        return await self.get_status()

    async def stop_simulation(self) -> SimulationStatusDTO:
        if self._engine is not None:
            if hasattr(self._engine, "_is_running"):
                self._engine._is_running = False
        return await self.get_status()

    async def advance_tick(self) -> SimulationStateResponseDTO:
        if self._engine is None:
            raise RuntimeError("Simulation not started")
        result = await asyncio.to_thread(self._engine.tick)
        state = self._engine.get_state()
        await self._repository.save_snapshot(result.tick, state)
        for action_result in result.agent_results:
            if action_result is not None:
                await self._repository.save_tick_record(
                    tick=result.tick,
                    event_type="agent_acted",
                    data={"agent_id": str(action_result.agent_id), "action": str(action_result.action)},
                )
        return self._state_to_dto(state)

    async def get_state(self) -> SimulationStateResponseDTO:
        if self._engine is None:
            return SimulationStateResponseDTO()
        state = self._engine.get_state()
        return self._state_to_dto(state)

    async def reset_simulation(self, seed: Optional[int] = None) -> SimulationStatusDTO:
        if self._engine is not None:
            self._engine.reset(seed)
        return await self.get_status()

    def get_engine(self) -> Optional[ISimulationEngine]:
        return self._engine

    def _state_to_dto(self, state: SimulationState) -> SimulationStateResponseDTO:
        return SimulationStateResponseDTO(
            tick=state.tick,
            population=state.population,
            economic_health=state.economy.health if state.economy else 0.5,
            social_cohesion=state.psychology.social_cohesion if state.psychology else 0.5,
            environmental_quality=0.5,
            public_order=state.crime.public_order if state.crime else 0.5,
            innovation_index=state.economy.innovation_index if state.economy else 0.5,
            unlust=state.psychology.unlust if state.psychology else 0.0,
            morality=state.psychology.morality if state.psychology else 0.5,
        )
