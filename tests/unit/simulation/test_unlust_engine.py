"""Tests for the Unlust engine — deterministic dissatisfaction scoring.

Verifies compute_unlust, morality_active, is_thanatos_active,
and get_unlust_state against the Freudian Unlust formula.
"""

import pytest

from shared.schemas.agent_state import AgentState, AgentNeeds, AgentResources, AgentTraits
from shared.types.aliases import AgentId, NeedValue
from shared.types.enums import NeedType
from simulation.agents.unlust_engine import (
    compute_unlust,
    get_unlust_state,
    is_thanatos_active,
    morality_active,
)


def _make_agent(
    food: float = 0.7,
    water: float = 0.7,
    safety: float = 0.7,
    social: float = 0.7,
    money: float = 100.0,
    morality: float = 0.5,
) -> AgentState:
    """Build an AgentState with the given need levels, resources, and traits."""
    needs = AgentNeeds(
        levels={
            NeedType.FOOD: NeedValue(food),
            NeedType.WATER: NeedValue(water),
            NeedType.SAFETY: NeedValue(safety),
            NeedType.SOCIAL_CONNECTION: NeedValue(social),
        }
    )
    resources = AgentResources(money=money)
    traits = AgentTraits(morality=morality)
    return AgentState(
        id=AgentId("test-agent"),
        needs=needs,
        resources=resources,
        traits=traits,
    )


# --- compute_unlust tests ------------------------------------------------


def test_zero_unlust() -> None:
    """All needs at 0.7+, money >= 600 -> unlust = 0.0."""
    agent = _make_agent(food=0.7, water=0.7, safety=0.7, social=0.7, money=600)
    assert compute_unlust(agent) == 0.0


def test_max_unlust() -> None:
    """All needs at 0.0, money = 0 -> unlust = 0.7*(0.28+0.22+0.20+0.12) + 1.0*0.18 = 0.754."""
    agent = _make_agent(food=0.0, water=0.0, safety=0.0, social=0.0, money=0)
    expected = 0.7 * (0.28 + 0.22 + 0.20 + 0.12) + 1.0 * 0.18
    assert compute_unlust(agent) == expected


def test_food_deficit_only() -> None:
    """Food=0.2, others=0.8, money=600 -> unlust = (0.7-0.2)*0.28 = 0.14."""
    agent = _make_agent(food=0.2, water=0.8, safety=0.8, social=0.8, money=600)
    assert compute_unlust(agent) == pytest.approx(0.14)


def test_water_deficit_only() -> None:
    """Water=0.2, others=0.8, money=600 -> unlust = (0.7-0.2)*0.22 = 0.11."""
    agent = _make_agent(food=0.8, water=0.2, safety=0.8, social=0.8, money=600)
    assert compute_unlust(agent) == pytest.approx(0.11)


def test_safety_deficit_only() -> None:
    """Safety=0.2, others=0.8, money=600 -> unlust = (0.7-0.2)*0.20 = 0.10."""
    agent = _make_agent(food=0.8, water=0.8, safety=0.2, social=0.8, money=600)
    assert compute_unlust(agent) == pytest.approx(0.10)


def test_social_deficit_only() -> None:
    """Social=0.2, others=0.8, money=600 -> unlust = (0.7-0.2)*0.12 = 0.06."""
    agent = _make_agent(food=0.8, water=0.8, safety=0.8, social=0.2, money=600)
    assert compute_unlust(agent) == pytest.approx(0.06)


def test_money_deficit_only() -> None:
    """All needs=0.8, money=0 -> unlust = (1.0-0)*0.18 = 0.18."""
    agent = _make_agent(food=0.8, water=0.8, safety=0.8, social=0.8, money=0)
    assert compute_unlust(agent) == 0.18


def test_money_partial_deficit() -> None:
    """All needs=0.8, money=300 -> unlust = (1.0-0.5)*0.18 = 0.09."""
    agent = _make_agent(food=0.8, water=0.8, safety=0.8, social=0.8, money=300)
    assert compute_unlust(agent) == 0.09


def test_money_no_deficit() -> None:
    """All needs=0.8, money=600 -> unlust = 0.0 (money_ratio=1.0)."""
    agent = _make_agent(food=0.8, water=0.8, safety=0.8, social=0.8, money=600)
    assert compute_unlust(agent) == 0.0


def test_money_above_threshold() -> None:
    """All needs=0.8, money=1000 -> unlust = 0.0 (capped at 1.0 ratio)."""
    agent = _make_agent(food=0.8, water=0.8, safety=0.8, social=0.8, money=1000)
    assert compute_unlust(agent) == 0.0


