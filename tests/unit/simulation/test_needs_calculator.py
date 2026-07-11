"""
Tests for needs_calculator.py
==============================

Comprehensive test suite covering decay formulas, death conditions,
wealth class derivation, and determinism guarantees.
"""

from copy import deepcopy
from unittest.mock import patch

import pytest

from shared.constants.defaults import (
    DESPAIR_MORTALITY_RATE,
    FAMILY_DECAY_RATE,
    FOOD_DEATH_THRESHOLD,
    FOOD_DECAY_RATE,
    HEALTH_DEATH_THRESHOLD,
    JOB_LOSS_RATE,
    REPUTATION_DECAY_RATE,
    ROMANTIC_DECAY_RATE,
    SAFETY_DECAY_RATE,
    SCARCITY_BASE,
    SELF_ESTEEM_DECAY_RATE,
    SEXUAL_TENSION_GROWTH_RATE,
    SLEEP_DECAY_RATE,
    SLEEP_REPLENISH_RATE,
    SOCIAL_DECAY_RATE,
    UNLUST_FINANCIAL_DIVISOR,
    WATER_DEATH_THRESHOLD,
    WATER_DECAY_RATE,
)
from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
)
from shared.schemas.simulation_state import SimulationState
from shared.types.aliases import AgentId
from shared.types.enums import EmotionType, EmploymentStatus, NeedType, WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.needs_calculator import check_death, decay_needs, derive_wealth_class, maybe_lose_job


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(
    *,
    extraversion: float = 0.5,
    money: float = 100.0,
    health: float = 1.0,
    property: bool = False,
    is_alive: bool = True,
    primary_emotion: EmotionType = EmotionType.NORMAL,
) -> AgentState:
    """Create a minimal AgentState with sensible defaults for testing."""
    traits = AgentTraits(extraversion=extraversion)
    needs = AgentNeeds()
    resources = AgentResources(money=money, health=health, property=property)
    emotions = AgentEmotions(primary=primary_emotion)
    return AgentState(
        id=AgentId("test-agent"),
        traits=traits,
        needs=needs,
        resources=resources,
        emotions=emotions,
        is_alive=is_alive,
    )


def _make_world(
    *,
    food_availability: float = 0.85,
    crime_rate: float = 0.05,
) -> SimulationState:
    """Create a minimal SimulationState for testing."""
    return SimulationState(
        food_availability=food_availability,
        crime_rate=crime_rate,
    )


def _set_need(agent: AgentState, need_type: NeedType, value: float) -> None:
    """Convenience wrapper to set a need level."""
    agent.needs.set_level(need_type, value)


# ---------------------------------------------------------------------------
# Need decay tests
# ---------------------------------------------------------------------------

