from dataclasses import asdict
from typing import Optional

from shared.dto.agent_dto import (
    AgentDetailDTO,
    AgentListResponseDTO,
    AgentSummaryDTO,
)
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.schemas.agent_state import AgentState


class AgentService:
    def __init__(self, engine: Optional[ISimulationEngine] = None):
        self._engine = engine

    async def list_agents(self, limit: int = 50, offset: int = 0) -> AgentListResponseDTO:
        if self._engine is None:
            return AgentListResponseDTO()
        agents = self._engine.get_agents()
        total = len(agents)
        page = (offset // limit) + 1 if limit > 0 else 1
        paginated = agents[offset : offset + limit]
        return AgentListResponseDTO(
            agents=[self._agent_to_summary(a) for a in paginated],
            total=total,
            page=page,
            page_size=limit,
        )

    async def get_agent(self, agent_id: str) -> Optional[AgentDetailDTO]:
        if self._engine is None:
            return None
        agent = self._engine.get_agent(agent_id)
        if agent is None:
            return None
        return self._agent_to_detail(agent)

    def _agent_to_summary(self, agent: AgentState) -> AgentSummaryDTO:
        return AgentSummaryDTO(
            id=agent.id,
            persona=agent.persona,
            wealth_class=agent.wealth_class,
            employment_status=agent.employment_status,
            age=agent.age,
            is_alive=agent.is_alive,
        )

    def _agent_to_detail(self, agent: AgentState) -> AgentDetailDTO:
        return AgentDetailDTO(
            id=agent.id,
            persona=agent.persona,
            traits=asdict(agent.traits),
            needs={str(k): float(v) for k, v in agent.needs.levels.items()},
            emotions={str(k): float(v) for k, v in agent.emotions.intensities.items()},
            resources=asdict(agent.resources),
            employment_status=agent.employment_status,
            wealth_class=agent.wealth_class,
            age=agent.age,
            location=agent.location,
            last_action=agent.decision_scores.top_action if agent.decision_scores else None,
            social_connections=len(agent.social_connections),
        )
