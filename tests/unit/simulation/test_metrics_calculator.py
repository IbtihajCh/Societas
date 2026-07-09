"""Tests for simulation/world/metrics_calculator.py."""

from typing import Any

import pytest

from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
)
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.types.aliases import AgentId, TickNumber
from shared.types.enums import ActionType, EmotionType, NeedType, WealthClass
from simulation.world.metrics_calculator import (
    compute_action_frequencies,
    compute_state_hash,
    compute_wealth_stratified_metrics,
    update_world_metrics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(
    *,
    agent_id: str = "test-agent",
    is_alive: bool = True,
    crimes_committed: int = 0,
    protest_count: int = 0,
    employed: bool = False,
    money: float = 100.0,
    unlust: float = 0.0,
    morality: float = 0.5,
    happiness_score: float = 0.5,
    wealth_class: WealthClass = WealthClass.POOR,
    last_action: ActionType = ActionType.IDLE,
    grid_x: int = 0,
    grid_y: int = 0,
    primary_emotion: EmotionType = EmotionType.NORMAL,
) -> AgentState:
    """Create a minimal AgentState with sensible defaults for testing."""
    traits = AgentTraits(morality=morality)
    needs = AgentNeeds()
    resources = AgentResources(money=money, employed=employed)
    emotions = AgentEmotions(
        primary=primary_emotion,
        happiness_score=happiness_score,
    )
    return AgentState(
        id=AgentId(agent_id),
        traits=traits,
        needs=needs,
        resources=resources,
        emotions=emotions,
        is_alive=is_alive,
        crimes_committed=crimes_committed,
        protest_count=protest_count,
        unlust=unlust,
        wealth_class=wealth_class,
        last_action=last_action,
        grid_x=grid_x,
        grid_y=grid_y,
    )


def _make_world(**overrides: Any) -> SimulationState:
    """Create a minimal SimulationState for testing."""
    kwargs: dict[str, Any] = {
        "time_step": TickNumber(0),
        "population": 0,
        "crime_rate": 0.0,
        "protest_intensity": 0.0,
        "unemployment_rate": 0.0,
        "unlust": 0.0,
        "morality": 0.5,
        "food_availability": 0.85,
        "water_availability": 0.90,
        "tax_rate": 0.15,
        "welfare_enabled": False,
    }
    kwargs.update(overrides)
    return SimulationState(**kwargs)


def _set_food_need(agent: AgentState, value: float) -> None:
    """Set the FOOD need level for an agent."""
    agent.needs.set_level(NeedType.FOOD, value)


# ---------------------------------------------------------------------------
# update_world_metrics tests
# ---------------------------------------------------------------------------


class TestUpdateWorldMetrics:
    """Tests for update_world_metrics."""

    def test_update_world_metrics_basic(self) -> None:
        """10 agents, some crimes, some protests → metrics computed."""
        agents = [
            _make_agent(
                agent_id=f"a{i}",
                crimes_committed=1 if i < 4 else 0,
                protest_count=1 if i < 2 else 0,
                employed=(i % 3 != 0),
                unlust=0.2 + i * 0.02,
                morality=0.4 + i * 0.03,
            )
            for i in range(10)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        assert world.population == 10
        assert world.time_step == 1
        assert world.crime_rate > 0.0
        assert world.protest_intensity > 0.0
        assert world.unemployment_rate > 0.0
        assert 0.0 < world.unlust <= 1.0
        assert 0.0 < world.morality <= 1.0

    def test_crime_rate_formula(self) -> None:
        """10 agents, 8 total crimes → crime_rate = 8/(10*8) = 0.1."""
        agents = [
            _make_agent(agent_id=f"a{i}", crimes_committed=1)
            for i in range(8)
        ] + [
            _make_agent(agent_id=f"a{i}", crimes_committed=0)
            for i in range(8, 10)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        assert world.crime_rate == pytest.approx(0.1)

    def test_crime_rate_capped_at_one(self) -> None:
        """Crime rate is capped at 1.0 even with extreme crime."""
        agents = [
            _make_agent(agent_id=f"a{i}", crimes_committed=100)
            for i in range(10)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        assert world.crime_rate == pytest.approx(1.0)

    def test_protest_intensity_formula(self) -> None:
        """10 agents, 4 total protests → 4/(10*4) = 0.1."""
        agents = [
            _make_agent(agent_id=f"a{i}", protest_count=1)
            for i in range(4)
        ] + [
            _make_agent(agent_id=f"a{i}", protest_count=0)
            for i in range(4, 10)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        assert world.protest_intensity == pytest.approx(0.1)

    def test_unemployment_rate(self) -> None:
        """10 agents, 3 unemployed → 0.3."""
        agents = [
            _make_agent(agent_id=f"a{i}", employed=(i >= 3))
            for i in range(10)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        assert world.unemployment_rate == pytest.approx(0.3)

    def test_avg_unlust(self) -> None:
        """Verify average unlust computed correctly."""
        agents = [
            _make_agent(agent_id=f"a{i}", unlust=0.1 * (i + 1))
            for i in range(5)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        # unlust values: 0.1, 0.2, 0.3, 0.4, 0.5 → avg = 0.3
        assert world.unlust == pytest.approx(0.3)

    def test_avg_morality(self) -> None:
        """Verify average morality computed correctly."""
        agents = [
            _make_agent(agent_id=f"a{i}", morality=0.2 * (i + 1))
            for i in range(5)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        # morality: 0.2, 0.4, 0.6, 0.8, 1.0 → avg = 0.6
        assert world.morality == pytest.approx(0.6)

    def test_population_count(self) -> None:
        """Only living agents counted."""
        agents = [
            _make_agent(agent_id=f"alive{i}", is_alive=True)
            for i in range(7)
        ] + [
            _make_agent(agent_id=f"dead{i}", is_alive=False)
            for i in range(3)
        ]
        world = _make_world()

        update_world_metrics(world, agents)

        assert world.population == 7

    def test_time_step_increment(self) -> None:
        """time_step increments by 1."""
        agents = [_make_agent()]
        world = _make_world(time_step=TickNumber(5))

        update_world_metrics(world, agents)

        assert world.time_step == 6

    def test_empty_population(self) -> None:
        """No living agents → no crash, no changes."""
        agents = [
            _make_agent(agent_id="dead", is_alive=False),
        ]
        world = _make_world(
            time_step=TickNumber(5),
            crime_rate=0.3,
            population=100,
        )

        update_world_metrics(world, agents)

        # No changes should have been made
        assert world.time_step == 5
        assert world.crime_rate == 0.3
        assert world.population == 100


# ---------------------------------------------------------------------------
# compute_wealth_stratified_metrics tests
# ---------------------------------------------------------------------------


class TestWealthStratifiedMetrics:
    """Tests for compute_wealth_stratified_metrics."""

    def test_wealth_stratified_basic(self) -> None:
        """3 classes represented, verify all have entries."""
        agents = [
            _make_agent(agent_id="p1", wealth_class=WealthClass.POOR),
            _make_agent(agent_id="m1", wealth_class=WealthClass.MIDDLE),
            _make_agent(agent_id="r1", wealth_class=WealthClass.RICH),
        ]
        result = compute_wealth_stratified_metrics(agents)

        assert "poor" in result
        assert "middle" in result
        assert "rich" in result

    def test_wealth_stratified_empty_class(self) -> None:
        """Class with 0 agents → zeros."""
        agents = [
            _make_agent(agent_id="r1", wealth_class=WealthClass.RICH),
        ]
        result = compute_wealth_stratified_metrics(agents)

        assert result["poor"] == {
            "avg_happiness": 0.0,
            "avg_unlust": 0.0,
            "avg_money": 0.0,
            "count": 0,
            "crime_rate": 0.0,
        }
        assert result["middle"] == {
            "avg_happiness": 0.0,
            "avg_unlust": 0.0,
            "avg_money": 0.0,
            "count": 0,
            "crime_rate": 0.0,
        }
        assert result["rich"]["count"] == 1

    def test_wealth_stratified_values(self) -> None:
        """Verify avg_happiness, avg_unlust, avg_money computed."""
        agents = [
            _make_agent(
                agent_id="p1",
                wealth_class=WealthClass.POOR,
                happiness_score=0.2,
                unlust=0.7,
                money=50.0,
            ),
            _make_agent(
                agent_id="p2",
                wealth_class=WealthClass.POOR,
                happiness_score=0.4,
                unlust=0.5,
                money=150.0,
            ),
            _make_agent(
                agent_id="r1",
                wealth_class=WealthClass.RICH,
                happiness_score=0.9,
                unlust=0.1,
                money=50000.0,
            ),
        ]
        result = compute_wealth_stratified_metrics(agents)

        assert result["poor"]["avg_happiness"] == pytest.approx(0.3)
        assert result["poor"]["avg_unlust"] == pytest.approx(0.6)
        assert result["poor"]["avg_money"] == pytest.approx(100.0)
        assert result["poor"]["count"] == 2

        assert result["rich"]["avg_happiness"] == pytest.approx(0.9)
        assert result["rich"]["avg_unlust"] == pytest.approx(0.1)
        assert result["rich"]["avg_money"] == pytest.approx(50000.0)
        assert result["rich"]["count"] == 1

    def test_wealth_stratified_crime_rate(self) -> None:
        """Crime rate computed per class."""
        agents = [
            _make_agent(
                agent_id="p1",
                wealth_class=WealthClass.POOR,
                crimes_committed=2,
            ),
            _make_agent(
                agent_id="p2",
                wealth_class=WealthClass.POOR,
                crimes_committed=0,
            ),
        ]
        result = compute_wealth_stratified_metrics(agents)

        # 2 crimes across 2 agents: 2 / (2 * 8) = 0.125
        assert result["poor"]["crime_rate"] == pytest.approx(0.125)

    def test_wealth_stratified_excludes_dead(self) -> None:
        """Dead agents excluded from wealth-stratified metrics."""
        agents = [
            _make_agent(
                agent_id="alive",
                wealth_class=WealthClass.POOR,
                is_alive=True,
            ),
            _make_agent(
                agent_id="dead",
                wealth_class=WealthClass.POOR,
                is_alive=False,
            ),
        ]
        result = compute_wealth_stratified_metrics(agents)

        assert result["poor"]["count"] == 1


# ---------------------------------------------------------------------------
# compute_action_frequencies tests
# ---------------------------------------------------------------------------


class TestActionFrequencies:
    """Tests for compute_action_frequencies."""

    def test_action_frequencies_basic(self) -> None:
        """10 actions, 5 work, 3 rest, 2 idle → work=0.5, rest=0.3, idle=0.2."""
        actions = [
            AgentActionResult(agent_id=AgentId("a"), action=ActionType.WORK)
            for _ in range(5)
        ] + [
            AgentActionResult(agent_id=AgentId("b"), action=ActionType.REST)
            for _ in range(3)
        ] + [
            AgentActionResult(agent_id=AgentId("c"), action=ActionType.IDLE)
            for _ in range(2)
        ]
        result = compute_action_frequencies(actions)

        assert result["work"] == pytest.approx(0.5)
        assert result["rest"] == pytest.approx(0.3)
        assert result["idle"] == pytest.approx(0.2)
        assert sum(result.values()) == pytest.approx(1.0)

    def test_action_frequencies_empty(self) -> None:
        """No actions → empty dict."""
        result = compute_action_frequencies([])

        assert result == {}


# ---------------------------------------------------------------------------
# compute_state_hash tests
# ---------------------------------------------------------------------------


class TestStateHash:
    """Tests for compute_state_hash."""

    def _make_minimal_state(
        self,
        agent_count: int = 2,
    ) -> tuple[SimulationState, list[AgentState]]:
        """Create a minimal world and agent list for hash testing."""
        world = _make_world(
            time_step=TickNumber(1),
            population=agent_count,
            crime_rate=0.1,
            food_availability=0.8,
        )
        agents = []
        for i in range(agent_count):
            agent = _make_agent(
                agent_id=f"agent-{i}",
                money=500.0 + i * 100,
                unlust=0.1 + i * 0.05,
                morality=0.5 + i * 0.1,
                happiness_score=0.6 + i * 0.1,
                grid_x=i,
                grid_y=i * 2,
                last_action=ActionType.WORK if i % 2 == 0 else ActionType.REST,
                primary_emotion=EmotionType.HAPPY if i == 0 else EmotionType.NORMAL,
            )
            _set_food_need(agent, 0.75 - i * 0.1)
            agents.append(agent)
        return world, agents

    def test_state_hash_deterministic(self) -> None:
        """Same state → same hash."""
        world1, agents1 = self._make_minimal_state()
        world2, agents2 = self._make_minimal_state()

        hash1 = compute_state_hash(world1, agents1)
        hash2 = compute_state_hash(world2, agents2)

        assert hash1 == hash2

    def test_state_hash_different_states(self) -> None:
        """Different state → different hash."""
        world1, agents1 = self._make_minimal_state()
        world2, agents2 = self._make_minimal_state()

        # Change one value
        world2.crime_rate = 0.5

        hash1 = compute_state_hash(world1, agents1)
        hash2 = compute_state_hash(world2, agents2)

        assert hash1 != hash2

    def test_state_hash_excludes_dead(self) -> None:
        """Dead agents produce a different hash than alive agents."""
        world, agents_alive = self._make_minimal_state()
        agents_dead = [a for a in agents_alive]  # shallow copy the list
        agents_dead[0] = AgentState(
            id=agents_alive[0].id,
            is_alive=False,
        )

        hash_alive = compute_state_hash(world, agents_alive)
        hash_dead = compute_state_hash(world, agents_dead)

        assert hash_alive != hash_dead

    def test_state_hash_format(self) -> None:
        """Returns 64-char hex string (SHA-256)."""
        world, agents = self._make_minimal_state()

        hash_str = compute_state_hash(world, agents)

        assert len(hash_str) == 64
        # Verify it's a valid hex string
        int(hash_str, 16)

    def test_state_hash_sorting_independent(self) -> None:
        """Hash is independent of agent list order due to sorting."""
        world1, agents1 = self._make_minimal_state(agent_count=3)
        agents2 = list(reversed(agents1.copy()))

        hash1 = compute_state_hash(world1, agents1)
        hash2 = compute_state_hash(world1, agents2)

        assert hash1 == hash2