class TestDecayNeeds:
    """Deterministic decay of all 13 needs per tick."""

    def test_decay_food(self) -> None:
        """Food decays by FOOD_DECAY_RATE * scarcity each tick."""
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.8)
        # scarcity = SCARCITY_BASE - 1.0 = 1.0
        world = _make_world(food_availability=1.0)

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.8 - FOOD_DECAY_RATE * 1.0
        assert agent.needs.get_level(NeedType.FOOD) == pytest.approx(expected)

    def test_decay_water(self) -> None:
        """Water decays by WATER_DECAY_RATE * scarcity each tick."""
        agent = _make_agent()
        _set_need(agent, NeedType.WATER, 0.9)
        world = _make_world(food_availability=1.0)

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.9 - WATER_DECAY_RATE * 1.0
        assert agent.needs.get_level(NeedType.WATER) == pytest.approx(expected)

    def test_decay_sleep_auto_replenish(self) -> None:
        """Sleep decays by SLEEP_DECAY_RATE but replenishes by SLEEP_RECOVERY_NATURAL."""
        from shared.constants.defaults import SLEEP_RECOVERY_NATURAL
        agent = _make_agent()
        _set_need(agent, NeedType.SLEEP, 0.6)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.6 - SLEEP_DECAY_RATE + SLEEP_RECOVERY_NATURAL
        assert agent.needs.get_level(NeedType.SLEEP) == pytest.approx(expected)

    def test_sexual_tension_builds(self) -> None:
        """Sexual tension INCREASES by SEXUAL_TENSION_GROWTH_RATE each tick."""
        agent = _make_agent()
        _set_need(agent, NeedType.SEXUAL_TENSION, 0.3)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.3 + SEXUAL_TENSION_GROWTH_RATE
        assert agent.needs.get_level(NeedType.SEXUAL_TENSION) == pytest.approx(expected)

    def test_safety_decay_with_crime(self) -> None:
        """Safety decays by SAFETY_DECAY_RATE + crime_rate*0.01."""
        agent = _make_agent()
        _set_need(agent, NeedType.SAFETY, 0.8)
        world = _make_world(crime_rate=0.1)

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.8 - SAFETY_DECAY_RATE - 0.1 * 0.01
        assert agent.needs.get_level(NeedType.SAFETY) == pytest.approx(expected)

    def test_financial_security_derived(self) -> None:
        """Financial security is set to min(1.0, money/UNLUST_FINANCIAL_DIVISOR)."""
        agent = _make_agent(money=300.0)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        expected = min(1.0, 300.0 / UNLUST_FINANCIAL_DIVISOR)
        assert agent.needs.get_level(NeedType.FINANCIAL_SECURITY) == pytest.approx(expected)

    def test_financial_security_capped(self) -> None:
        """Financial security caps at 1.0 for large money values."""
        agent = _make_agent(money=10_000.0)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.needs.get_level(NeedType.FINANCIAL_SECURITY) == pytest.approx(1.0)

    def test_shelter_from_property(self) -> None:
        """Shelter is 1.0 if agent owns property."""
        agent = _make_agent(property=True)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.needs.get_level(NeedType.SHELTER) == pytest.approx(1.0)

    def test_shelter_no_property(self) -> None:
        """Shelter is 0.3 if agent does not own property."""
        agent = _make_agent(property=False)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.needs.get_level(NeedType.SHELTER) == pytest.approx(0.3)

    def test_social_decay_extravert(self) -> None:
        """Extravert social connection decays at 1.2x base rate."""
        agent = _make_agent(extraversion=0.7)  # > 0.5
        _set_need(agent, NeedType.SOCIAL_CONNECTION, 0.9)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.9 - SOCIAL_DECAY_RATE * 1.2
        assert agent.needs.get_level(NeedType.SOCIAL_CONNECTION) == pytest.approx(expected)

    def test_social_decay_introvert(self) -> None:
        """Introvert social connection decays at 0.8x base rate."""
        agent = _make_agent(extraversion=0.3)  # <= 0.5
        _set_need(agent, NeedType.SOCIAL_CONNECTION, 0.9)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        expected = 0.9 - SOCIAL_DECAY_RATE * 0.8
        assert agent.needs.get_level(NeedType.SOCIAL_CONNECTION) == pytest.approx(expected)

    def test_family_and_romantic_decay(self) -> None:
        """Family bond and romantic bond decay by their respective rates."""
        agent = _make_agent()
        _set_need(agent, NeedType.FAMILY_BOND, 0.7)
        _set_need(agent, NeedType.ROMANTIC_BOND, 0.7)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.needs.get_level(NeedType.FAMILY_BOND) == pytest.approx(0.7 - FAMILY_DECAY_RATE)
        assert agent.needs.get_level(NeedType.ROMANTIC_BOND) == pytest.approx(0.7 - ROMANTIC_DECAY_RATE)

    def test_self_esteem_and_reputation_decay(self) -> None:
        """Self-esteem and reputation decay by their respective rates."""
        agent = _make_agent()
        _set_need(agent, NeedType.SELF_ESTEEM, 0.8)
        _set_need(agent, NeedType.REPUTATION, 0.8)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.needs.get_level(NeedType.SELF_ESTEEM) == pytest.approx(0.8 - SELF_ESTEEM_DECAY_RATE)
        assert agent.needs.get_level(NeedType.REPUTATION) == pytest.approx(0.8 - REPUTATION_DECAY_RATE)

    def test_inferiority_gap_not_touched(self) -> None:
        """INFERIORITY_GAP is not modified by passive decay."""
        agent = _make_agent()
        # Setting it to a non-default value
        _set_need(agent, NeedType.INFERIORITY_GAP, 0.5)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        # Should remain unchanged
        assert agent.needs.get_level(NeedType.INFERIORITY_GAP) == pytest.approx(0.5)

    # ------------------------------------------------------------------
    # Wealth class & wealth field
    # ------------------------------------------------------------------

    def test_wealth_class_derivation(self) -> None:
        """derive_wealth_class returns POOR for <500, MIDDLE for <5000, RICH otherwise."""
        assert derive_wealth_class(0.0) == WealthClass.POOR
        assert derive_wealth_class(499.99) == WealthClass.POOR
        assert derive_wealth_class(500.0) == WealthClass.MIDDLE
        assert derive_wealth_class(4999.99) == WealthClass.MIDDLE
        assert derive_wealth_class(5000.0) == WealthClass.RICH
        assert derive_wealth_class(1_000_000.0) == WealthClass.RICH

    def test_wealth_class_updated_on_decay(self) -> None:
        """After decay_needs, agent.wealth_class reflects the current money."""
        agent = _make_agent(money=500.0)
        assert agent.wealth_class == WealthClass.POOR  # default

        agent.resources.money = 2000.0
        world = _make_world()
        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.wealth_class == WealthClass.MIDDLE

    def test_wealth_mirrors_money(self) -> None:
        """After decay_needs, resources.wealth == resources.money."""
        agent = _make_agent(money=7500.0)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.resources.wealth == pytest.approx(agent.resources.money)

    # ------------------------------------------------------------------
    # Scarcity
    # ------------------------------------------------------------------

    def test_scarcity_multiplier(self) -> None:
        """Lower food_availability increases scarcity, accelerating food decay."""
        agent1 = _make_agent()
        _set_need(agent1, NeedType.FOOD, 0.8)
        agent2 = _make_agent()
        _set_need(agent2, NeedType.FOOD, 0.8)

        world_scarce = _make_world(food_availability=0.5)   # scarcity = 1.5
        world_plenty = _make_world(food_availability=1.0)    # scarcity = 1.0

        rng = DeterministicRNG(42)
        decay_needs(agent1, world_scarce, rng)
        rng2 = DeterministicRNG(42)
        decay_needs(agent2, world_plenty, rng2)

        # Agent in scarce world should have less food
        assert agent1.needs.get_level(NeedType.FOOD) < agent2.needs.get_level(NeedType.FOOD)

        # Verify the exact math: food1 = 0.8 - 0.018*1.5 = 0.773, food2 = 0.8 - 0.018*1.0 = 0.782
        expected_scarce = 0.8 - FOOD_DECAY_RATE * (SCARCITY_BASE - 0.5)
        expected_plenty = 0.8 - FOOD_DECAY_RATE * (SCARCITY_BASE - 1.0)
        assert agent1.needs.get_level(NeedType.FOOD) == pytest.approx(expected_scarce)
        assert agent2.needs.get_level(NeedType.FOOD) == pytest.approx(expected_plenty)

    # ------------------------------------------------------------------
    # Clamping
    # ------------------------------------------------------------------

    def test_needs_clamped(self) -> None:
        """After many ticks of decay, needs don't go below 0 (set_level clamps)."""
        agent = _make_agent()
        # Set food very low
        _set_need(agent, NeedType.FOOD, 0.01)
        world = _make_world(food_availability=0.0)  # max scarcity = 2.0
        rng = DeterministicRNG(42)

        # Run many ticks
        for _ in range(20):
            decay_needs(agent, world, rng)

        # Should be clamped to 0.0
        assert agent.needs.get_level(NeedType.FOOD) == pytest.approx(0.0)
        # Other needs should also be >= 0
        for need in NeedType:
            assert agent.needs.get_level(need) >= 0.0


