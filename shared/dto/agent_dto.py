"""
Agent DTO
=========

Data Transfer Objects for agent-related API communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import AgentId
from shared.types.enums import ActionType, EmploymentStatus, WealthClass


@dataclass
class AgentSummaryDTO:
    """
    Summary representation of an agent for list views.
    
    Attributes:
        id: Agent identifier
        persona: Agent persona description
        wealth_class: Current wealth classification
        employment_status: Current employment status
        age: Agent age
        is_alive: Whether the agent is active
    """
    
    id: AgentId
    persona: str = ""
    wealth_class: WealthClass = WealthClass.WORKING
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    age: int = 0
    is_alive: bool = True
    emotion: str = "content"


@dataclass
class AgentDetailDTO:
    """
    Detailed representation of an agent for detail views.
    
    Attributes:
        id: Agent identifier
        persona: Agent persona description
        traits: Dictionary of trait values
        needs: Dictionary of current need levels
        emotions: Dictionary of emotion intensities
        resources: Dictionary of resource holdings
        employment_status: Current employment status
        wealth_class: Current wealth classification
        age: Agent age
        is_alive: Whether the agent is active
        location: Current location
        last_action: Last action taken
        social_connections: Number of social connections
    """
    
    id: AgentId
    persona: str = ""
    traits: Dict[str, float] = field(default_factory=dict)
    needs: Dict[str, float] = field(default_factory=dict)
    emotions: Dict[str, float] = field(default_factory=dict)
    resources: Dict[str, float] = field(default_factory=dict)
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    wealth_class: WealthClass = WealthClass.WORKING
    age: int = 0
    is_alive: bool = True
    location: str = "default"
    last_action: Optional[ActionType] = None
    social_connections: int = 0


@dataclass
class AgentListResponseDTO:
    """
    Response DTO for agent list queries.
    
    Attributes:
        agents: List of agent summaries
        total: Total number of agents
        page: Current page number
        page_size: Number of agents per page
    """
    
    agents: List[AgentSummaryDTO] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
