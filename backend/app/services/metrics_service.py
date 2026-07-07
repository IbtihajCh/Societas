from dataclasses import asdict
from typing import Any, Dict, Optional

from shared.dto.metrics_dto import MetricPointDTO, MetricsResponseDTO
from shared.interfaces.i_simulation_engine import ISimulationEngine

from backend.app.repositories.simulation_repository import SimulationRepository


class MetricsService:
    def __init__(
        self,
        engine: Optional[ISimulationEngine] = None,
        repository: Optional[SimulationRepository] = None,
    ):
        self._engine = engine
        self._repository = repository or SimulationRepository()

    async def get_metrics(self, tick_from: int = 0, tick_to: int = 0) -> MetricsResponseDTO:
        if self._engine is None:
            return MetricsResponseDTO()
        engine_metrics = self._engine.get_metrics()
        current_tick = self._engine.get_current_tick()
        actual_tick_to = tick_to if tick_to > 0 else current_tick
        snapshots = await self._repository.get_snapshots(tick_from, actual_tick_to)
        population_data = []
        economy_data = []
        for snap in snapshots:
            s = snap["state"]
            tick = int(snap["tick"])
            population_data.append(MetricPointDTO(tick=tick, value=float(s.get("population", 0))))
            economy = s.get("economy", {})
            economy_data.append(MetricPointDTO(tick=tick, value=float(economy.get("health", 0.5))))
        return MetricsResponseDTO(
            current_tick=current_tick,
            population=population_data,
            economy=economy_data,
            crime=[],
            happiness=[],
            summary={},
        )

    async def get_dashboard_data(self) -> Dict[str, Any]:
        if self._engine is None:
            return {"status": "idle"}
        state = self._engine.get_state()
        metrics = self._engine.get_metrics()
        recent = await self._repository.get_tick_history(limit=20)
        return {
            "status": "running" if self._engine.is_running() else "paused",
            "current_tick": self._engine.get_current_tick(),
            "population": state.population,
            "state": asdict(state),
            "metrics": asdict(metrics),
            "recent_events": recent,
        }