# ---------------------------------------------------------------------------
# Death condition tests
# ---------------------------------------------------------------------------

class TestCheckDeath:
    """Death conditions: starvation, dehydration, health failure, despair."""

    def test_death_starvation(self) -> None:
        """Food <= FOOD_DEATH_THRESHOLD triggers death."""
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, FOOD_DEATH_THRESHOLD)
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is True

    def test_death_starvation_below_threshold(self) -> None:
        """Food below threshold triggers death."""
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, FOOD_DEATH_THRESHOLD - 0.01)
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is True

    def test_death_dehydration(self) -> None:
        """Water <= WATER_DEATH_THRESHOLD triggers death."""
        agent = _make_agent()
        _set_need(agent, NeedType.WATER, WATER_DEATH_THRESHOLD)
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is True

    def test_death_health(self) -> None:
        """Health <= HEALTH_DEATH_THRESHOLD triggers death with 50% probability."""
        agent = _make_agent(health=HEALTH_DEATH_THRESHOLD)

        class _AlwaysDieRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0

        assert check_death(agent, _AlwaysDieRNG()) is True

    def test_death_starvation_takes_precedence(self) -> None:
        """Starvation death is detected even if other conditions also hold."""
        agent = _make_agent(health=HEALTH_DEATH_THRESHOLD)
        _set_need(agent, NeedType.FOOD, FOOD_DEATH_THRESHOLD)
        _set_need(agent, NeedType.WATER, WATER_DEATH_THRESHOLD)
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is True

    def test_death_despair_mortality(self) -> None:
        """Despair emotion + lucky RNG roll (< DESPAIR_MORTALITY_RATE) causes death."""
        class _ControlledRNG(DeterministicRNG):
            """RNG that always returns a fixed value."""

            def __init__(self, return_value: float) -> None:
                super().__init__(0)
                self._return_value = return_value

            def random(self) -> float:
                return self._return_value

        agent = _make_agent(primary_emotion=EmotionType.DESPAIR)
        # Ensure no starvation/dehydration/health death
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)

        assert check_death(agent, _ControlledRNG(0.0)) is True

    def test_death_despair_survival(self) -> None:
        """Despair emotion + high RNG roll (>= DESPAIR_MORTALITY_RATE) survives."""
        class _ControlledRNG(DeterministicRNG):
            """RNG that always returns a fixed value."""

            def __init__(self, return_value: float) -> None:
                super().__init__(0)
                self._return_value = return_value

            def random(self) -> float:
                return self._return_value

        agent = _make_agent(primary_emotion=EmotionType.DESPAIR)
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)

        assert check_death(agent, _ControlledRNG(1.0)) is False

    def test_dead_agent_stays_dead(self) -> None:
        """An already dead agent (is_alive=False) is never flagged for death."""
        agent = _make_agent(is_alive=False)
        _set_need(agent, NeedType.FOOD, 0.0)  # would kill if alive
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is False

    def test_no_death_normal_agent(self) -> None:
        """A healthy agent with full needs does not die."""
        agent = _make_agent(money=5000.0, health=1.0)
        _set_need(agent, NeedType.FOOD, 0.8)
        _set_need(agent, NeedType.WATER, 0.8)
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is False


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Same seed + same config = identical results."""

    def test_determinism_single_tick(self) -> None:
        """Same seed produces identical need levels after one tick."""
        def run() -> float:
            agent = _make_agent()
            _set_need(agent, NeedType.FOOD, 0.8)
            _set_need(agent, NeedType.WATER, 0.8)
            world = _make_world(food_availability=0.7)
            decay_needs(agent, world, DeterministicRNG(42))
            return agent.needs.get_level(NeedType.FOOD)

        assert run() == run()

    def test_determinism_multiple_ticks(self) -> None:
        """Same seed produces identical need levels after 10 ticks."""
        def run_10_ticks() -> dict[str, object]:
            agent = _make_agent(extraversion=0.6, money=500.0)
            _set_need(agent, NeedType.FOOD, 0.9)
            _set_need(agent, NeedType.WATER, 0.9)
            _set_need(agent, NeedType.SLEEP, 0.7)
            _set_need(agent, NeedType.SEXUAL_TENSION, 0.3)
            _set_need(agent, NeedType.SAFETY, 0.8)
            _set_need(agent, NeedType.SOCIAL_CONNECTION, 0.7)
            _set_need(agent, NeedType.FAMILY_BOND, 0.6)
            _set_need(agent, NeedType.ROMANTIC_BOND, 0.5)
            _set_need(agent, NeedType.SELF_ESTEEM, 0.7)
            _set_need(agent, NeedType.REPUTATION, 0.6)

            world = _make_world(food_availability=0.75, crime_rate=0.08)
            rng = DeterministicRNG(42)

            for _ in range(10):
                decay_needs(agent, world, rng)

            return {
                "food": agent.needs.get_level(NeedType.FOOD),
                "water": agent.needs.get_level(NeedType.WATER),
                "sleep": agent.needs.get_level(NeedType.SLEEP),
                "sexual_tension": agent.needs.get_level(NeedType.SEXUAL_TENSION),
                "safety": agent.needs.get_level(NeedType.SAFETY),
                "financial_security": agent.needs.get_level(NeedType.FINANCIAL_SECURITY),
                "shelter": agent.needs.get_level(NeedType.SHELTER),
                "social": agent.needs.get_level(NeedType.SOCIAL_CONNECTION),
                "family": agent.needs.get_level(NeedType.FAMILY_BOND),
                "romantic": agent.needs.get_level(NeedType.ROMANTIC_BOND),
                "self_esteem": agent.needs.get_level(NeedType.SELF_ESTEEM),
                "reputation": agent.needs.get_level(NeedType.REPUTATION),
                "wealth_class": str(agent.wealth_class),
            }

        assert run_10_ticks() == run_10_ticks()

    def test_different_seeds_different_results(self) -> None:
        """Different RNG values produce both death and survival for despair agents."""
        class _ControlledRNG(DeterministicRNG):
            """RNG that always returns a fixed value."""

            def __init__(self, return_value: float) -> None:
                super().__init__(0)
                self._return_value = return_value

            def random(self) -> float:
                return self._return_value

        agent_dead = _make_agent(primary_emotion=EmotionType.DESPAIR)
        _set_need(agent_dead, NeedType.FOOD, 0.5)
        _set_need(agent_dead, NeedType.WATER, 0.5)
        assert check_death(agent_dead, _ControlledRNG(0.0)) is True

        agent_alive = _make_agent(primary_emotion=EmotionType.DESPAIR)
        _set_need(agent_alive, NeedType.FOOD, 0.5)
        _set_need(agent_alive, NeedType.WATER, 0.5)
        assert check_death(agent_alive, _ControlledRNG(0.5)) is False


# ---------------------------------------------------------------------------
# derive_wealth_class standalone tests
# ---------------------------------------------------------------------------

class TestDeriveWealthClass:
    """Pure function tests for derive_wealth_class."""

    def test_poor(self) -> None:
        assert derive_wealth_class(0.0) == WealthClass.POOR
        assert derive_wealth_class(499.99) == WealthClass.POOR

    def test_middle_at_boundary(self) -> None:
        assert derive_wealth_class(500.0) == WealthClass.MIDDLE

    def test_middle(self) -> None:
        assert derive_wealth_class(2500.0) == WealthClass.MIDDLE
        assert derive_wealth_class(4999.99) == WealthClass.MIDDLE

    def test_rich_at_boundary(self) -> None:
        assert derive_wealth_class(5000.0) == WealthClass.RICH

    def test_rich(self) -> None:
        assert derive_wealth_class(1_000_000.0) == WealthClass.RICH


# ---------------------------------------------------------------------------
# Edge-case / integration tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and integration-level invariants."""

    def test_all_needs_decayed(self) -> None:
        """Every passive-decay need is modified after a call to decay_needs.

        INFERIORITY_GAP is excluded because it is computed on social interaction,
        not passively decayed.
        """
        agent = _make_agent(extraversion=0.5, money=1000.0, property=True)
        world = _make_world()
        decay_needs(agent, world, DeterministicRNG(42))

        passive_needs = [
            NeedType.FOOD,
            NeedType.WATER,
            NeedType.SLEEP,
            NeedType.SEXUAL_TENSION,
            NeedType.SAFETY,
            NeedType.FINANCIAL_SECURITY,
            NeedType.SHELTER,
            NeedType.SOCIAL_CONNECTION,
            NeedType.FAMILY_BOND,
            NeedType.ROMANTIC_BOND,
            NeedType.SELF_ESTEEM,
            NeedType.REPUTATION,
        ]
        for need in passive_needs:
            assert need in agent.needs.levels, f"{need} was not set by decay_needs"

    def test_no_side_effects_on_immutable_fields(self) -> None:
        """Fields not touched by decay_needs remain unchanged."""
        agent = _make_agent()
        original_id = agent.id
        original_age = agent.age
        original_location = agent.location
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.id == original_id
        assert agent.age == original_age
        assert agent.location == original_location

    def test_health_not_modified_by_decay(self) -> None:
        """decay_needs applies passive health decay."""
        agent = _make_agent(health=0.75)
        world = _make_world()

        decay_needs(agent, world, DeterministicRNG(42))

        assert agent.resources.health == pytest.approx(0.749)


