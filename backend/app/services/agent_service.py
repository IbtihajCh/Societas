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
            emotion=agent.emotions.primary.value if agent.emotions.primary else "normal",
            unlust=agent.unlust,
            job_type=agent.job_type.value if agent.job_type else "unemployed",
            grid_x=int(agent.grid_x),
            grid_y=int(agent.grid_y),
        )

    def _agent_to_detail(self, agent: AgentState) -> AgentDetailDTO:
        recent_actions = []
        if hasattr(agent, 'memories') and agent.memories:
            for m in list(agent.memories)[-10:]:
                if isinstance(m, dict):
                    recent_actions.append({
                        "tick": m.get("tick", 0),
                        "action": str(m.get("action", "")),
                        "description": str(m.get("description", "")),
                    })
                else:
                    recent_actions.append({
                        "tick": m.tick if hasattr(m, 'tick') else 0,
                        "action": m.action if hasattr(m, 'action') else "",
                        "description": m.description if hasattr(m, 'description') else "",
                    })
        return AgentDetailDTO(
            recent_actions=recent_actions,
            id=agent.id,
            persona=agent.persona,
            traits=asdict(agent.traits),
            needs={str(k): float(v) for k, v in agent.needs.levels.items()},
            emotions={str(k): float(v) for k, v in agent.emotions.intensities.items()},
            resources=asdict(agent.resources),
            employment_status=agent.employment_status,
            wealth_class=agent.wealth_class,
            age=agent.age,
            is_alive=agent.is_alive,
            location=agent.location,
            last_action=agent.last_action.value if agent.last_action else None,
            last_reasoning=agent.last_reasoning or "",
            social_connections=len(agent.social_connections),
            gender=agent.gender.value if agent.gender else "male",
            culture=agent.culture.value if agent.culture else "A",
            born_tick=int(agent.born_tick),
            unlust=agent.unlust,
            happiness_score=agent.emotions.happiness_score,
            emotion=agent.emotions.primary.value if agent.emotions.primary else "normal",
            emotion_timer=agent.emotions.emotion_timer,
            good_acts=agent.good_acts,
            crimes_committed=agent.crimes_committed,
            notoriety=agent.notoriety,
            trust_in_govt=agent.trust_in_govt,
            protest_count=agent.protest_count,
            money=agent.resources.money,
            base_salary=agent.resources.base_salary,
            employed=agent.resources.employed,
            education=agent.resources.education,
            property=agent.resources.property,
            health=agent.resources.health,
            job_type=agent.job_type.value if agent.job_type else "unemployed",
            grid_x=int(agent.grid_x),
            grid_y=int(agent.grid_y),
            spouse=agent.spouse,
            enemies=list(agent.enemies) if agent.enemies else [],
            community_id=agent.community_id,
        )
