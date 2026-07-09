"""Tests for the economy system (rent, welfare, money flow)."""

import pytest

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.aliases import AgentId
from shared.types.enums import WealthClass

from simulation.world.economy import apply_rent, apply_welfare, process_economy_tick


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(
    wealth_class: WealthClass = WealthClass.POOR,
    money: float = 100.0,
    property: bool = False,
    employed: bool = False,
    is_alive: bool = True,
) -> AgentState:
    """Create an AgentState with the given resource configuration."""
    agent = AgentState(id=AgentId("test-agent"))
    agent.wealth_class = wealth_class
    agent.resources.money = money
    agent.resources.wealth = money
    agent.resources.property = property
    agent.resources.employed = employed
    agent.is_alive = is_alive
    return agent


def _make_world(
    welfare_enabled: bool = False,
    welfare_amount: float = 8.0,
) -> SimulationState:
    """Create a SimulationState with the given welfare config."""
    world = SimulationState()
    world.welfare_enabled = welfare_enabled
    world.welfare_amount = welfare_amount
    return world


# ===================================================================
# apply_rent
# ===================================================================


class TestApplyRent:
    """Tests for apply_rent()."""

    def test_apply_rent_property_owner(self) -> None:
        """Owning property means zero rent."""
        agent = _make_agent(property=True)
        assert apply_rent(agent) == 0.0

    def test_apply_rent_poor(self) -> None:
        """Poor, no property → pays 2.0."""
        agent = _make_agent(wealth_class=WealthClass.POOR, property=False)
        assert apply_rent(agent) == 2.0

    def test_apply_rent_middle(self) -> None:
        """Middle, no property → pays 15.0."""
        agent = _make_agent(wealth_class=WealthClass.MIDDLE, property=False)
        assert apply_rent(agent) == 15.0

    def test_apply_rent_rich(self) -> None:
        """Rich, no property → pays 50.0."""
        agent = _make_agent(wealth_class=WealthClass.RICH, property=False)
        assert apply_rent(agent) == 50.0

    def test_apply_rent_money_clamped(self) -> None:
        """Money goes to 0, not negative, when rent exceeds cash."""
        agent = _make_agent(money=1.0, wealth_class=WealthClass.MIDDLE, property=False)
        apply_rent(agent)
        assert agent.resources.money == 0.0

    def test_apply_rent_wealth_mirrors(self) -> None:
        """wealth is kept in sync with money after rent."""
        agent = _make_agent(money=50.0, wealth_class=WealthClass.MIDDLE, property=False)
        apply_rent(agent)
        assert agent.resources.wealth == agent.resources.money


# ===================================================================
# apply_welfare
# ===================================================================


class TestApplyWelfare:
    """Tests for apply_welfare()."""

    def test_apply_welfare_disabled(self) -> None:
        """Welfare disabled → 0."""
        agent = _make_agent(employed=False)
        world = _make_world(welfare_enabled=False)
        assert apply_welfare(agent, world) == 0.0

    def test_apply_welfare_employed(self) -> None:
        """Employed agent → 0."""
        agent = _make_agent(employed=True)
        world = _make_world(welfare_enabled=True)
        assert apply_welfare(agent, world) == 0.0

    def test_apply_welfare_eligible(self) -> None:
        """Unemployed, welfare enabled → receives default 8.0."""
        agent = _make_agent(employed=False, money=0.0)
        world = _make_world(welfare_enabled=True)
        assert apply_welfare(agent, world) == 8.0

    def test_apply_welfare_custom_amount(self) -> None:
        """Custom welfare_amount is respected."""
        agent = _make_agent(employed=False, money=0.0)
        world = _make_world(welfare_enabled=True, welfare_amount=20.0)
        assert apply_welfare(agent, world) == 20.0

    def test_apply_welfare_wealth_mirrors(self) -> None:
        """wealth is kept in sync with money after welfare."""
        agent = _make_agent(employed=False, money=10.0)
        world = _make_world(welfare_enabled=True, welfare_amount=5.0)
        apply_welfare(agent, world)
        assert agent.resources.wealth == agent.resources.money


# ===================================================================
# process_economy_tick
# ===================================================================


class TestProcessEconomyTick:
    """Tests for process_economy_tick()."""

    def test_process_economy_tick_mixed(self) -> None:
        """Mixed scenario: renters pay, unemployed get welfare."""
        agents = [
            _make_agent(wealth_class=WealthClass.POOR, property=False, employed=False),
            _make_agent(wealth_class=WealthClass.MIDDLE, property=False, employed=True),
            _make_agent(wealth_class=WealthClass.RICH, property=True, employed=True),
        ]
        world = _make_world(welfare_enabled=True)
        result = process_economy_tick(agents, world)

        # Agent 0 (poor, renter, unemployed): pays 2 rent, gets 8 welfare
        # Agent 1 (middle, renter, employed): pays 15 rent, no welfare
        # Agent 2 (rich, owner, employed): no rent, no welfare
        assert result["total_rent"] == 17.0
        assert result["total_welfare"] == 8.0
        assert result["rent_payers"] == 2.0
        assert result["welfare_recipients"] == 1.0

    def test_process_economy_tick_all_property(self) -> None:
        """All own property → total_rent = 0."""
        agents = [
            _make_agent(property=True, employed=False),
            _make_agent(property=True, employed=True),
        ]
        world = _make_world(welfare_enabled=True)
        result = process_economy_tick(agents, world)
        assert result["total_rent"] == 0.0

    def test_process_economy_tick_no_welfare(self) -> None:
        """Welfare disabled → total_welfare = 0."""
        agents = [
            _make_agent(property=False, employed=False),
            _make_agent(property=False, employed=True),
        ]
        world = _make_world(welfare_enabled=False)
        result = process_economy_tick(agents, world)
        assert result["total_welfare"] == 0.0

    def test_process_economy_tick_dead_skipped(self) -> None:
        """Dead agents are skipped."""
        agents = [
            _make_agent(property=False, employed=False, is_alive=False),
            _make_agent(wealth_class=WealthClass.MIDDLE, property=False, employed=True),
        ]
        world = _make_world(welfare_enabled=True)
        result = process_economy_tick(agents, world)

        # Only agent 1 is alive: pays 15 rent, employed so no welfare
        assert result["total_rent"] == 15.0
        assert result["total_welfare"] == 0.0
        assert result["rent_payers"] == 1.0
        assert result["welfare_recipients"] == 0.0

    def test_process_economy_tick_returns_dict(self) -> None:
        """Returns dict with all 4 keys."""
        agents = [_make_agent()]
        world = _make_world()
        result = process_economy_tick(agents, world)
        assert set(result.keys()) == {
            "total_rent",
            "total_welfare",
            "rent_payers",
            "welfare_recipients",
        }
