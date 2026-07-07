from fastapi import APIRouter, Depends, HTTPException

from shared.dto.agent_dto import AgentDetailDTO, AgentListResponseDTO

from backend.app.dependencies import get_agent_service
from backend.app.services.agent_service import AgentService

router = APIRouter()


@router.get("/", response_model=AgentListResponseDTO)
async def list_agents(
    limit: int = 100,
    offset: int = 0,
    service: AgentService = Depends(get_agent_service),
):
    return await service.list_agents(limit=limit, offset=offset)


@router.get("/{agent_id}", response_model=AgentDetailDTO)
async def get_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
):
    agent = await service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/history")
async def get_agent_history(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
):
    return {"agent_id": agent_id, "history": []}