# ---------------------------------------------------------------------------
# Job loss tests
# ---------------------------------------------------------------------------

class TestMaybeLoseJob:
    """Probabilistic job loss mechanic tests."""

    def test_job_loss_doesnt_affect_unemployed(self) -> None:
        """Unemployed agent returns False and fields remain unchanged."""
        agent = _make_agent()
        # Default: employed=False, employment_status=UNEMPLOYED
        assert not agent.resources.employed
        original_status = agent.employment_status
        original_salary = agent.resources.base_salary

        rng = DeterministicRNG(42)
        result = maybe_lose_job(agent, rng)

        assert result is False
        assert agent.resources.employed is False
        assert agent.employment_status == original_status
        assert agent.resources.base_salary == original_salary

    def test_job_loss_rate_zero(self) -> None:
        """With JOB_LOSS_RATE=0, employed agent never loses job."""
        agent = _make_agent()
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.resources.base_salary = 30000.0

        # Controlled RNG that would trigger if rate were > 0
        class _ControlledRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0

        with patch("simulation.agents.needs_calculator.JOB_LOSS_RATE", 0.0):
            result = maybe_lose_job(agent, _ControlledRNG())

        assert result is False
        assert agent.resources.employed is True
        assert agent.resources.base_salary == 30000.0

    def test_job_loss_occurs(self) -> None:
        """Employed agent with favorable RNG roll loses job."""
        agent = _make_agent()
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.resources.base_salary = 30000.0

        class _ControlledRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0  # Always < JOB_LOSS_RATE (0.002)

        result = maybe_lose_job(agent, _ControlledRNG())

        assert result is True

    def test_job_loss_occurs_boundary(self) -> None:
        """RNG roll exactly at JOB_LOSS_RATE does NOT trigger job loss (strict <)."""
        agent = _make_agent()
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.resources.base_salary = 30000.0

        class _ControlledRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return JOB_LOSS_RATE  # Equal to rate, not less than

        result = maybe_lose_job(agent, _ControlledRNG())

        assert result is False
        assert agent.resources.employed is True

    def test_job_loss_sets_fields(self) -> None:
        """On job loss, employed=False, employment_status=UNEMPLOYED, base_salary=0.0."""
        agent = _make_agent()
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.resources.base_salary = 30000.0

        class _ControlledRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0

        maybe_lose_job(agent, _ControlledRNG())

        assert agent.resources.employed is False
        assert agent.employment_status == EmploymentStatus.UNEMPLOYED
        assert agent.resources.base_salary == pytest.approx(0.0)

    def test_job_loss_deterministic(self) -> None:
        """Same seed produces same job loss outcome."""
        def run() -> bool:
            agent = _make_agent()
            agent.resources.employed = True
            agent.employment_status = EmploymentStatus.EMPLOYED
            agent.resources.base_salary = 30000.0
            rng = DeterministicRNG(seed=42)
            return maybe_lose_job(agent, rng)

        assert run() == run()

    def test_job_loss_with_world_economic_pressure(self) -> None:
        """Higher unemployment + weaker economy increases job loss probability."""
        agent = _make_agent()
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.resources.base_salary = 30000.0

        class _ControlledRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return JOB_LOSS_RATE * 1.001  # Slightly above base rate

        # With poor economic health, effective rate increases and triggers loss
        world = _make_world()
        world.economic_health = 0.1  # Very weak economy

        result = maybe_lose_job(agent, _ControlledRNG(), world)

        assert result is True

    def test_job_loss_with_world_no_effect_healthy(self) -> None:
        """With strong economy, economic_pressure ~ 0, effective rate = base."""
        agent = _make_agent()
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        agent.resources.base_salary = 30000.0

        class _ControlledRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return JOB_LOSS_RATE * 0.999  # Just below base

        world = _make_world()
        world.economic_health = 1.0  # Very strong economy → no pressure

        result = maybe_lose_job(agent, _ControlledRNG(), world)

        assert result is True  # Still above effective rate


