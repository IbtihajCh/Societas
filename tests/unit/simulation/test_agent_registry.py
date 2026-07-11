"""
Agent Registry Unit Tests
=========================

Tests for the AgentRegistry class covering registration, lookup,
iteration, lifecycle management, and determinism.
"""

import pytest

from shared.types.aliases import AgentId
from simulation.agents.agent import Agent
from simulation.agents.agent_registry import AgentRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> AgentRegistry:
    """An empty registry."""
    return AgentRegistry()


@pytest.fixture
def agent_a() -> Agent:
    """Agent with id 'agent-a'."""
    return Agent(AgentId("agent-a"))


@pytest.fixture
def agent_b() -> Agent:
    """Agent with id 'agent-b'."""
    return Agent(AgentId("agent-b"))


def _dead_agent(aid: str = "dead-agent") -> Agent:
    """Create an agent that is already dead."""
    agent = Agent(AgentId(aid))
    agent.get_state().is_alive = False
    return agent


# ===========================================================================
# Registration
# ===========================================================================

class TestRegisterAgent:
    """Tests for register_agent."""

    def test_register_single(self, registry: AgentRegistry, agent_a: Agent) -> None:
        """A single agent can be registered."""
        registry.register_agent(agent_a)
        assert registry.get_agent_count() == 1

    def test_register_multiple(
        self, registry: AgentRegistry, agent_a: Agent, agent_b: Agent,
    ) -> None:
        """Multiple agents can be registered."""
        registry.register_agent(agent_a)
        registry.register_agent(agent_b)
        assert registry.get_agent_count() == 2

    def test_register_overwrites(self, registry: AgentRegistry) -> None:
        """Registering the same ID again overwrites."""
        a1 = Agent(AgentId("dup"))
        a2 = Agent(AgentId("dup"))
        registry.register_agent(a1)
        registry.register_agent(a2)
        assert registry.get_agent_count() == 1
        # The state returned should be from a2
        state = registry.get_agent(AgentId("dup"))
        assert state is not None


# ===========================================================================
# Unregistration
# ===========================================================================

class TestUnregisterAgent:
    """Tests for unregister_agent."""

    def test_unregister_existing(
        self, registry: AgentRegistry, agent_a: Agent,
    ) -> None:
        """An existing agent can be unregistered."""
        registry.register_agent(agent_a)
        registry.unregister_agent(AgentId("agent-a"))
        assert registry.get_agent_count() == 0
        assert registry.get_agent(AgentId("agent-a")) is None

    def test_unregister_nonexistent(self, registry: AgentRegistry) -> None:
        """Unregistering a non-existent agent does not raise."""
        registry.unregister_agent(AgentId("ghost"))
        assert registry.get_agent_count() == 0

    def test_unregister_one_of_many(
        self, registry: AgentRegistry, agent_a: Agent, agent_b: Agent,
    ) -> None:
        """Unregistering one agent leaves the other intact."""
        registry.register_agent(agent_a)
        registry.register_agent(agent_b)
        registry.unregister_agent(AgentId("agent-a"))
        assert registry.get_agent_count() == 1
        assert registry.get_agent(AgentId("agent-b")) is not None


# ===========================================================================
# Lookup
# ===========================================================================

class TestGetAgent:
    """Tests for get_agent."""

    def test_get_returns_state(self, registry: AgentRegistry) -> None:
        """get_agent returns the AgentState, not the Agent."""
        agent = Agent(AgentId("lookup-me"))
        registry.register_agent(agent)
        state = registry.get_agent(AgentId("lookup-me"))
        assert state is not None
        assert state.id == AgentId("lookup-me")
        assert state.is_alive is True

    def test_get_nonexistent(self, registry: AgentRegistry) -> None:
        """get_agent on unknown ID returns None."""
        assert registry.get_agent(AgentId("nobody")) is None

    def test_get_after_unregister(
        self, registry: AgentRegistry, agent_a: Agent,
    ) -> None:
        """After unregister, get_agent returns None."""
        registry.register_agent(agent_a)
        registry.unregister_agent(AgentId("agent-a"))
        assert registry.get_agent(AgentId("agent-a")) is None


# ===========================================================================
# get_all_agents
# ===========================================================================

class TestGetAllAgents:
    """Tests for get_all_agents."""

    def test_get_all_empty(self, registry: AgentRegistry) -> None:
        """Empty registry returns empty list."""
        assert registry.get_all_agents() == []

    def test_get_all_returns_states(
        self, registry: AgentRegistry, agent_a: Agent, agent_b: Agent,
    ) -> None:
        """get_all_agents returns AgentState objects."""
        registry.register_agent(agent_a)
        registry.register_agent(agent_b)
        states = registry.get_all_agents()
        assert len(states) == 2
        assert all(s.id in {AgentId("agent-a"), AgentId("agent-b")} for s in states)

    def test_get_all_excludes_dead(self, registry: AgentRegistry) -> None:
        """Dead agents are excluded from get_all_agents."""
        alive = Agent(AgentId("alive"))
        dead = _dead_agent("dead")
        registry.register_agent(alive)
        registry.register_agent(dead)
        states = registry.get_all_agents()
        assert len(states) == 1
        assert states[0].id == AgentId("alive")

    def test_get_all_all_dead(self, registry: AgentRegistry) -> None:
        """When all agents are dead, get_all_agents returns empty list."""
        registry.register_agent(_dead_agent("d1"))
        registry.register_agent(_dead_agent("d2"))
        assert registry.get_all_agents() == []


# ===========================================================================
# Count & clear
# ===========================================================================

class TestCountAndClear:
    """Tests for get_agent_count and clear."""

    def test_count_initial(self, registry: AgentRegistry) -> None:
        """Initial count is zero."""
        assert registry.get_agent_count() == 0

    def test_count_after_register(
        self, registry: AgentRegistry, agent_a: Agent,
    ) -> None:
        """Count increments after registration."""
        registry.register_agent(agent_a)
        assert registry.get_agent_count() == 1

    def test_clear_removes_all(
        self, registry: AgentRegistry, agent_a: Agent, agent_b: Agent,
    ) -> None:
        """Clear removes all agents."""
        registry.register_agent(agent_a)
        registry.register_agent(agent_b)
        registry.clear()
        assert registry.get_agent_count() == 0
        assert registry.get_all_agents() == []

    def test_clear_empty(self, registry: AgentRegistry) -> None:
        """Clearing an empty registry does not raise."""
        registry.clear()
        assert registry.get_agent_count() == 0
