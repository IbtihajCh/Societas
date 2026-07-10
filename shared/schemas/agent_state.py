"""
Agent State Schema
==================

Defines the complete state representation for an autonomous agent in SOCIETAS.
Aligned with Project Guide v1.0 and ADR-005.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared.types.aliases import AgentId, GridCoordinate, NeedValue, TickNumber
from shared.types.enums import (
    ActionType,
    Culture,
    EducationLevel,
    EmotionType,
    EmploymentStatus,
    Gender,
    JobType,
    NeedType,
    WealthClass,
)


@dataclass
class AgentTraits:
    """Psychological traits of an agent (generated once at birth via Beta distributions).

    Attributes:
        morality: Moral alignment (0.0 = amoral, 1.0 = highly moral).
        creativity: Creative tendency (0.0 = conventional, 1.0 = highly creative).
        ambition: Drive for achievement (0.0 = passive, 1.0 = highly ambitious).
        resilience: Ability to recover from setbacks (0.0 = fragile, 1.0 = resilient).
        dominance_urge: Social dominance tendency (0.0 = submissive, 1.0 = dominant).
        anger_tendency: Propensity for anger (0.0 = calm, 1.0 = quick to anger).
        extraversion: Social energy orientation (0.0 = introverted, 1.0 = extraverted).
        risk_tolerance: Willingness to take risks (0.0 = cautious, 1.0 = risk-seeking).
    """

    morality: float = 0.5
    creativity: float = 0.5
    ambition: float = 0.5
    resilience: float = 0.5
    dominance_urge: float = 0.5
    anger_tendency: float = 0.5
    extraversion: float = 0.5
    risk_tolerance: float = 0.5


@dataclass
class AgentNeeds:
    """Current need levels for an agent (13 needs across 5 Maslow layers).

    Needs are stored as a dict mapping NeedType to NeedValue (0.0 to 1.0).
    Lower values indicate greater urgency (closer to critical).

    Attributes:
        levels: Mapping of need types to current levels (0.0 = critical, 1.0 = satisfied).
    """

    levels: Dict[NeedType, NeedValue] = field(default_factory=dict)

    def get_level(self, need_type: NeedType) -> NeedValue:
        """Get the current level for a specific need.

        Args:
            need_type: The need to query.

        Returns:
            Current need level (0.0 to 1.0), defaults to 0.5 if not set.
        """
        return self.levels.get(need_type, NeedValue(0.5))

    def set_level(self, need_type: NeedType, value: float) -> None:
        """Set the level for a specific need, clamped to [0.0, 1.0].

        Args:
            need_type: The need to set.
            value: New need level (will be clamped to 0.0-1.0).
        """
        clamped = max(0.0, min(1.0, value))
        self.levels[need_type] = NeedValue(clamped)

    def get_most_urgent_need(self) -> Optional[NeedType]:
        """Get the most urgent (lowest level) need.

        Returns:
            The need type with the lowest level, or None if no needs are set.
        """
        if not self.levels:
            return None
        return min(self.levels, key=lambda k: self.levels[k])


@dataclass
class AgentEmotions:
    """Current emotional state of an agent (5 states with timers).

    Attributes:
        primary: Current dominant emotion.
        intensities: Mapping of emotion types to intensities (0.0 to 1.0).
        emotion_timer: Remaining ticks in current emotional state.
        happiness_score: Composite happiness score (0.0 to 1.0).
    """

    primary: EmotionType = EmotionType.NORMAL
    intensities: Dict[EmotionType, float] = field(default_factory=dict)
    emotion_timer: int = 0
    happiness_score: float = 0.5


@dataclass
class AgentResources:
    """Resource holdings of an agent.

    Attributes:
        money: Current liquid money in pounds.
        base_salary: Annual base salary in pounds (0 if unemployed).
        employed: Whether the agent is currently employed.
        education: Highest education level achieved.
        property: Whether the agent owns property.
        health: Health level (0.0 = dead, 1.0 = perfect health).
        wealth: Legacy wealth field (kept for backward compatibility).
        assets: List of owned assets.
        skills: List of acquired skills.
    """

    money: float = 100.0
    base_salary: float = 0.0
    employed: bool = False
    education: EducationLevel = EducationLevel.PRIMARY
    property: bool = False
    health: float = 1.0
    wealth: float = 100.0
    debt: float = 0.0
    assets: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)


@dataclass
class AgentDecisionScores:
    """Decision utility scores for an agent.

    Attributes:
        scores: Mapping of action types to utility scores.
        top_action: Currently highest-scored action.
        top_score: Score of the top action.
        second_score: Score of the second-best action.
    """

    scores: Dict[ActionType, float] = field(default_factory=dict)
    top_action: Optional[ActionType] = None
    top_score: float = 0.0
    second_score: float = 0.0

    def is_ambiguous(self, threshold: float = 0.05) -> bool:
        """Check if the decision is ambiguous (requires AI tie-breaking).

        Args:
            threshold: Minimum score difference to be considered clear.

        Returns:
            True if the decision is ambiguous.
        """
        return (self.top_score - self.second_score) < threshold


@dataclass
class AgentState:
    """Complete state representation of an autonomous agent.

    Attributes:
        id: Unique agent identifier.
        persona: Natural language persona (generated once at birth).
        traits: Psychological traits.
        needs: Current need levels.
        emotions: Current emotional state.
        resources: Resource holdings.
        decision_scores: Current decision utility scores.
        employment_status: Current employment status.
        wealth_class: Current wealth classification.
        age: Agent age in ticks.
        is_alive: Whether the agent is still active.
        location: Current location identifier.
        social_connections: List of connected agent IDs.
        metadata: Additional metadata dictionary.
        gender: Agent gender.
        culture: Agent cultural background.
        born_tick: Tick when the agent was born.
        unlust: Current Unlust (dissatisfaction) level (0.0 to 1.0).
        good_acts: Count of prosocial actions performed.
        crimes_committed: Count of crimes committed.
        notoriety: Criminal notoriety score (0.0+).
        trust_in_govt: Trust in government (0.0 to 1.0).
        protest_count: Number of protests participated in.
        grid_x: X coordinate on the simulation grid.
        grid_y: Y coordinate on the simulation grid.
        job_type: Current job type.
        spouse: Agent ID of spouse, if any.
        enemies: List of enemy agent IDs.
        community_id: Community identifier, if any.
        last_action: The last action this agent took.
        last_reasoning: LLM reasoning from the last decision.
    """

    id: AgentId
    persona: str = ""
    traits: AgentTraits = field(default_factory=AgentTraits)
    needs: AgentNeeds = field(default_factory=AgentNeeds)
    emotions: AgentEmotions = field(default_factory=AgentEmotions)
    resources: AgentResources = field(default_factory=AgentResources)
    decision_scores: AgentDecisionScores = field(default_factory=AgentDecisionScores)
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    wealth_class: WealthClass = WealthClass.POOR
    age: int = 25
    is_alive: bool = True
    location: str = "default"
    social_connections: List[AgentId] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Extended fields per Project Guide and ADR-005:
    gender: Gender = Gender.MALE
    culture: Culture = Culture.A
    born_tick: TickNumber = TickNumber(0)
    unlust: float = 0.0
    good_acts: int = 0
    crimes_committed: int = 0
    notoriety: float = 0.0
    trust_in_govt: float = 0.5
    protest_count: int = 0
    grid_x: GridCoordinate = GridCoordinate(0)
    grid_y: GridCoordinate = GridCoordinate(0)
    job_type: JobType = JobType.UNEMPLOYED
    spouse: Optional[AgentId] = None
    enemies: List[AgentId] = field(default_factory=list)
    community_id: Optional[str] = None
    last_action: ActionType = ActionType.IDLE
    last_reasoning: str = ""
