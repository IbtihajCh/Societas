"""
Agents Router
=============

Agent query and management endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from shared.dto.agent_dto import AgentSummaryDTO, AgentDetailDTO, AgentListResponseDTO

router = APIRouter()


@router.get("/", response_model=AgentListResponseDTO)
async def list_agents(limit: int = 100, offset: int = 0):
    """
    List agents.
    
    Args:
        limit: Maximum number of agents to return
        offset: Offset for pagination
        
    Returns:
        AgentListResponseDTO
        
    TODO: Implement agent listing
    """
    # TODO: Get agents from simulation engine
    return AgentListResponseDTO()


@router.get("/{agent_id}", response_model=AgentDetailDTO)
async def get_agent(agent_id: str):
    """
    Get a specific agent.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        AgentDetailDTO
        
    TODO: Implement agent retrieval
    """
    # TODO: Get agent from simulation engine
    return AgentDetailDTO()


@router.get("/{agent_id}/history")
async def get_agent_history(agent_id: str):
    """
    Get agent action history.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Agent history
        
    TODO: Implement agent history retrieval
    """
    # TODO: Get agent history
    return {"agent_id": agent_id, "history": []}
