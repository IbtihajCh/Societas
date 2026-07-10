import asyncio
import os
from dataclasses import asdict
from typing import Optional

from shared.dto.simulation_dto import (
    SimulationStartRequestDTO,
    SimulationStateResponseDTO,
    SimulationStatusDTO,
)
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.schemas.simulation_state import SimulationState

from backend.app.services.ai_historian import AIHistorianService
from backend.app.websocket.manager import ws_manager
from backend.app.repositories.simulation_repository import SimulationRepository
from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter
from simulation.engine.config import SimulationConfig
from simulation.engine.simulation_engine import SimulationEngine

_service_instance: "SimulationService | None" = None


class SimulationService:
    def __init__(
        self,
        engine: Optional[ISimulationEngine] = None,
        repository: Optional[SimulationRepository] = None,
    ):
        global _service_instance
        _service_instance = self
        self._engine = engine
        self._historian: AIHistorianService | None = None
        self._repository = repository or SimulationRepository()

    @property
    def historian(self) -> AIHistorianService | None:
        return self._historian

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
        vllm_config = VLLMConfig(
            base_url=os.getenv("VLLM_BASE_URL", ""),
            base_url_e2b=os.getenv("VLLM_BASE_URL_E2B", ""),
            base_url_moe_26b=os.getenv("VLLM_BASE_URL_MOE_26B", ""),
            base_url_dense_31b=os.getenv("VLLM_BASE_URL_DENSE_31B", ""),
            api_key_e2b=os.getenv("API_KEY_E2B", ""),
            api_key_moe_26b=os.getenv("API_KEY_MOE_26B", ""),
            api_key_dense_31b=os.getenv("API_KEY_DENSE_31B", ""),
        )
        router = VLLMRouter(vllm_config)
        self._historian = AIHistorianService(router)
        self._engine = SimulationEngine(config=config)
        self._engine.start(ai_router=router)
        return await self.get_status()

    async def stop_simulation(self) -> SimulationStatusDTO:
        if self._engine is not None:
            self._engine.stop()
        if self._historian is not None and self._historian.has_snapshots():
            entry = self._historian.generate_summary(self._engine.get_current_tick() if self._engine else 0)
            if entry is not None:
                await ws_manager.broadcast({
                    "type": "chronicle",
                    "final": True,
                    "entry": entry,
                })
        return await self.get_status()

    async def advance_tick(self) -> SimulationStateResponseDTO:
        if self._engine is None or not self._engine.is_running():
            raise RuntimeError("Simulation not started")
        result = await asyncio.to_thread(self._engine.tick)
        state = self._engine.get_state()
        await self._repository.save_snapshot(result.tick, state)

        await ws_manager.broadcast({
            "type": "tick_completed",
            "tick": result.tick,
            "duration_ms": result.duration_ms,
            "population": state.population,
            "state_hash": result.state_hash,
            "ambiguity_count": result.ambiguity_count,
            "ai_calls": result.ai_calls,
        })

        for action_result in result.agent_actions:
            if action_result is not None:
                await self._repository.save_tick_record(
                    tick=result.tick,
                    event_type="agent_acted",
                    data={"agent_id": str(action_result.agent_id), "action": str(action_result.action)},
                )
                await ws_manager.broadcast({
                    "type": "agent_acted",
                    "agent_id": str(action_result.agent_id),
                    "action": str(action_result.action),
                })

        if self._historian is not None:
            self._historian.accumulate(state, result.tick)

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
            tick=state.time_step,
            population=state.population,
            economic_health=state.economic_health,
            social_cohesion=state.social_cohesion,
            environmental_quality=state.environmental_quality,
            public_order=state.public_order,
            innovation_index=state.innovation_index,
            unlust=state.unlust,
            morality=state.morality,
            food_availability=state.food_availability,
            water_availability=state.water_availability,
            crime_rate=state.crime_rate,
            protest_intensity=state.protest_intensity,
            unemployment_rate=state.unemployment_rate,
            tax_rate=state.tax_rate,
            welfare_enabled=state.welfare_enabled,
            welfare_amount=state.welfare_amount,
        )