# ===========================================================================
# Progress age tests
# ===========================================================================

class TestProgressAge:
    """Tests for progress_age."""

    def test_age_increments(self) -> None:
        """Age advances by AGE_PROGRESSION_INTERVAL each tick."""
        from shared.constants.defaults import AGE_PROGRESSION_INTERVAL
        from simulation.agents.needs_calculator import progress_age
        agent = _make_agent()
        original_age = agent.age
        progress_age(agent)
        assert agent.age == pytest.approx(original_age + AGE_PROGRESSION_INTERVAL)

    def test_age_bracket_updated(self) -> None:
        """Age bracket is recalculated after progress_age."""
        from simulation.agents.needs_calculator import progress_age
        from shared.schemas.agent_state import get_age_bracket
        agent = _make_agent()
        # Set age to just below a bracket boundary
        agent.age = 59  # Just below 60 (becomes elderly at 60)
        agent.age_bracket = "middle_adult"
        progress_age(agent)
        assert agent.age_bracket == get_age_bracket(agent.age)

    def test_young_adult_progression(self) -> None:
        """A young adult progresses correctly."""
        from simulation.agents.needs_calculator import progress_age
        from shared.constants.defaults import AGE_PROGRESSION_INTERVAL, AGE_YOUNG_ADULT_MAX
        agent = _make_agent()
        agent.age = AGE_YOUNG_ADULT_MAX - 1  # Just below young adult max
        progress_age(agent)
        assert agent.age_bracket in ("young_adult", "middle_adult")


