"""
Policy Effects Unit Tests
=========================

Tests for policy effect application on agents and world state,
and policy weight modification of utility scores.
"""

import pytest
from typing import Dict, List

from shared.types.aliases import AgentId
from shared.types.enums import ActionType, NeedType, WealthClass
from shared.schemas.agent_state import AgentState, AgentResources, AgentNeeds
from shared.schemas.simulation_state import SimulationState
from shared.schemas.policy import GovernmentPolicy, ImpactDelta, PolicyWeights
from simulation.policies.policy_effects import (
    apply_policy_effects,
    apply_policy_weights,
    apply_all_policies,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(
    agent_id: str = "test-agent",
    wealth_class: WealthClass = WealthClass.POOR,
    money: float = 100.0,
    wealth: float = 100.0,
    unlust: float = 0.0,
    is_alive: bool = True,
) -> AgentState:
    """Create a minimal AgentState for testing."""
    return AgentState(
        id=AgentId(agent_id),
        wealth_class=wealth_class,
        resources=AgentResources(money=money, wealth=wealth),
        unlust=unlust,
        is_alive=is_alive,
    )


def _make_policy(
    impact_deltas: Dict[WealthClass, ImpactDelta] | None = None,
) -> GovernmentPolicy:
    """Create a GovernmentPolicy with the given impact deltas."""
    return GovernmentPolicy(impact_deltas=impact_deltas or {})


# ===========================================================================
# apply_policy_effects — per-agent impact deltas
# ===========================================================================

class TestApplyPolicyEffects:
    """Tests for the apply_policy_effects function."""

    def test_money_delta(self):
        """poor agent, money_delta=-10 -> money decreases by 10."""
        agent = _make_agent(money=100.0, wealth=100.0)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(money_delta=-10.0)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.resources.money == 90.0

    def test_food_delta(self):
        """food_delta=0.05 -> food increases by 0.05."""
        agent = _make_agent()
        agent.needs.set_level(NeedType.FOOD, 0.5)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(food_delta=0.05)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.needs.get_level(NeedType.FOOD) == pytest.approx(0.55)

    def test_safety_delta(self):
        """safety_delta=-0.10 -> safety decreases."""
        agent = _make_agent()
        agent.needs.set_level(NeedType.SAFETY, 0.5)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(safety_delta=-0.10)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.needs.get_level(NeedType.SAFETY) == pytest.approx(0.40)

    def test_social_delta(self):
        """social_delta=0.03 -> social increases."""
        agent = _make_agent()
        agent.needs.set_level(NeedType.SOCIAL_CONNECTION, 0.5)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(social_delta=0.03)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.needs.get_level(NeedType.SOCIAL_CONNECTION) == pytest.approx(0.53)

    def test_anger_spike(self):
        """anger_spike=0.10 -> unlust increases by 0.10."""
        agent = _make_agent(unlust=0.0)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(anger_spike=0.10)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.unlust == pytest.approx(0.10)

    def test_no_delta_for_class(self):
        """rich agent, policy only has poor delta -> no change."""
        agent = _make_agent(wealth_class=WealthClass.RICH, money=100.0)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(money_delta=-10.0)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.resources.money == 100.0

    def test_wealth_mirrors_money_after_delta(self):
        """wealth == money after delta."""
        agent = _make_agent(money=50.0, wealth=100.0)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(money_delta=20.0)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.resources.money == 70.0
        assert agent.resources.wealth == 70.0

    def test_unlust_clamped(self):
        """anger_spike=0.5, unlust=0.8 -> unlust=1.0 (clamped)."""
        agent = _make_agent(unlust=0.8)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(anger_spike=0.5)})
        world = SimulationState()
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert agent.unlust == pytest.approx(1.0)


# ===========================================================================
# World-level changes (applied at most once per policy)
# ===========================================================================

class TestWorldChanges:
    """Tests for world-level policy effect application."""

    def test_world_change_tax(self):
        """new_tax_rate=0.25 -> world.tax_rate=0.25."""
        agent = _make_agent()
        policy = _make_policy({WealthClass.POOR: ImpactDelta(new_tax_rate=0.25)})
        world = SimulationState(tax_rate=0.15)
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert world.tax_rate == pytest.approx(0.25)

    def test_world_change_welfare(self):
        """welfare_on=True -> world.welfare_enabled=True."""
        agent = _make_agent()
        policy = _make_policy({WealthClass.POOR: ImpactDelta(welfare_on=True)})
        world = SimulationState(welfare_enabled=False)
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert world.welfare_enabled is True

    def test_world_change_food(self):
        """food_event=-0.20 -> world.food_availability decreases by 0.20."""
        agent = _make_agent()
        policy = _make_policy({WealthClass.POOR: ImpactDelta(food_event=-0.20)})
        world = SimulationState(food_availability=0.85)
        world_changed: dict[str, bool] = {}

        apply_policy_effects(agent, policy, world, world_changed)

        assert world.food_availability == pytest.approx(0.65)

    def test_world_change_applied_once(self):
        """10 agents, tax change applied only once."""
        world = SimulationState(tax_rate=0.15)
        policy = _make_policy({WealthClass.POOR: ImpactDelta(new_tax_rate=0.30)})
        world_changed: dict[str, bool] = {}

        agents = [_make_agent(f"agent-{i}") for i in range(10)]
        for agent in agents:
            apply_policy_effects(agent, policy, world, world_changed)

        # Tax only set once; agents' money all changed
        assert world.tax_rate == pytest.approx(0.30)
        # Each agent's money went from 100 -> 90 (money_delta is 0, only tax rate change)
        # Actually money_delta=0 so money stays 100, but let's verify
        for agent in agents:
            assert agent.resources.money == 100.0  # only tax rate changed, not money_delta