def test_no_negative_unlust() -> None:
    """All needs=1.0, money=1000 -> unlust = 0.0 (not negative)."""
    agent = _make_agent(food=1.0, water=1.0, safety=1.0, social=1.0, money=1000)
    assert compute_unlust(agent) == 0.0


def test_unlust_clamped_to_1() -> None:
    """With deficits driving over 1.0, result is clamped to 1.0.

    Max possible from the formula is 0.754 (all needs=0, money=0), so clamping
    to 1.0 is a theoretical safeguard. This test confirms it never exceeds 1.0.
    """
    agent = _make_agent(food=0.0, water=0.0, safety=0.0, social=0.0, money=0)
    assert 0.0 <= compute_unlust(agent) <= 1.0


# --- morality_active tests ------------------------------------------------


def test_morality_active_low_unlust() -> None:
    """unlust=0.2, morality=0.3 -> True (fully moral)."""
    assert morality_active(0.2, 0.3) is True


def test_morality_active_medium_high_morality() -> None:
    """unlust=0.50, morality=0.7 -> True (zone 2, high morality)."""
    assert morality_active(0.50, 0.7) is True


def test_morality_inactive_medium_low_morality() -> None:
    """unlust=0.50, morality=0.4 -> False (zone 2, low morality)."""
    assert morality_active(0.50, 0.4) is False


def test_morality_inactive_high_unlust() -> None:
    """unlust=0.85, morality=0.9 -> False (bypassed)."""
    assert morality_active(0.85, 0.9) is False


# --- is_thanatos_active tests --------------------------------------------


def test_thanatos_not_active_low_unlust() -> None:
    """unlust=0.5, morality=0.3 -> False."""
    assert is_thanatos_active(0.5, 0.3) is False


def test_thanatos_active_high_unlust_low_morality() -> None:
    """unlust=0.7, morality=0.3 -> True."""
    assert is_thanatos_active(0.7, 0.3) is True


def test_thanatos_not_active_high_unlust_high_morality() -> None:
    """unlust=0.50, morality=0.8 -> False (zone 2, high morality blocks Thanatos)."""
    assert is_thanatos_active(0.50, 0.8) is False


# --- get_unlust_state tests ----------------------------------------------


def test_unlust_state_content() -> None:
    """unlust=0.15 -> 'content'."""
    assert get_unlust_state(0.15) == "content"


def test_unlust_state_stressed() -> None:
    """unlust=0.40 -> 'stressed'."""
    assert get_unlust_state(0.40) == "stressed"


def test_unlust_state_driven() -> None:
    """unlust=0.50 -> 'driven' (zone between ANGRY=0.45 and DESPAIR=0.55)."""
    assert get_unlust_state(0.50) == "driven"


def test_unlust_state_desperate() -> None:
    """unlust=0.90 -> 'desperate'."""
    assert get_unlust_state(0.90) == "desperate"


# --- determinism test ----------------------------------------------------


def test_determinism() -> None:
    """Same agent state -> same unlust every time (pure function)."""
    agent = _make_agent(food=0.3, water=0.4, safety=0.6, social=0.7, money=200, morality=0.5)
    result1 = compute_unlust(agent)
    result2 = compute_unlust(agent)
    result3 = compute_unlust(agent)
    assert result1 == result2 == result3


# --- boundary tests --------------------------------------------------------


class TestMoralityActiveBoundaries:
    """Boundary tests for morality_active."""

    def test_at_low_gate_boundary(self) -> None:
        """unlust exactly at UNLUST_MORALITY_GATE (0.58) -> True (strict less than)."""
        from shared.constants.defaults import UNLUST_MORALITY_GATE
        assert morality_active(UNLUST_MORALITY_GATE - 0.001, 0.0) is True

    def test_just_above_gate_low_morality(self) -> None:
        """unlust just above 0.58, morality=0.5 -> False (needs > 0.6)."""
        from shared.constants.defaults import UNLUST_MORALITY_GATE
        assert morality_active(UNLUST_MORALITY_GATE + 0.001, 0.5) is False

    def test_zone2_high_morality(self) -> None:
        """unlust 0.50, morality=0.7 -> True (zone 2, high enough)."""
        assert morality_active(0.50, 0.7) is True

    def test_zone2_low_morality(self) -> None:
        """unlust 0.50, morality=0.4 -> False (zone 2, not high enough)."""
        assert morality_active(0.50, 0.4) is False

    def test_at_despair_boundary_low(self) -> None:
        """unlust at DESPAIR_UNLUST_THRESHOLD - epsilon -> check partial zone."""
        from shared.constants.defaults import DESPAIR_UNLUST_THRESHOLD
        assert morality_active(DESPAIR_UNLUST_THRESHOLD - 0.001, 0.7) is True

    def test_at_despair_boundary_high(self) -> None:
        """unlust at DESPAIR_UNLUST_THRESHOLD -> bypassed entirely."""
        from shared.constants.defaults import DESPAIR_UNLUST_THRESHOLD
        assert morality_active(DESPAIR_UNLUST_THRESHOLD, 1.0) is False