# ===========================================================================
# Update insomnia tests
# ===========================================================================

class TestUpdateInsomnia:
    """Tests for update_insomnia."""

    def test_insomnia_ticks_increment_low_sleep(self) -> None:
        """ticks_without_sleep increments when sleep < 0.3."""
        from simulation.agents.needs_calculator import update_insomnia
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.2)
        original_ticks = agent.ticks_without_sleep
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.ticks_without_sleep == original_ticks + 1

    def test_insomnia_ticks_reset_high_sleep(self) -> None:
        """ticks_without_sleep resets to 0 when sleep > 0.5."""
        from simulation.agents.needs_calculator import update_insomnia
        agent = _make_agent()
        agent.ticks_without_sleep = 10
        agent.needs.set_level(NeedType.SLEEP, 0.7)
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.ticks_without_sleep == 0

    def test_insomnia_increases_low_sleep(self) -> None:
        """insomnia severity increases when sleep < 0.3."""
        from simulation.agents.needs_calculator import update_insomnia
        from shared.constants.defaults import INSOMNIA_INCREASE_RATE
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.2)
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.insomnia_severity == pytest.approx(INSOMNIA_INCREASE_RATE)

    def test_insomnia_increases_stress_safety(self) -> None:
        """Insomnia increases when unlust high + safety low."""
        from simulation.agents.needs_calculator import update_insomnia
        from shared.constants.defaults import INSOMNIA_INCREASE_RATE
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.5)  # Not low
        agent.needs.set_level(NeedType.SAFETY, 0.2)  # Very low
        agent.unlust = 0.8  # Very high
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.insomnia_severity == pytest.approx(INSOMNIA_INCREASE_RATE)

    def test_insomnia_decreases_normally(self) -> None:
        """Insomnia severity decreases when conditions are good."""
        from simulation.agents.needs_calculator import update_insomnia
        from shared.constants.defaults import INSOMNIA_DECAY_RATE
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.5)  # Adequate
        agent.needs.set_level(NeedType.SAFETY, 0.5)
        agent.unlust = 0.3
        agent.insomnia_severity = 0.5
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.insomnia_severity == pytest.approx(0.5 - INSOMNIA_DECAY_RATE)

    def test_insomnia_clamped_to_max(self) -> None:
        """Insomnia severity cannot exceed INSOMNIA_MAX."""
        from simulation.agents.needs_calculator import update_insomnia
        from shared.constants.defaults import INSOMNIA_MAX, INSOMNIA_INCREASE_RATE
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.0)
        agent.insomnia_severity = 0.99
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.insomnia_severity <= INSOMNIA_MAX

    def test_sleep_deprivation_feedback_partial(self) -> None:
        """Insomnia > 0.5 adds 0.01 to unlust."""
        from simulation.agents.needs_calculator import update_insomnia
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.5)
        agent.needs.set_level(NeedType.SAFETY, 0.5)
        agent.unlust = 0.5
        agent.insomnia_severity = 0.6  # > 0.5
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.unlust == pytest.approx(0.51)

    def test_sleep_deprivation_feedback_severe(self) -> None:
        """Insomnia > 0.7 adds 0.03 total to unlust (0.01 + 0.02)."""
        from simulation.agents.needs_calculator import update_insomnia
        agent = _make_agent()
        agent.needs.set_level(NeedType.SLEEP, 0.5)
        agent.needs.set_level(NeedType.SAFETY, 0.5)
        agent.unlust = 0.5
        agent.insomnia_severity = 0.8  # > 0.7
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.unlust == pytest.approx(0.53)

    def test_insomnia_skipped_dead_agent(self) -> None:
        """Dead agent's insomnia is not updated."""
        from simulation.agents.needs_calculator import update_insomnia
        agent = _make_agent(is_alive=False)
        agent.needs.set_level(NeedType.SLEEP, 0.0)
        agent.insomnia_severity = 0.0
        world = _make_world()
        update_insomnia(agent, world)
        assert agent.insomnia_severity == 0.0
        assert agent.ticks_without_sleep == 0


