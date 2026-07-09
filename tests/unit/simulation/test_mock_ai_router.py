"""Tests for MockAIRouter — trait-aware decisions for testing without GPU."""

import json

import pytest

from shared.types.enums import ActionType, EmotionType, NeedType
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.agent_factory import create_agent
from simulation.engine.mock_ai_router import MockAIRouter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rng() -> DeterministicRNG:
    """Shared deterministic RNG for tests."""
    return DeterministicRNG(seed=42)


@pytest.fixture
def agent(rng: DeterministicRNG) -> AgentState:
    """A single agent for testing."""
    return create_agent(0, rng)


@pytest.fixture
def agents(rng: DeterministicRNG) -> list[AgentState]:
    """Multiple agents for testing."""
    return [create_agent(i, rng) for i in range(3)]


@pytest.fixture
def world() -> SimulationState:
    """Default world state for testing."""
    return SimulationState()


@pytest.fixture
def router(rng: DeterministicRNG) -> MockAIRouter:
    """Mock AI router with known seed."""
    return MockAIRouter(rng=rng)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMockAIRouter:
    """Tests for MockAIRouter."""

    def test_mock_router_is_available(self, router: MockAIRouter) -> None:
        """Mock router is always available."""
        assert router.is_available() is True

    def test_mock_router_agent_decide_returns_json(
        self, router: MockAIRouter, agent: AgentState, world: SimulationState
    ) -> None:
        """agent_decide returns valid JSON with action, feeling, reason."""
        response = router.agent_decide("prompt", agent, world)
        data = json.loads(response)
        assert "action" in data
        assert "feeling" in data
        assert "reason" in data
        assert isinstance(data["action"], str)
        assert isinstance(data["feeling"], str)
        assert isinstance(data["reason"], str)

    def test_mock_router_agent_decide_valid_action(
        self, router: MockAIRouter, agent: AgentState, world: SimulationState
    ) -> None:
        """agent_decide returns a valid ActionType value."""
        response = router.agent_decide("prompt", agent, world)
        data = json.loads(response)
        action_names = {a.value for a in ActionType}
        assert data["action"] in action_names, f"Unknown action: {data['action']}"

    def test_mock_router_agent_decide_batch(
        self, router: MockAIRouter, agents: list[AgentState], world: SimulationState
    ) -> None:
        """batch returns list of JSON strings, one per agent."""
        prompts = ["prompt"] * len(agents)
        responses = router.agent_decide_batch(prompts, agents, world)
        assert len(responses) == len(agents)
        for resp in responses:
            data = json.loads(resp)
            assert "action" in data

    def test_mock_router_moral_reasoning_returns_json(
        self, router: MockAIRouter, agent: AgentState, world: SimulationState
    ) -> None:
        """moral_reasoning returns valid JSON."""
        response = router.moral_reasoning("prompt", agent, world)
        data = json.loads(response)
        assert "action" in data
        assert "feeling" in data
        assert "reason" in data

    def test_mock_router_moral_reasoning_batch(
        self, router: MockAIRouter, agents: list[AgentState], world: SimulationState
    ) -> None:
        """moral_reasoning batch returns list of JSON strings."""
        prompts = ["prompt"] * len(agents)
        responses = router.moral_reasoning_batch(prompts, agents, world)
        assert len(responses) == len(agents)
        for resp in responses:
            data = json.loads(resp)
            assert "action" in data

    def test_mock_router_governance_advisory_stable(
        self, router: MockAIRouter, agents: list[AgentState], world: SimulationState
    ) -> None:
        """Low unlust, low crime → 'Society is stable'."""
        # Ensure agents have low unlust
        for a in agents:
            a.unlust = 0.1
        world.crime_rate = 0.05
        world.unemployment_rate = 0.05
        advisory = router.governance_advisory(world, agents)
        assert advisory["recommendation"] == "Society is stable"

    def test_mock_router_governance_advisory_high_unlust(
        self, router: MockAIRouter, agents: list[AgentState], world: SimulationState
    ) -> None:
        """High unlust → welfare recommendation."""
        for a in agents:
            a.unlust = 0.75
        world.crime_rate = 0.05
        world.unemployment_rate = 0.05
        advisory = router.governance_advisory(world, agents)
        assert "welfare" in advisory["recommendation"].lower()

    def test_mock_router_governance_advisory_high_crime(
        self, router: MockAIRouter, agents: list[AgentState], world: SimulationState
    ) -> None:
        """High crime → public order recommendation."""
        for a in agents:
            a.unlust = 0.5
        world.crime_rate = 0.20
        world.unemployment_rate = 0.05
        advisory = router.governance_advisory(world, agents)
        assert "public order" in advisory["recommendation"].lower()

    def test_mock_router_governance_advisory_no_agents(
        self, router: MockAIRouter, world: SimulationState
    ) -> None:
        """Empty agent list → 'No living agents'."""
        advisory = router.governance_advisory(world, [])
        assert advisory["assessment"] == "No living agents"
        assert advisory["recommendation"] == "N/A"

    def test_mock_router_call_count(
        self, router: MockAIRouter, agent: AgentState, world: SimulationState
    ) -> None:
        """call_count tracks number of LLM calls."""
        assert router.call_count == 0
        router.agent_decide("p1", agent, world)
        assert router.call_count == 1
        router.moral_reasoning("p2", agent, world)
        assert router.call_count == 2
        router.agent_decide("p3", agent, world)
        assert router.call_count == 3

    def test_mock_router_deterministic(
        self, agent: AgentState, world: SimulationState
    ) -> None:
        """Same agent, same world, same seed → same response."""
        router_a = MockAIRouter(rng=DeterministicRNG(seed=42))
        router_b = MockAIRouter(rng=DeterministicRNG(seed=42))
        resp_a = router_a.agent_decide("prompt", agent, world)
        resp_b = router_b.agent_decide("prompt", agent, world)
        assert resp_a == resp_b

    # ------------------------------------------------------------------
    # Trait-aware variety tests
    # ------------------------------------------------------------------

    def _setup_trait_agent(
        self, rng: DeterministicRNG, agent_id: int = 99
    ) -> AgentState:
        """Create a base agent with sufficient needs for personality testing."""
        agent = create_agent(agent_id, rng)
        agent.needs.set_level(NeedType.FOOD, 0.5)
        agent.needs.set_level(NeedType.WATER, 0.5)
        agent.needs.set_level(NeedType.SLEEP, 0.5)
        agent.needs.set_level(NeedType.SOCIAL_CONNECTION, 0.5)
        agent.resources.employed = True
        agent.resources.money = 500
        return agent

    def test_mock_ai_variety(
        self, world: SimulationState
    ) -> None:
        """Run agent_decide 20 times with different seeds → at least 3 different actions."""
        agent = create_agent(0, DeterministicRNG(seed=99))
        agent.needs.set_level(NeedType.FOOD, 0.5)
        agent.needs.set_level(NeedType.WATER, 0.5)
        agent.needs.set_level(NeedType.SLEEP, 0.3)
        agent.needs.set_level(NeedType.SOCIAL_CONNECTION, 0.5)
        agent.resources.employed = True
        agent.resources.money = 500
        agent.traits.extraversion = 0.9
        agent.traits.ambition = 0.2
        agent.traits.anger_tendency = 0.5
        agent.traits.morality = 0.4
        agent.unlust = 0.5

        actions: list[str] = []
        for seed in range(20):
            router = MockAIRouter(rng=DeterministicRNG(seed=seed))
            response = router.agent_decide("prompt", agent, world)
            data = json.loads(response)
            actions.append(data["action"])

        unique_actions = set(actions)
        assert len(unique_actions) >= 3, (
            f"Expected at least 3 different actions across 20 seeds, "
            f"got {len(unique_actions)}: {unique_actions}"
        )

    def test_mock_ai_extravert_social(
        self, world: SimulationState
    ) -> None:
        """High extraversion agent selects BEFRIEND more often."""
        agent = self._setup_trait_agent(DeterministicRNG(seed=55))
        agent.traits.extraversion = 0.95
        agent.needs.set_level(NeedType.SOCIAL_CONNECTION, 0.2)

        actions: list[str] = []
        for seed in range(30):
            router = MockAIRouter(rng=DeterministicRNG(seed=seed))
            response = router.agent_decide("prompt", agent, world)
            data = json.loads(response)
            actions.append(data["action"])

        befriend_count = actions.count("befriend")
        assert befriend_count >= 5, (
            f"Expected BEFRIEND >= 5/30 for extravert agent, got {befriend_count}/30"
        )

    def test_mock_ai_angry_protest(
        self, world: SimulationState
    ) -> None:
        """Angry agent selects PROTEST more often."""
        agent = self._setup_trait_agent(DeterministicRNG(seed=77))
        agent.emotions.primary = EmotionType.ANGRY
        agent.traits.anger_tendency = 0.8
        agent.trust_in_govt = 0.2

        actions: list[str] = []
        for seed in range(30):
            router = MockAIRouter(rng=DeterministicRNG(seed=seed))
            response = router.agent_decide("prompt", agent, world)
            data = json.loads(response)
            actions.append(data["action"])

        protest_count = actions.count("protest")
        assert protest_count >= 5, (
            f"Expected PROTEST >= 5/30 for angry agent, got {protest_count}/30"
        )

    def test_mock_ai_moral_shares(
        self, world: SimulationState
    ) -> None:
        """High morality agent with money selects SHARE."""
        agent = self._setup_trait_agent(DeterministicRNG(seed=33))
        agent.traits.morality = 0.9
        agent.resources.money = 500

        actions: list[str] = []
        for seed in range(30):
            router = MockAIRouter(rng=DeterministicRNG(seed=seed))
            response = router.agent_decide("prompt", agent, world)
            data = json.loads(response)
            actions.append(data["action"])

        share_count = actions.count("share")
        assert share_count >= 3, (
            f"Expected SHARE >= 3/30 for moral agent, got {share_count}/30"
        )

    def test_mock_ai_amoral_steals(
        self, world: SimulationState
    ) -> None:
        """Low morality + high unlust selects STEAL."""
        agent = self._setup_trait_agent(DeterministicRNG(seed=44))
        agent.traits.morality = 0.2
        agent.unlust = 0.6
        agent.resources.money = 50
        agent.traits.anger_tendency = 0.5

        actions: list[str] = []
        for seed in range(30):
            router = MockAIRouter(rng=DeterministicRNG(seed=seed))
            response = router.agent_decide("prompt", agent, world)
            data = json.loads(response)
            actions.append(data["action"])

        steal_count = actions.count("steal")
        assert steal_count >= 3, (
            f"Expected STEAL >= 3/30 for amoral agent, got {steal_count}/30"
        )