# ===========================================================================
# apply_policy_weights — utility score modification
# ===========================================================================

class TestApplyPolicyWeights:
    """Tests for the apply_policy_weights function."""

    def test_economic_freedom(self):
        """economic_freedom=0.5 -> WORK score boosted."""
        base = {
            ActionType.WORK: 1.0,
            ActionType.STEAL: 0.5,
        }
        weights = PolicyWeights(economic_freedom=0.5)

        result = apply_policy_weights(base, weights)

        assert result[ActionType.WORK] == pytest.approx(1.05)  # 1.0 + 0.5*0.1

    def test_social_welfare(self):
        """social_welfare=0.5 -> SHARE boosted, STEAL reduced."""
        base = {
            ActionType.SHARE: 0.5,
            ActionType.STEAL: 0.5,
            ActionType.CONSOLE: 0.5,
        }
        weights = PolicyWeights(social_welfare=0.5)

        result = apply_policy_weights(base, weights)

        assert result[ActionType.SHARE] == pytest.approx(0.575)  # 0.5 + 0.5*0.15
        assert result[ActionType.CONSOLE] == pytest.approx(0.55)  # 0.5 + 0.5*0.1
        assert result[ActionType.STEAL] == pytest.approx(0.45)  # 0.5 - 0.5*0.1

    def test_public_order(self):
        """public_order=0.5 -> PROTEST, STEAL, HARM_OTHER reduced."""
        base = {
            ActionType.PROTEST: 0.5,
            ActionType.STEAL: 0.5,
            ActionType.HARM_OTHER: 0.5,
        }
        weights = PolicyWeights(public_order=0.5)

        result = apply_policy_weights(base, weights)

        assert result[ActionType.PROTEST] == pytest.approx(0.45)  # 0.5 - 0.5*0.1
        assert result[ActionType.STEAL] == pytest.approx(0.425)  # 0.5 - 0.5*0.15
        assert result[ActionType.HARM_OTHER] == pytest.approx(0.40)  # 0.5 - 0.5*0.2

    def test_no_change(self):
        """all weights=0 -> scores unchanged."""
        base = {
            ActionType.WORK: 0.7,
            ActionType.STEAL: 0.3,
        }
        weights = PolicyWeights()

        result = apply_policy_weights(base, weights)

        assert result == base

    def test_returns_new_dict(self):
        """base_scores dict not modified."""
        base = {
            ActionType.WORK: 1.0,
            ActionType.STEAL: 0.5,
        }
        original = dict(base)
        weights = PolicyWeights(economic_freedom=0.5)

        result = apply_policy_weights(base, weights)

        assert base == original  # original unchanged
        assert result is not base  # different object


# ===========================================================================
# apply_all_policies — integration
# ===========================================================================

class TestApplyAllPolicies:
    """Tests for the apply_all_policies function."""

    def test_basic(self):
        """2 policies, 5 agents -> all agents get both policy effects."""
        world = SimulationState(tax_rate=0.15)
        policy_a = _make_policy({WealthClass.POOR: ImpactDelta(money_delta=-5.0)})
        policy_b = _make_policy({WealthClass.POOR: ImpactDelta(new_tax_rate=0.25)})
        agents = [_make_agent(f"agent-{i}", money=100.0) for i in range(5)]

        apply_all_policies(agents, [policy_a, policy_b], world)

        # Each agent should have money reduced by policy_a and have wealth mirrored
        for agent in agents:
            assert agent.resources.money == pytest.approx(95.0)
            assert agent.resources.wealth == pytest.approx(95.0)
        # Tax rate set (once)
        assert world.tax_rate == pytest.approx(0.25)

    def test_dead_skipped(self):
        """dead agents not affected."""
        world = SimulationState()
        policy = _make_policy({WealthClass.POOR: ImpactDelta(money_delta=-10.0)})
        alive = _make_agent("alive", money=100.0, is_alive=True)
        dead = _make_agent("dead", money=100.0, is_alive=False)

        apply_all_policies([dead, alive], [policy], world)

        assert alive.resources.money == pytest.approx(90.0)
        assert dead.resources.money == pytest.approx(100.0)  # unchanged

    def test_empty(self):
        """no policies -> no changes."""
        world = SimulationState(tax_rate=0.15)
        agent = _make_agent(money=100.0)
        agent.needs.set_level(NeedType.FOOD, 0.5)

        apply_all_policies([agent], [], world)

        assert agent.resources.money == 100.0
        assert agent.needs.get_level(NeedType.FOOD) == pytest.approx(0.5)
        assert world.tax_rate == 0.15
