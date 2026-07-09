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
    """unlust=0.65, morality=0.7 -> True (partial, high morality)."""
    assert morality_active(0.65, 0.7) is True


def test_morality_inactive_medium_low_morality() -> None:
    """unlust=0.65, morality=0.4 -> False (partial, low morality)."""
    assert morality_active(0.65, 0.4) is False


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
    """unlust=0.7, morality=0.8 -> False (morality active blocks Thanatos)."""
    assert is_thanatos_active(0.7, 0.8) is False


# --- get_unlust_state tests ----------------------------------------------


def test_unlust_state_content() -> None:
    """unlust=0.15 -> 'content'."""
    assert get_unlust_state(0.15) == "content"


def test_unlust_state_stressed() -> None:
    """unlust=0.40 -> 'stressed'."""
    assert get_unlust_state(0.40) == "stressed"


def test_unlust_state_driven() -> None:
    """unlust=0.70 -> 'driven'."""
    assert get_unlust_state(0.70) == "driven"


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
