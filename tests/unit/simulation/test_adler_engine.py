"""Tests for the Adler comparison engine — Maslow score and social comparison.

Verifies compute_maslow_score and adler_comparison for upward, downward,
and equal comparison scenarios, including clamping and determinism.
"""

from copy import deepcopy

import pytest

from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentState,
    AgentTraits,
)
from shared.schemas.simulation_state import SimulationState
from shared.types.aliases import AgentId, NeedValue
from shared.types.enums import NeedType
from shared.constants.defaults import (
    ADLER_GAP_THRESHOLD,
)
from simulation.agents.adler_engine import (
    adler_comparison,
    compute_maslow_score,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(
    *,
    agent_id: str = "test-agent",
    food: float = 0.5,
    water: float = 0.5,
    sleep: float = 0.5,
    safety: float = 0.5,
    financial_security: float = 0.5,
    social_connection: float = 0.5,
    self_esteem: float = 0.5,
    reputation: float = 0.5,
    inferiority_gap: float = 0.5,
    happiness_score: float = 0.5,
    unlust: float = 0.0,
    dominance_urge: float = 0.5,
) -> AgentState:
    """Build an AgentState with the given need levels, traits, and emotion state.

    Args:
        agent_id: Unique agent identifier.
        food: FOOD need level (0.0 to 1.0).
        water: WATER need level (0.0 to 1.0).
        sleep: SLEEP need level (0.0 to 1.0).
        safety: SAFETY need level (0.0 to 1.0).
        financial_security: FINANCIAL_SECURITY need level (0.0 to 1.0).
        social_connection: SOCIAL_CONNECTION need level (0.0 to 1.0).
        self_esteem: SELF_ESTEEM need level (0.0 to 1.0).
        reputation: REPUTATION need level (0.0 to 1.0).
        inferiority_gap: INFERIORITY_GAP need level (0.0 to 1.0).
        happiness_score: Happiness score (0.0 to 1.0).
        unlust: Unlust level (0.0 to 1.0).
        dominance_urge: Dominance urge trait (0.0 to 1.0).

    Returns:
        A configured AgentState.
    """
    needs = AgentNeeds(
        levels={
            NeedType.FOOD: NeedValue(food),
            NeedType.WATER: NeedValue(water),
            NeedType.SLEEP: NeedValue(sleep),
            NeedType.SAFETY: NeedValue(safety),
            NeedType.FINANCIAL_SECURITY: NeedValue(financial_security),
            NeedType.SOCIAL_CONNECTION: NeedValue(social_connection),
            NeedType.SELF_ESTEEM: NeedValue(self_esteem),
            NeedType.REPUTATION: NeedValue(reputation),
            NeedType.INFERIORITY_GAP: NeedValue(inferiority_gap),
        }
    )
    emotions = AgentEmotions(happiness_score=happiness_score)
    traits = AgentTraits(dominance_urge=dominance_urge)
    return AgentState(
        id=AgentId(agent_id),
        needs=needs,
        emotions=emotions,
        traits=traits,
        unlust=unlust,
    )


def _make_world() -> SimulationState:
    """Build a default SimulationState for adler_comparison calls.

    Returns:
        A default SimulationState.
    """
    return SimulationState()


# ===========================================================================
# Maslow score tests
# ===========================================================================


class TestMaslowScore:
    """Weighted Maslow hierarchy score computation."""

    def test_maslow_score_all_satisfied(self) -> None:
        """All needs=1.0, happiness=1.0 -> score close to 1.0."""
        agent = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=1.0, reputation=1.0,
            happiness_score=1.0,
        )
        score = compute_maslow_score(agent)
        # All weights sum to 1.0, all terms = 1.0 * weight
        assert score == pytest.approx(1.0)

    def test_maslow_score_all_deprived(self) -> None:
        """All needs=0.0, happiness=0.0 -> score close to 0.0."""
        agent = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
        )
        score = compute_maslow_score(agent)
        assert score == pytest.approx(0.0)

    def test_maslow_score_in_range(self) -> None:
        """Score is always clamped to [0.0, 1.0]."""
        # Below zero
        agent_low = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
        )
        assert compute_maslow_score(agent_low) == 0.0

        # Above one
        agent_high = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=1.0, reputation=1.0,
            happiness_score=1.0,
        )
        assert compute_maslow_score(agent_high) == 1.0

        # Mid-range
        agent_mid = _make_agent(
            food=0.5, water=0.5, sleep=0.5, safety=0.5,
            financial_security=0.5, social_connection=0.5,
            self_esteem=0.5, reputation=0.5,
            happiness_score=0.5,
        )
        score = compute_maslow_score(agent_mid)
        assert 0.0 <= score <= 1.0

    def test_maslow_score_deterministic(self) -> None:
        """Same agent state -> same score (pure function)."""
        agent = _make_agent(
            food=0.3, water=0.7, sleep=0.6, safety=0.9,
            financial_security=0.5, social_connection=0.4,
            self_esteem=0.8, reputation=0.7,
            happiness_score=0.6,
        )
        assert compute_maslow_score(agent) == compute_maslow_score(agent)
        assert compute_maslow_score(agent) == compute_maslow_score(agent)

    def test_maslow_score_weights(self) -> None:
        """Higher layers weighted more: SELF_ESTEEM (0.13) > FOOD (0.10)."""
        agent_esteem = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=1.0, reputation=0.0,
            happiness_score=0.0,
        )
        agent_food = _make_agent(
            food=1.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
        )
        # SELF_ESTEEM weight = 0.13 > FOOD weight = 0.10
        esteem_score = compute_maslow_score(agent_esteem)
        food_score = compute_maslow_score(agent_food)
        assert esteem_score > food_score