# ===========================================================================
# Additional death condition tests
# ===========================================================================

class TestDeathAdditional:
    """Additional death condition coverage: elderly, hardship, sleep."""

    def test_death_elderly_mortality(self) -> None:
        """Elderly agents face age mortality roll."""
        from shared.constants.defaults import AGE_MORTALITY_BASE, AGE_MORTALITY_ELDERLY
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        agent.age_bracket = "elderly"
        agent.purpose_fulfillment = 1.0
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)

        class _AlwaysDieRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0  # Always triggers mortality

        assert check_death(agent, _AlwaysDieRNG()) is True
        assert agent.cause_of_death == "old_age"

    def test_death_elderly_survives(self) -> None:
        """Elderly agents can survive the mortality roll."""
        from shared.constants.defaults import AGE_MORTALITY_BASE, AGE_MORTALITY_ELDERLY
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        agent.age_bracket = "elderly"
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)

        class _AlwaysLiveRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 1.0  # Never triggers mortality

        assert check_death(agent, _AlwaysLiveRNG()) is False

    def test_death_sleep_exhaustion(self) -> None:
        """Sleep below threshold with 50+ ticks without sleep causes death with 30% probability."""
        from shared.constants.defaults import SLEEP_DEATH_THRESHOLD
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)
        _set_need(agent, NeedType.SLEEP, SLEEP_DEATH_THRESHOLD - 0.01)
        agent.ticks_without_sleep = 50

        class _AlwaysDieRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0

        assert check_death(agent, _AlwaysDieRNG()) is True
        assert agent.cause_of_death == "insomnia_exhaustion"

    def test_death_insomnia_not_enough_ticks(self) -> None:
        """Sleep below threshold but <50 ticks without sleep does not cause death."""
        from shared.constants.defaults import SLEEP_DEATH_THRESHOLD
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)
        _set_need(agent, NeedType.SLEEP, SLEEP_DEATH_THRESHOLD - 0.01)
        agent.ticks_without_sleep = 30
        rng = DeterministicRNG(42)

        assert check_death(agent, rng) is False

    def test_death_economic_hardship(self) -> None:
        """Unemployed agent with low money and high inflation may die."""
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)
        agent.resources.employed = False
        agent.resources.money = 10.0
        world = _make_world()
        world.economy.inflation_rate = 0.15  # High inflation

        class _AlwaysDieRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0  # Always triggers hardship death

        assert check_death(agent, _AlwaysDieRNG(), world) is True

    def test_death_economic_hardship_avoids(self) -> None:
        """Employed agent with money is not at risk of economic hardship death."""
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)
        agent.resources.employed = True
        agent.resources.money = 1000.0
        agent.purpose_fulfillment = 1.0
        world = _make_world()
        world.economy.inflation_rate = 0.15

        class _AlwaysDieRNG(DeterministicRNG):
            def __init__(self) -> None:
                super().__init__(0)

            def random(self) -> float:
                return 0.0

        # hardship_risk will be 0 because employed=True → (1-1)=0
        assert check_death(agent, _AlwaysDieRNG(), world) is False

    def test_death_no_world_skips_hardship(self) -> None:
        """When world is None, hardship check is skipped."""
        from simulation.agents.needs_calculator import check_death
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.5)
        _set_need(agent, NeedType.WATER, 0.5)
        agent.resources.employed = False
        agent.resources.money = 0.0
        rng = DeterministicRNG(42)
        # No world → no hardship check
        assert check_death(agent, rng) is False

    def test_death_starvation_precedence_over_economic(self) -> None:
        """Starvation is checked before economic hardship."""
        from simulation.agents.needs_calculator import check_death
        from shared.constants.defaults import FOOD_DEATH_THRESHOLD
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, FOOD_DEATH_THRESHOLD)
        _set_need(agent, NeedType.WATER, 0.5)
        rng = DeterministicRNG(42)
        assert check_death(agent, rng) is True
        assert agent.cause_of_death == "food_starvation"


