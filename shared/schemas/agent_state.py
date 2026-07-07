"""
Agent State Schema
==================

Defines the complete state representation for an autonomous agent in SOCIETAS.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import AgentId, NeedValue
from shared.types.enums import (
    ActionType,
    EmotionType,
    EmploymentStatus,
    NeedType,
    WealthClass,
)


@dataclass
class AgentTraits:
    """
    Psychological traits of an agent.
    
    These traits are generated once at agent creation and remain stable
    throughout the agent's lifecycle. They influence decision-making
    and behavior patterns.
    
    Attributes:
        morality: Moral alignment (0.0 = amoral, 1.0 = highly moral)
        creativity: Creative tendency (0.0 = conventional, 1.0 = highly creative)
        ambition: Drive for achievement (0.0 = passive, 1.0 = highly ambitious)
        resilience: Ability to recover from setbacks (0.0 = fragile, 1.0 = resilient)
        dominance: Social dominance tendency (0.0 = submissive, 1.0 = dominant)
        anger_tendency: Propensity for anger (0.0 = calm, 1.0 = quick to anger)
        extraversion: Social energy orientation (0.0 = introverted, 1.0 = extraverted)
        risk_tolerance: Willingness to take risks (0.0 = cautious, 1.0 = risk-seeking)
    """
    
    morality: float = 0.5
    creativity: float = 0.5
    ambition: float = 0.5
    resilience: float = 0.5
    dominance: float = 0.5
    anger_tendency: float = 0.5
    extraversion: float = 0.5
    risk_tolerance: float = 0.5


@dataclass
class AgentNeeds:
    """
    Current need levels for an agent.
    
    Needs drive agent behavior. Higher values indicate greater urgency.
    Needs are fulfilled through agent actions and decay over time.
    
    Attributes:
        levels: Mapping of need types to current levels (0.0 = satisfied, 1.0 = critical)
    """
    
    levels: Dict[NeedType, NeedValue] = field(default_factory=dict)
    
    def get_level(self, need_type: NeedType) -> NeedValue:
        """Get the current level for a specific need."""
        return self.levels.get(need_type, NeedValue(0.0))
    
    def set_level(self, need_type: NeedType, value: NeedValue) -> None:
        """Set the level for a specific need."""
        self.levels[need_type] = value
    
    def get_most_urgent_need(self) -> Optional[NeedType]:
        """Get the most urgent (highest level) need."""
        if not self.levels:
            return None
        return max(self.levels, key=lambda k: self.levels[k])


@dataclass
class AgentEmotions:
    """
    Current emotional state of an agent.
    
    Emotions influence decision-making and can be triggered by events,
    need fulfillment/deficit, and social interactions.
    
    Attributes:
        primary: Current dominant emotion
        intensities: Mapping of emotion types to intensities (0.0 to 1.0)
    """
    
    primary: EmotionType = EmotionType.CONTENT
    intensities: Dict[EmotionType, float] = field(default_factory=dict)


@dataclass
class AgentResources:
    """
    Resource holdings of an agent.
    
    Tracks material and financial resources available to the agent.
    
    Attributes:
        wealth: Current financial wealth (monetary units)
        assets: List of owned assets
        skills: List of acquired skills
    """
    
    wealth: float = 0.0
    assets: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)


@dataclass
class AgentDecisionScores:
    """
    Decision utility scores for an agent.
    
    Calculated each tick based on needs, traits, emotions, and environment.
    Used to determine the agent's next action.
    
    Attributes:
        scores: Mapping of action types to utility scores (-1.0 to 1.0)
        top_action: Currently highest-scored action
        top_score: Score of the top action
        second_score: Score of the second-best action
    """
    
    scores: Dict[ActionType, float] = field(default_factory=dict)
    top_action: Optional[ActionType] = None
    top_score: float = 0.0
    second_score: float = 0.0
    
    def is_ambiguous(self, threshold: float = 0.05) -> bool:
        """
        Check if the decision is ambiguous (requires AI tie-breaking).
        
        Args:
            threshold: Minimum score difference to be considered clear
            
        Returns:
            True if the decision is ambiguous
        """
        return (self.top_score - self.second_score) < threshold


@dataclass
class AgentState:
    """
    Complete state representation of an autonomous agent.
    
    This is the primary data structure for agent state in SOCIETAS.
    It contains all information needed to simulate agent behavior,
    make decisions, and track agent lifecycle.
    
    Attributes:
        id: Unique agent identifier
        persona: Natural language persona (generated once at birth)
        traits: Psychological traits
        needs: Current need levels
        emotions: Current emotional state
        resources: Resource holdings
        decision_scores: Current decision utility scores
        employment_status: Current employment status
        wealth_class: Current wealth classification
        age: Agent age in ticks
        is_alive: Whether the agent is still active
        location: Current location identifier
        social_connections: List of connected agent IDs
        metadata: Additional metadata dictionary
    """
    
    id: AgentId
    persona: str = ""
    traits: AgentTraits = field(default_factory=AgentTraits)
    needs: AgentNeeds = field(default_factory=AgentNeeds)
    emotions: AgentEmotions = field(default_factory=AgentEmotions)
    resources: AgentResources = field(default_factory=AgentResources)
    decision_scores: AgentDecisionScores = field(default_factory=AgentDecisionScores)
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    wealth_class: WealthClass = WealthClass.WORKING
    age: int = 0
    is_alive: bool = True
    location: str = "default"
    social_connections: List[AgentId] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)
