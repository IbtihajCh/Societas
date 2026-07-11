"""Tests for the agent factory module."""

import statistics

import pytest

from shared.constants.defaults import GRID_SIZE
from shared.constants.simulation_constants import (
    EDUCATION_BY_WEALTH,
    WEALTH_CLASS_DISTRIBUTION,
)
from shared.types.enums import (
    Culture,
    EducationLevel,
    Gender,
    JobType,
    NeedType,
    WealthClass,
)
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.agent_factory import (
    create_agent,
    create_initial_population,
)


class TestCreateAgent:
    """Tests for create_agent()."""

    def test_create_agent_basic(self):
        """Verify a basic agent is created with expected defaults."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        assert agent.id == "0"
        assert agent.is_alive is True
        # All major sub-objects should be populated
        assert agent.traits is not None
        assert agent.needs is not None
        assert agent.emotions is not None
        assert agent.resources is not None

    def test_traits_in_range(self):
        """All 8 psychological traits must be in [0.0, 1.0]."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        for trait_name in [
            "creativity",
            "morality",
            "anger_tendency",
            "extraversion",
            "ambition",
            "resilience",
            "dominance_urge",
            "risk_tolerance",
        ]:
            value = getattr(agent.traits, trait_name)
            assert 0.0 <= value <= 1.0, (
                f"Trait {trait_name} = {value} outside [0, 1]"
            )

    def test_traits_deterministic(self):
        """Same seed must produce identical traits."""
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        agent1 = create_agent(0, rng1)
        agent2 = create_agent(0, rng2)

        t1 = agent1.traits
        t2 = agent2.traits
        assert t1.creativity == t2.creativity
        assert t1.morality == t2.morality
        assert t1.anger_tendency == t2.anger_tendency
        assert t1.extraversion == t2.extraversion
        assert t1.ambition == t2.ambition
        assert t1.resilience == t2.resilience
        assert t1.dominance_urge == t2.dominance_urge
        assert t1.risk_tolerance == t2.risk_tolerance

    def test_traits_different_seeds(self):
        """Different seeds should produce different traits."""
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=99)
        agent1 = create_agent(0, rng1)
        agent2 = create_agent(0, rng2)

        t1 = agent1.traits
        t2 = agent2.traits
        # At least some traits should differ
        trait_values_1 = [
            t1.creativity, t1.morality, t1.anger_tendency,
            t1.extraversion, t1.ambition, t1.resilience,
        ]
        trait_values_2 = [
            t2.creativity, t2.morality, t2.anger_tendency,
            t2.extraversion, t2.ambition, t2.resilience,
        ]
        assert trait_values_1 != trait_values_2

    def test_anger_tendency_skewed_low(self):
        """
        Over 1000 agents, mean anger_tendency should be lower than mean creativity.
        Beta(2,3) has mean 0.4; Beta(2,2) has mean 0.5.
        """
        anger_values = []
        creativity_values = []
        for seed in range(1000):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            anger_values.append(agent.traits.anger_tendency)
            creativity_values.append(agent.traits.creativity)

        mean_anger = statistics.mean(anger_values)
        mean_creativity = statistics.mean(creativity_values)
        assert mean_anger < mean_creativity, (
            f"Expected mean anger ({mean_anger:.4f}) < mean creativity "
            f"({mean_creativity:.4f})"
        )

    def test_wealth_class_distribution(self):
        """Over 1000 agents, verify wealth class proportions approximately match config."""
        from collections import defaultdict
        wealth_counts: dict[WealthClass, int] = defaultdict(int)
        for seed in range(1000):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            wealth_counts[agent.wealth_class] += 1

        total = sum(wealth_counts.values())
        for wc, expected_pct in WEALTH_CLASS_DISTRIBUTION.items():
            actual_pct = wealth_counts[wc] / total * 100.0
            # Allow ±15% absolute tolerance
            assert abs(actual_pct - float(expected_pct)) < 15.0, (
                f"Wealth class {wc}: expected ~{expected_pct}%, got {actual_pct:.1f}%"
            )

    def test_money_in_range(self):
        """Agent money should be within its wealth class range."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        wc = agent.wealth_class
        low, high = (100.0, 800.0) if wc == WealthClass.POOR else (
            (2000.0, 8000.0) if wc == WealthClass.MIDDLE else (15000.0, 80000.0)
        )
        assert low <= agent.resources.money <= high, (
            f"Money {agent.resources.money} not in [{low}, {high}] for {wc}"
        )

    def test_employed_get_job(self):
        """Employed agents should have a non-UNEMPLOYED job type and positive salary."""
        # Use many agents to find some employed ones
        for seed in range(200):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            if agent.resources.employed:
                assert agent.job_type != JobType.UNEMPLOYED, (
                    f"Employed agent has UNEMPLOYED job type"
                )
                assert agent.resources.base_salary > 0, (
                    f"Employed agent has zero salary"
                )
                return
        pytest.fail("No employed agent found in 200 attempts")

    def test_unemployed_no_job(self):
        """Unemployed agents should have UNEMPLOYED job type and zero salary."""
        for seed in range(200):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            if not agent.resources.employed:
                assert agent.job_type == JobType.UNEMPLOYED, (
                    f"Unemployed agent has job type {agent.job_type}"
                )
                assert agent.resources.base_salary == 0.0, (
                    f"Unemployed agent has non-zero salary"
                )
                return
        pytest.fail("No unemployed agent found in 200 attempts")

    def test_education_by_wealth(self):
        """Education distribution should follow wealth class tendencies."""
        poor_primary = 0
        poor_secondary = 0
        rich_secondary = 0
        rich_higher = 0
        poor_count = 0
        rich_count = 0

        for seed in range(2000):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            if agent.wealth_class == WealthClass.POOR:
                poor_count += 1
                if agent.resources.education == EducationLevel.PRIMARY:
                    poor_primary += 1
                elif agent.resources.education == EducationLevel.SECONDARY:
                    poor_secondary += 1
            elif agent.wealth_class == WealthClass.RICH:
                rich_count += 1
                if agent.resources.education == EducationLevel.SECONDARY:
                    rich_secondary += 1
                elif agent.resources.education == EducationLevel.HIGHER:
                    rich_higher += 1

        # Poor agents: PRIMARY should dominate
        if poor_count > 0:
            poor_primary_pct = poor_primary / poor_count * 100.0
            assert poor_primary_pct > 40.0, (
                f"Poor agents with PRIMARY education: {poor_primary_pct:.1f}% "
                f"(expected >40%)"
            )

        # Rich agents: HIGHER should be common
        if rich_count > 0:
            rich_higher_pct = rich_higher / rich_count * 100.0
            assert rich_higher_pct > 30.0, (
                f"Rich agents with HIGHER education: {rich_higher_pct:.1f}% "
                f"(expected >30%)"
            )

    def test_needs_initialized(self):
        """All 13 needs should have values set, with correct ranges."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        needs = agent.needs

        # All 13 need types should have values
        assert len(needs.levels) == 13

        # FOOD and WATER in [0.5, 0.8]
        assert 0.5 <= needs.get_level(NeedType.FOOD) <= 0.8
        assert 0.5 <= needs.get_level(NeedType.WATER) <= 0.8

        # SHELTER depends on property
        if agent.resources.property:
            assert needs.get_level(NeedType.SHELTER) == 1.0
        else:
            assert needs.get_level(NeedType.SHELTER) == 0.3

        # SEXUAL_TENSION and INFERIORITY_GAP start at 0
        assert needs.get_level(NeedType.SEXUAL_TENSION) == 0.0
        assert needs.get_level(NeedType.INFERIORITY_GAP) == 0.0

    def test_grid_position(self):
        """Grid coordinates should be in [0, GRID_SIZE)."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        assert 0 <= agent.grid_x < GRID_SIZE
        assert 0 <= agent.grid_y < GRID_SIZE

    def test_gender_distribution(self):
        """Over 100 agents, both genders should appear."""
        genders_found: set[Gender] = set()
        for seed in range(100):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            genders_found.add(agent.gender)
        assert Gender.MALE in genders_found
        assert Gender.FEMALE in genders_found

    def test_culture_distribution(self):
        """Over 100 agents, all 3 cultures should appear."""
        cultures_found: set[Culture] = set()
        for seed in range(100):
            rng = DeterministicRNG(seed=seed)
            agent = create_agent(0, rng)
            cultures_found.add(agent.culture)
        assert Culture.A in cultures_found
        assert Culture.B in cultures_found
        assert Culture.C in cultures_found

    def test_health_in_range(self):
        """Health should be in [0.7, 1.0]."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        assert 0.7 <= agent.resources.health <= 1.0

    def test_wealth_mirrors_money(self):
        """resources.wealth should equal resources.money initially."""
        rng = DeterministicRNG(seed=42)
        agent = create_agent(0, rng)
        assert agent.resources.wealth == agent.resources.money


class TestCreateInitialPopulation:
    """Tests for create_initial_population()."""

    def test_create_initial_population(self):
        """Create 80 agents and verify correct structure."""
        rng = DeterministicRNG(seed=42)
        population = create_initial_population(80, rng)
        assert len(population) == 80

        # All IDs should be unique
        ids = [a.id for a in population]
        assert len(set(ids)) == 80

        # All IDs should be sequential "0", "1", ..., "79"
        expected_ids = {str(i) for i in range(80)}
        assert set(ids) == expected_ids

    def test_population_deterministic(self):
        """Same seed produces identical population."""
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        pop1 = create_initial_population(5, rng1)
        pop2 = create_initial_population(5, rng2)
        for a1, a2 in zip(pop1, pop2):
            assert a1.id == a2.id
            assert a1.traits == a2.traits
            assert a1.resources.money == a2.resources.money
