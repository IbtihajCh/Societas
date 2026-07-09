"""Tests for shared/schemas/ — verify new fields and defaults."""

from shared.schemas.agent_state import (
    AgentDecisionScores,
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
)
from shared.schemas.policy import GovernmentPolicy, ImpactDelta, Policy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult, TickResult
from shared.types.aliases import AgentId, TickNumber
from shared.types.enums import (
    ActionType,
    Culture,
    EducationLevel,
    EmotionType,
    Gender,
    JobType,
    NeedType,
    WealthClass,
)


class TestAgentTraits:
    def test_has_8_fields(self) -> None:
        traits = AgentTraits()
        assert traits.morality == 0.5
        assert traits.creativity == 0.5
        assert traits.ambition == 0.5
        assert traits.resilience == 0.5
        assert traits.dominance_urge == 0.5
        assert traits.anger_tendency == 0.5
        assert traits.extraversion == 0.5
        assert traits.risk_tolerance == 0.5

    def test_can_set_values(self) -> None:
        traits = AgentTraits(morality=0.8, creativity=0.3)
        assert traits.morality == 0.8
        assert traits.creativity == 0.3


class TestAgentNeeds:
    def test_default_empty(self) -> None:
        needs = AgentNeeds()
        assert len(needs.levels) == 0

    def test_set_and_get(self) -> None:
        needs = AgentNeeds()
        needs.set_level(NeedType.FOOD, 0.3)
        assert needs.get_level(NeedType.FOOD) == 0.3

    def test_clamps_to_0_1(self) -> None:
        needs = AgentNeeds()
        needs.set_level(NeedType.FOOD, 1.5)
        assert needs.get_level(NeedType.FOOD) == 1.0
        needs.set_level(NeedType.FOOD, -0.5)
        assert needs.get_level(NeedType.FOOD) == 0.0

    def test_default_value(self) -> None:
        needs = AgentNeeds()
        assert needs.get_level(NeedType.WATER) == 0.5

    def test_most_urgent_need(self) -> None:
        needs = AgentNeeds()
        needs.set_level(NeedType.FOOD, 0.2)
        needs.set_level(NeedType.WATER, 0.8)
        assert needs.get_most_urgent_need() == NeedType.FOOD


class TestAgentEmotions:
    def test_defaults(self) -> None:
        emotions = AgentEmotions()
        assert emotions.primary == EmotionType.NORMAL
        assert emotions.emotion_timer == 0
        assert emotions.happiness_score == 0.5


class TestAgentResources:
    def test_defaults(self) -> None:
        resources = AgentResources()
        assert resources.money == 100.0
        assert resources.base_salary == 0.0
        assert resources.employed is False
        assert resources.education == EducationLevel.PRIMARY
        assert resources.property is False
        assert resources.health == 1.0


class TestAgentState:
    def test_can_create_with_id(self) -> None:
        state = AgentState(id=AgentId("test-1"))
        assert state.id == "test-1"
        assert state.is_alive is True
        assert state.age == 25

    def test_new_fields_exist(self) -> None:
        state = AgentState(id=AgentId("test-1"))
        assert state.gender == Gender.MALE
        assert state.culture == Culture.A
        assert state.born_tick == 0
        assert state.unlust == 0.0
        assert state.good_acts == 0
        assert state.crimes_committed == 0
        assert state.notoriety == 0.0
        assert state.trust_in_govt == 0.5
        assert state.protest_count == 0
        assert state.grid_x == 0
        assert state.grid_y == 0
        assert state.job_type == JobType.UNEMPLOYED
        assert state.spouse is None
        assert state.enemies == []
        assert state.community_id is None
        assert state.last_action == ActionType.IDLE
        assert state.last_reasoning == ""

    def test_wealth_class_default(self) -> None:
        state = AgentState(id=AgentId("test-1"))
        assert state.wealth_class == WealthClass.POOR


class TestImpactDelta:
    def test_defaults(self) -> None:
        delta = ImpactDelta()
        assert delta.money_delta == 0.0
        assert delta.food_delta == 0.0
        assert delta.safety_delta == 0.0
        assert delta.social_delta == 0.0
        assert delta.anger_spike == 0.0

    def test_can_set_values(self) -> None:
        delta = ImpactDelta(money_delta=-50.0, food_delta=0.05)
        assert delta.money_delta == -50.0
        assert delta.food_delta == 0.05


class TestGovernmentPolicy:
    def test_has_impact_deltas(self) -> None:
        gov = GovernmentPolicy()
        assert gov.impact_deltas == {}

    def test_can_set_impact_deltas(self) -> None:
        gov = GovernmentPolicy()
        gov.impact_deltas[WealthClass.POOR] = ImpactDelta(money_delta=-10.0)
        assert gov.impact_deltas[WealthClass.POOR].money_delta == -10.0


class TestSimulationState:
    def test_new_world_fields(self) -> None:
        state = SimulationState()
        assert state.food_availability == 0.85
        assert state.water_availability == 0.90
        assert state.crime_rate == 0.05
        assert state.protest_intensity == 0.0
        assert state.unemployment_rate == 0.10
        assert state.tax_rate == 0.15
        assert state.welfare_enabled is False
        assert state.welfare_amount == 8.0


class TestAgentActionResult:
    def test_has_metadata(self) -> None:
        result = AgentActionResult(agent_id=AgentId("a1"))
        assert result.metadata == {}
        assert result.action == ActionType.IDLE

    def test_can_set_metadata(self) -> None:
        result = AgentActionResult(
            agent_id=AgentId("a1"),
            action=ActionType.WORK,
            metadata={"source": "e2b_brain", "reasoning": "I need money"},
        )
        assert result.metadata["source"] == "e2b_brain"