# ===========================================================================
# Adler comparison — upward tests
# ===========================================================================


class TestUpwardComparison:
    """When other is much better off -> upward comparison effects."""

    def _setup_upward_gap(self, gap: float = 0.3) -> tuple[AgentState, AgentState, SimulationState]:
        """Create an agent pair with a specific upward gap (other - self).

        The other agent's scores are elevated so that other_score - self_score == gap.

        Args:
            gap: The score difference (other better than self).

        Returns:
            Tuple of (agent, other, world).
        """
        # Self is mediocre across the board
        agent = _make_agent(
            food=0.5, water=0.5, sleep=0.5, safety=0.5,
            financial_security=0.5, social_connection=0.5,
            self_esteem=0.5, reputation=0.5,
            happiness_score=0.5,
            inferiority_gap=0.5,
            unlust=0.5,
            dominance_urge=0.5,
        )
        # Other is better — set happiness_score to produce approximate gap
        # self_score = 8 * 0.5 * 0.10-0.13 + 0.5 * 0.15 = 0.5 * (0.10+0.10+0.08+0.12+0.10+0.12+0.13+0.10+0.15)
        #            = 0.5 * 1.0 = 0.5
        # To get gap of e.g. 0.3, other_score needs to be 0.8
        # 0.13*x + ... = 0.8, easiest: push happiness + social + safety up
        other = _make_agent(
            food=0.5, water=0.5, sleep=0.5, safety=0.5,
            financial_security=0.5, social_connection=0.5,
            self_esteem=0.5, reputation=0.5,
            happiness_score=0.5,
            inferiority_gap=0.5,
            unlust=0.3,
            dominance_urge=0.5,
        )
        # Manually raise the other's scores to produce the gap
        # We'll calculate: for gap=0.3, other_score = self_score + 0.3
        # self_score = 0.5
        # other_score = 0.8
        # Set happiness=1.0 (+0.5*0.15=0.075) not enough
        # Let's just set the other's needs to bespoke values
        # other_score = food*0.10 + water*0.10 + sleep*0.08 + safety*0.12 + financial*0.10
        #               + social*0.12 + esteem*0.13 + reputation*0.10 + happiness*0.15
        # Set them all = 1.0 -> score = 1.0 -> gap = 0.5
        # We need exact gap, let's compute precisely:
        # self_score with all 0.5 = 0.5
        # To get score = S, we need sum of weighted terms = S
        # Easiest: set everything to X, except happiness
        # X*(0.10+0.10+0.08+0.12+0.10+0.12+0.13+0.10) + happiness*0.15 = X*0.85 + happiness*0.15 = S
        # For S = 0.8 with X=0.5: 0.5*0.85 + h*0.15 = 0.8 -> 0.425 + 0.15h = 0.8 -> h = 2.5 (impossible)
        # So lift needs too. X=0.8: 0.8*0.85 + h*0.15 = 0.8 -> 0.68 + 0.15h = 0.8 -> h = 0.8
        # So set all needs=0.8, happiness=0.8
        other.needs.set_level(NeedType.FOOD, 0.8)
        other.needs.set_level(NeedType.WATER, 0.8)
        other.needs.set_level(NeedType.SLEEP, 0.8)
        other.needs.set_level(NeedType.SAFETY, 0.8)
        other.needs.set_level(NeedType.FINANCIAL_SECURITY, 0.8)
        other.needs.set_level(NeedType.SOCIAL_CONNECTION, 0.8)
        other.needs.set_level(NeedType.SELF_ESTEEM, 0.8)
        other.needs.set_level(NeedType.REPUTATION, 0.8)
        other.emotions.happiness_score = 0.8

        world = _make_world()
        return agent, other, world

    def test_upward_comparison_inferiority(self) -> None:
        """Other much better off -> inferiority_gap increases."""
        agent, other, world = self._setup_upward_gap(gap=0.3)
        initial_inferiority = agent.needs.get_level(NeedType.INFERIORITY_GAP)

        adler_comparison(agent, other, world)

        # Gap = other_score - self_score. With all=0.5 for self and all=0.8 + happiness=0.8 for other:
        # self_score = 0.5, other_score = 0.8*0.85 + 0.8*0.15 = 0.8
        # gap = 0.3, which is > 0.15 threshold
        # inferiority_gap = 0.5 + 0.3 * 0.1 = 0.53
        assert agent.needs.get_level(NeedType.INFERIORITY_GAP) > initial_inferiority

    def test_upward_comparison_self_esteem_drop(self) -> None:
        """Self_esteem decreases on upward comparison."""
        agent, other, world = self._setup_upward_gap(gap=0.3)
        initial_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)

        adler_comparison(agent, other, world)

        assert agent.needs.get_level(NeedType.SELF_ESTEEM) < initial_esteem

    def test_upward_comparison_unlust_increase(self) -> None:
        """Unlust increases on upward comparison."""
        agent, other, world = self._setup_upward_gap(gap=0.3)
        initial_unlust = agent.unlust

        adler_comparison(agent, other, world)

        assert agent.unlust > initial_unlust

    def test_upward_comparison_dominance_increase(self) -> None:
        """Dominance_urge increases (compensatory drive) on upward comparison."""
        agent, other, world = self._setup_upward_gap(gap=0.3)
        initial_dominance = agent.traits.dominance_urge

        adler_comparison(agent, other, world)

        assert agent.traits.dominance_urge > initial_dominance

    def test_upward_comparison_proportional(self) -> None:
        """Larger gap -> larger changes in inferiority_gap."""
        agent1, other1, world = self._setup_upward_gap(gap=0.3)
        agent2, other2, _ = self._setup_upward_gap(gap=0.3)
        # Make agent2/other2 have a bigger gap (gap ~0.5)
        # Set all needs and happiness for other2 to 1.0
        other2.needs.set_level(NeedType.FOOD, 1.0)
        other2.needs.set_level(NeedType.WATER, 1.0)
        other2.needs.set_level(NeedType.SLEEP, 1.0)
        other2.needs.set_level(NeedType.SAFETY, 1.0)
        other2.needs.set_level(NeedType.FINANCIAL_SECURITY, 1.0)
        other2.needs.set_level(NeedType.SOCIAL_CONNECTION, 1.0)
        other2.needs.set_level(NeedType.SELF_ESTEEM, 1.0)
        other2.needs.set_level(NeedType.REPUTATION, 1.0)
        other2.emotions.happiness_score = 1.0

        adler_comparison(agent1, other1, world)
        adler_comparison(agent2, other2, world)

        # agent2 should have larger inferiority increase (bigger gap)
        assert (
            agent2.needs.get_level(NeedType.INFERIORITY_GAP)
            > agent1.needs.get_level(NeedType.INFERIORITY_GAP)
        )


