"""
Agent DTO
=========

Data Transfer Objects for agent-related API communication.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared.types.aliases import AgentId
from shared.types.enums import EmploymentStatus, WealthClass


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
        emotion: Primary emotion as string for display
        unlust: Current dissatisfaction level
        job_type: Current job type
    """
    
    id: AgentId
    persona: str = ""
    wealth_class: WealthClass = WealthClass.MIDDLE
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    age: int = 0
    is_alive: bool = True
    emotion: str = "normal"
    unlust: float = 0.0
    job_type: str = "unemployed"
    grid_x: int = 0
    grid_y: int = 0


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
        last_action: Last action taken (ActionType as string)
        last_reasoning: LLM reasoning from last decision
        social_connections: Number of social connections
        gender: Agent gender
        culture: Agent cultural background
        born_tick: Tick when the agent was born
        unlust: Current dissatisfaction level
        happiness_score: Composite happiness score
        emotion: Primary emotion as string
        emotion_timer: Remaining ticks in current emotional state
        good_acts: Count of prosocial actions performed
        crimes_committed: Count of crimes committed
        notoriety: Criminal notoriety score
        trust_in_govt: Trust in government
        protest_count: Number of protests participated in
        money: Current liquid money
        base_salary: Annual base salary
        employed: Whether the agent is currently employed
        education: Highest education level achieved (string)
        property: Whether the agent owns property
        health: Health level
        job_type: Current job type
        grid_x: X coordinate on the simulation grid
        grid_y: Y coordinate on the simulation grid
        spouse: Agent ID of spouse, if any
        enemies: List of enemy agent IDs
        community_id: Community identifier, if any
    """
    
    id: AgentId
    persona: str = ""
    traits: Dict[str, float] = field(default_factory=dict)
    needs: Dict[str, float] = field(default_factory=dict)
    emotions: Dict[str, float] = field(default_factory=dict)
    resources: Dict[str, float] = field(default_factory=dict)
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    wealth_class: WealthClass = WealthClass.MIDDLE
    age: int = 0
    is_alive: bool = True
    location: str = "default"
    last_action: Optional[str] = None
    last_reasoning: str = ""
    social_connections: int = 0
    # Identity
    gender: str = "male"
    culture: str = "A"
    born_tick: int = 0
    # Psychology
    unlust: float = 0.0
    happiness_score: float = 0.5
    emotion: str = "normal"
    emotion_timer: int = 0
    # Social/behavioral tracking
    good_acts: int = 0
    crimes_committed: int = 0
    notoriety: float = 0.0
    trust_in_govt: float = 0.5
    protest_count: int = 0
    # Economic details
    money: float = 100.0
    base_salary: float = 0.0
    employed: bool = False
    education: str = "primary"
    property: bool = False
    health: float = 1.0
    job_type: str = "unemployed"
    # Grid position
    grid_x: int = 0
    grid_y: int = 0
    # Social connections (detailed)
    spouse: Optional[str] = None
    enemies: List[str] = field(default_factory=list)
    community_id: Optional[str] = None
    # Recent actions timeline
    recent_actions: List[Dict[str, Any]] = field(default_factory=list)


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


@dataclass
class AgentRecentActionDTO:
    """
    Single recent action entry for an agent.

    Attributes:
        tick: Simulation tick when the action occurred.
        action: ActionType as string.
        description: Human-readable description of the action.
    """

    tick: int = 0
    action: str = ""
    description: str = ""