# ===========================================================================
# Environmental crisis multiplier tests
# ===========================================================================

class TestEnvCrisisMultiplier:
    """Tests for environmental crisis multipliers on need decay."""

    def test_food_crisis_multiplier(self) -> None:
        """When food_availability < 0.4, food decay uses ENV_NEED_DECAY_FOOD_MULTIPLIER."""
        from shared.constants.defaults import ENV_NEED_DECAY_FOOD_MULTIPLIER, SCARCITY_BASE, FOOD_DECAY_RATE
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.8)
        world = _make_world(food_availability=0.3)  # Below 0.4 → crisis
        decay_needs(agent, world, DeterministicRNG(42))
        scarcity = SCARCITY_BASE - 0.3
        expected = 0.8 - FOOD_DECAY_RATE * scarcity * ENV_NEED_DECAY_FOOD_MULTIPLIER
        assert agent.needs.get_level(NeedType.FOOD) == pytest.approx(expected)

    def test_water_crisis_multiplier(self) -> None:
        """When water_availability < 0.4, water decay uses ENV_NEED_DECAY_WATER_MULTIPLIER."""
        from shared.constants.defaults import ENV_NEED_DECAY_WATER_MULTIPLIER, SCARCITY_BASE, WATER_DECAY_RATE
        agent = _make_agent()
        _set_need(agent, NeedType.WATER, 0.8)
        world = _make_world(food_availability=0.85)
        world.water_availability = 0.3  # Below 0.4 → crisis
        decay_needs(agent, world, DeterministicRNG(42))
        scarcity = SCARCITY_BASE - 0.85  # Food availability used for scarcity
        expected = 0.8 - WATER_DECAY_RATE * scarcity * ENV_NEED_DECAY_WATER_MULTIPLIER
        assert agent.needs.get_level(NeedType.WATER) == pytest.approx(expected)

    def test_no_crisis_at_normal_levels(self) -> None:
        """When food/water availability >= 0.4, normal multiplier (1.0) is used."""
        from shared.constants.defaults import FOOD_DECAY_RATE, SCARCITY_BASE
        agent = _make_agent()
        _set_need(agent, NeedType.FOOD, 0.8)
        world = _make_world(food_availability=0.5)  # >= 0.4 → no crisis
        decay_needs(agent, world, DeterministicRNG(42))
        scarcity = SCARCITY_BASE - 0.5
        expected = 0.8 - FOOD_DECAY_RATE * scarcity * 1.0
        assert agent.needs.get_level(NeedType.FOOD) == pytest.approx(expected)