# ===========================================================================
# Adler comparison — downward tests
# ===========================================================================


class TestDownwardComparison:
    """When self is much better off -> downward comparison effects."""

    def test_downward_comparison_self_esteem_boost(self) -> None:
        """Self much better off -> self_esteem increases by ADLER_SUPERIORITY_GAIN."""
        # Self has higher scores
        agent = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=0.5, reputation=1.0,
            happiness_score=1.0,
            inferiority_gap=0.5,
            unlust=0.3,
            dominance_urge=0.5,
        )
        # Other is worse off
        other = _make_agent(
            food=0.2, water=0.2, sleep=0.2, safety=0.2,
            financial_security=0.2, social_connection=0.2,
            self_esteem=0.2, reputation=0.2,
            happiness_score=0.2,
        )
        world = _make_world()
        initial_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)

        adler_comparison(agent, other, world)

        expected_esteem = initial_esteem + 0.02  # ADLER_SUPERIORITY_GAIN
        assert agent.needs.get_level(NeedType.SELF_ESTEEM) == pytest.approx(expected_esteem)

    def test_downward_comparison_inferiority_decrease(self) -> None:
        """Inferiority_gap decreases on downward comparison."""
        agent = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=0.5, reputation=1.0,
            happiness_score=1.0,
            inferiority_gap=0.5,
            unlust=0.3,
        )
        other = _make_agent(
            food=0.2, water=0.2, sleep=0.2, safety=0.2,
            financial_security=0.2, social_connection=0.2,
            self_esteem=0.2, reputation=0.2,
            happiness_score=0.2,
        )
        world = _make_world()

        adler_comparison(agent, other, world)

        expected_inferiority = 0.5 - 0.02
        assert agent.needs.get_level(NeedType.INFERIORITY_GAP) == pytest.approx(expected_inferiority)

    def test_downward_comparison_unlust_decrease(self) -> None:
        """Unlust decreases on downward comparison."""
        agent = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=0.5, reputation=1.0,
            happiness_score=1.0,
            inferiority_gap=0.5,
            unlust=0.3,
        )
        other = _make_agent(
            food=0.2, water=0.2, sleep=0.2, safety=0.2,
            financial_security=0.2, social_connection=0.2,
            self_esteem=0.2, reputation=0.2,
            happiness_score=0.2,
        )
        world = _make_world()

        adler_comparison(agent, other, world)

        expected_unlust = max(0.0, 0.3 - 0.02)
        assert agent.unlust == pytest.approx(expected_unlust)