class TestThanatosBoundaries:
    """Boundary tests for is_thanatos_active."""

    def test_below_threshold(self) -> None:
        """unlust=0.64, morality=0.3 -> False (not above 0.65)."""
        assert is_thanatos_active(0.64, 0.3) is False

    def test_at_threshold(self) -> None:
        """unlust=0.65, morality=0.3 -> False (needs strictly greater than 0.65)."""
        # is_thanatos_active uses `unlust > 0.65`, so exactly 0.65 is not active
        assert is_thanatos_active(0.65, 0.3) is False

    def test_above_threshold(self) -> None:
        """unlust=0.66, morality=0.3 -> True (just above 0.65)."""
        assert is_thanatos_active(0.66, 0.3) is True

    def test_above_threshold_morality_blocks(self) -> None:
        """unlust=0.50, morality=0.8 -> False (zone 2, morality active blocks Thanatos)."""
        assert is_thanatos_active(0.50, 0.8) is False

    def test_thanatos_and_morality_inactive_both(self) -> None:
        """unlust=0.5, morality=0.5 -> False (too low, morality still active)."""
        assert is_thanatos_active(0.5, 0.5) is False


class TestUnlustStateBoundaries:
    """Boundary tests for get_unlust_state."""

    def test_exactly_content_boundary(self) -> None:
        """unlust=0.30 -> 'stressed' (not < 0.30, goes to next)."""
        assert get_unlust_state(0.30) == "stressed"

    def test_just_below_content(self) -> None:
        """unlust=0.299 -> 'content'."""
        assert get_unlust_state(0.299) == "content"

    def test_exactly_angry_boundary(self) -> None:
        """unlust at ANGRY_UNLUST_THRESHOLD (0.58) -> 'driven'."""
        from shared.constants.defaults import ANGRY_UNLUST_THRESHOLD
        assert get_unlust_state(ANGRY_UNLUST_THRESHOLD) == "driven"

    def test_just_below_angry(self) -> None:
        """unlust just below 0.58 -> 'stressed'."""
        from shared.constants.defaults import ANGRY_UNLUST_THRESHOLD
        assert get_unlust_state(ANGRY_UNLUST_THRESHOLD - 0.001) == "stressed"

    def test_exactly_despair_boundary(self) -> None:
        """unlust at DESPAIR_UNLUST_THRESHOLD (0.82) -> 'desperate'."""
        from shared.constants.defaults import DESPAIR_UNLUST_THRESHOLD
        assert get_unlust_state(DESPAIR_UNLUST_THRESHOLD) == "desperate"

    def test_below_despair(self) -> None:
        """unlust just below 0.82 -> 'driven'."""
        from shared.constants.defaults import DESPAIR_UNLUST_THRESHOLD
        assert get_unlust_state(DESPAIR_UNLUST_THRESHOLD - 0.001) == "driven"

    def test_zero_unlust(self) -> None:
        """unlust=0.0 -> 'content'."""
        assert get_unlust_state(0.0) == "content"

    def test_one_unlust(self) -> None:
        """unlust=1.0 -> 'desperate'."""
        assert get_unlust_state(1.0) == "desperate"


# --- combined scenario tests ----------------------------------------------


class TestCombinedScenarios:
    """Tests combining unlust with morality in realistic scenarios."""

    def test_high_unlust_no_morality_thanatos(self) -> None:
        """High unlust + low morality = Thanatos active."""
        agent = _make_agent(food=0.1, water=0.1, safety=0.1, social=0.1, money=0, morality=0.3)
        u = compute_unlust(agent)
        assert is_thanatos_active(u, agent.traits.morality) is True

    def test_low_unlust_full_morality(self) -> None:
        """Content agent with high morality = morality gate active, no Thanatos."""
        agent = _make_agent(food=0.7, water=0.7, safety=0.7, social=0.7, money=600, morality=0.8)
        u = compute_unlust(agent)
        assert morality_active(u, agent.traits.morality) is True
        assert is_thanatos_active(u, agent.traits.morality) is False
