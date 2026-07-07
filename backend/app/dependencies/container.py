from typing import Optional

from shared.interfaces.i_simulation_engine import ISimulationEngine

from backend.app.repositories.policy_repository import PolicyRepository
from backend.app.repositories.simulation_repository import SimulationRepository
from backend.app.services.agent_service import AgentService
from backend.app.services.metrics_service import MetricsService
from backend.app.services.policy_service import PolicyService
from backend.app.services.simulation_service import SimulationService

_engine: Optional[ISimulationEngine] = None


def get_engine() -> Optional[ISimulationEngine]:
    return _engine


def set_engine(engine: ISimulationEngine) -> None:
    global _engine
    _engine = engine


async def get_simulation_service() -> SimulationService:
    return SimulationService(engine=_engine, repository=SimulationRepository())


async def get_policy_service() -> PolicyService:
    return PolicyService(engine=_engine, repository=PolicyRepository())


async def get_agent_service() -> AgentService:
    return AgentService(engine=_engine)


async def get_metrics_service() -> MetricsService:
    return MetricsService(engine=_engine, repository=SimulationRepository())