# ===========================================================================
# Adler comparison — equal / small gap tests
# ===========================================================================


class TestEqualComparison:
    """When scores are close — no change expected."""

    def test_equal_no_change(self) -> None:
        """Equal scores (same agent) -> gap=0, no changes."""
        agent = _make_agent(
            food=0.5, water=0.5, sleep=0.5, safety=0.5,
            financial_security=0.5, social_connection=0.5,
            self_esteem=0.5, reputation=0.5,
            happiness_score=0.5,
            inferiority_gap=0.5,
            unlust=0.3,
            dominance_urge=0.5,
        )
        other = deepcopy(agent)
        world = _make_world()

        original_inferiority = agent.needs.get_level(NeedType.INFERIORITY_GAP)
        original_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
        original_unlust = agent.unlust
        original_dominance = agent.traits.dominance_urge

        adler_comparison(agent, other, world)

        assert agent.needs.get_level(NeedType.INFERIORITY_GAP) == original_inferiority
        assert agent.needs.get_level(NeedType.SELF_ESTEEM) == original_esteem
        assert agent.unlust == original_unlust
        assert agent.traits.dominance_urge == original_dominance

    def test_small_gap_no_change(self) -> None:
        """Gap = 0.10 (below 0.15 threshold) -> no changes."""
        # Self score ~0.5, other needs = 0.6 -> other_score = 0.6
        # gap = 0.10 which is < 0.15
        agent = _make_agent(
            food=0.5, water=0.5, sleep=0.5, safety=0.5,
            financial_security=0.5, social_connection=0.5,
            self_esteem=0.5, reputation=0.5,
            happiness_score=0.5,
            inferiority_gap=0.5,
            unlust=0.3,
            dominance_urge=0.5,
        )
        # Slightly better but gap small enough
        other = _make_agent(
            food=0.6, water=0.6, sleep=0.6, safety=0.6,
            financial_security=0.6, social_connection=0.6,
            self_esteem=0.6, reputation=0.6,
            happiness_score=0.6,
        )
        world = _make_world()

        # Verify gap is small
        self_score = compute_maslow_score(agent)
        other_score = compute_maslow_score(other)
        gap = other_score - self_score
        assert gap < ADLER_GAP_THRESHOLD, f"Gap {gap} should be below threshold"

        original_inferiority = agent.needs.get_level(NeedType.INFERIORITY_GAP)
        original_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
        original_unlust = agent.unlust
        original_dominance = agent.traits.dominance_urge

        adler_comparison(agent, other, world)

        assert agent.needs.get_level(NeedType.INFERIORITY_GAP) == original_inferiority
        assert agent.needs.get_level(NeedType.SELF_ESTEEM) == original_esteem
        assert agent.unlust == original_unlust
        assert agent.traits.dominance_urge == original_dominance


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    """Clamping and determinism edge cases."""

    def test_unlust_clamped(self) -> None:
        """Unlust doesn't exceed 1.0 after repeated upward comparisons."""
        agent = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
            unlust=0.9,
            inferiority_gap=0.5,
            dominance_urge=0.5,
        )
        other = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=1.0, reputation=1.0,
            happiness_score=1.0,
        )
        world = _make_world()

        # Apply comparison multiple times
        for _ in range(10):
            adler_comparison(agent, other, world)

        assert agent.unlust <= 1.0

    def test_dominance_clamped(self) -> None:
        """Dominance_urge doesn't exceed 1.0 after repeated upward comparisons."""
        agent = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
            dominance_urge=0.9,
            unlust=0.5,
            inferiority_gap=0.5,
        )
        other = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=1.0, reputation=1.0,
            happiness_score=1.0,
        )
        world = _make_world()

        for _ in range(10):
            adler_comparison(agent, other, world)

        assert agent.traits.dominance_urge <= 1.0

    def test_self_esteem_clamped(self) -> None:
        """Self_esteem stays in [0, 1] via set_level clamping after repeated downward comparisons."""
        agent = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=0.99, reputation=1.0,
            happiness_score=1.0,
            inferiority_gap=0.5,
            unlust=0.3,
            dominance_urge=0.5,
        )
        other = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
        )
        world = _make_world()

        for _ in range(10):
            adler_comparison(agent, other, world)
            esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
            assert 0.0 <= esteem <= 1.0

    def test_inferiority_clamped(self) -> None:
        """Inferiority_gap stays in [0, 1] via set_level clamping."""
        agent = _make_agent(
            food=0.0, water=0.0, sleep=0.0, safety=0.0,
            financial_security=0.0, social_connection=0.0,
            self_esteem=0.0, reputation=0.0,
            happiness_score=0.0,
            inferiority_gap=0.95,
            unlust=0.3,
            dominance_urge=0.5,
        )
        other = _make_agent(
            food=1.0, water=1.0, sleep=1.0, safety=1.0,
            financial_security=1.0, social_connection=1.0,
            self_esteem=1.0, reputation=1.0,
            happiness_score=1.0,
        )
        world = _make_world()

        for _ in range(10):
            adler_comparison(agent, other, world)
            inferiority = agent.needs.get_level(NeedType.INFERIORITY_GAP)
            assert 0.0 <= inferiority <= 1.0

    def test_determinism(self) -> None:
        """Same agents, same comparison -> same results."""
        agent_a = _make_agent(
            food=0.3, water=0.7, sleep=0.6, safety=0.9,
            financial_security=0.5, social_connection=0.4,
            self_esteem=0.8, reputation=0.7,
            happiness_score=0.6,
            inferiority_gap=0.4,
            unlust=0.2,
            dominance_urge=0.6,
        )
        other_a = _make_agent(
            food=0.8, water=0.6, sleep=0.7, safety=0.5,
            financial_security=0.9, social_connection=0.3,
            self_esteem=0.6, reputation=0.8,
            happiness_score=0.7,
            inferiority_gap=0.3,
            unlust=0.1,
            dominance_urge=0.4,
        )

        agent_b = deepcopy(agent_a)
        other_b = deepcopy(other_a)

        world = _make_world()

        adler_comparison(agent_a, other_a, world)
        adler_comparison(agent_b, other_b, world)

        assert agent_a.needs.get_level(NeedType.INFERIORITY_GAP) == pytest.approx(
            agent_b.needs.get_level(NeedType.INFERIORITY_GAP)
        )
        assert agent_a.needs.get_level(NeedType.SELF_ESTEEM) == pytest.approx(
            agent_b.needs.get_level(NeedType.SELF_ESTEEM)
        )
        assert agent_a.unlust == pytest.approx(agent_b.unlust)
        assert agent_a.traits.dominance_urge == pytest.approx(agent_b.traits.dominance_urge)
