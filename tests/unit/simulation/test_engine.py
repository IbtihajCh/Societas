"""
Simulation Engine Unit Tests
=============================

Tests for the simulation engine core functionality.
"""

import pytest

from simulation.engine.simulation_engine import SimulationEngine
from simulation.engine.config import SimulationConfig
from simulation.engine.mock_ai_router import MockAIRouter
from shared.schemas.policy import Policy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.schemas.agent_state import AgentState
from shared.schemas.tick_result import TickResult
from shared.types.aliases import AgentId, PolicyId
from shared.types.enums import PolicyCategory


class TestSimulationEngine:
    """Tests for SimulationEngine class."""

    def test_engine_initialization(self):
        """Test engine can be initialized with default config."""
        engine = SimulationEngine()
        assert engine.is_running() is False
        assert engine.get_current_tick() == 0
        assert engine.config.population_size > 0
        assert isinstance(engine.get_state(), SimulationState)

    def test_engine_init_with_config(self):
        """Test engine can be initialized with custom config."""
        config = SimulationConfig(population_size=10, seed=99)
        engine = SimulationEngine(config)
        assert engine.config.population_size == 10
        assert engine.config.seed == 99

    def test_engine_start(self):
        """Test start() initializes agents and RNG."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        assert engine.is_running() is True
        assert len(engine.get_agents()) == 5
        assert engine._rng is not None

    def test_engine_tick_without_start(self):
        """Test that calling tick() before start() raises RuntimeError."""
        engine = SimulationEngine()
        with pytest.raises(RuntimeError, match="not started"):
            engine.tick()

    def test_engine_tick_after_start(self):
        """Test that tick() returns a valid TickResult after start()."""
        config = SimulationConfig(population_size=10, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        result = engine.tick()
        assert isinstance(result, TickResult)
        assert result.tick == 0
        assert result.state_hash != ""
        assert len(result.agent_actions) > 0

    def test_engine_tick_increments(self):
        """Test that successive ticks increment the tick number."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        result1 = engine.tick()
        assert result1.tick == 0
        result2 = engine.tick()
        assert result2.tick == 1
        assert engine.get_current_tick() == 2

    def test_engine_reset(self):
        """Test that reset() returns to initial clean state."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        engine.tick()  # Advance state
        engine.reset()
        assert engine.is_running() is False
        assert engine.get_current_tick() == 0
        assert len(engine.get_agents()) == 0
        assert engine._rng is None

    def test_engine_reset_with_seed(self):
        """Test reset() with a new seed updates config."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        engine.reset(seed=99)
        assert engine.config.seed == 99
        assert engine.get_current_tick() == 0
        assert engine.is_running() is False

    def test_engine_get_state(self):
        """Test that get_state() returns the current SimulationState."""
        engine = SimulationEngine()
        state = engine.get_state()
        assert isinstance(state, SimulationState)
        assert hasattr(state, "economy")

    def test_engine_get_agents(self):
        """Test that get_agents() returns list of agents after start."""
        config = SimulationConfig(population_size=3, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        agents = engine.get_agents()
        assert isinstance(agents, list)
        assert len(agents) == 3
        assert all(isinstance(a, AgentState) for a in agents)

    def test_engine_get_agent(self):
        """Test that get_agent() returns a specific agent by ID."""
        config = SimulationConfig(population_size=3, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        agent = engine.get_agent(AgentId("1"))
        assert agent is not None
        assert agent.id == AgentId("1")
        assert agent.is_alive is True

    def test_engine_get_agent_not_found(self):
        """Test that get_agent() returns None for non-existent ID."""
        engine = SimulationEngine()
        assert engine.get_agent(AgentId("nonexistent")) is None

    def test_engine_apply_policy(self):
        """Test that policies can be applied."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        policy = Policy(
            id=PolicyId("test-policy-001"),
            name="Test UBI Policy",
            category=PolicyCategory.ECONOMIC,
            weights=PolicyWeights(social_welfare=0.3),
        )
        engine.apply_policy(policy)
        active = engine._policy_engine.get_active_policies()
        assert len(active) == 1
        assert active[0].policy.id == PolicyId("test-policy-001")

    def test_engine_revoke_policy(self):
        """Test that policies can be revoked."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        policy = Policy(
            id=PolicyId("test-policy-002"),
            name="Test Tax Policy",
            category=PolicyCategory.ECONOMIC,
            weights=PolicyWeights(economic_freedom=-0.2),
        )
        engine.apply_policy(policy)
        assert len(engine._policy_engine.get_active_policies()) == 1
        engine.revoke_policy("test-policy-002")
        assert len(engine._policy_engine.get_active_policies()) == 0

    def test_engine_determinism(self):
        """Test that same seed produces identical state hashes."""
        config1 = SimulationConfig(population_size=5, seed=42)
        engine1 = SimulationEngine(config1)
        engine1.start()
        result1 = engine1.tick()

        config2 = SimulationConfig(population_size=5, seed=42)
        engine2 = SimulationEngine(config2)
        engine2.start()
        result2 = engine2.tick()

        assert result1.state_hash == result2.state_hash

    def test_engine_determinism_full_two_ticks(self):
        """Test determinism holds over multiple ticks."""
        config1 = SimulationConfig(population_size=5, seed=42)
        engine1 = SimulationEngine(config1)
        engine1.start()
        r1t1 = engine1.tick()
        r1t2 = engine1.tick()

        config2 = SimulationConfig(population_size=5, seed=42)
        engine2 = SimulationEngine(config2)
        engine2.start()
        r2t1 = engine2.tick()
        r2t2 = engine2.tick()

        assert r1t1.state_hash == r2t1.state_hash
        assert r1t2.state_hash == r2t2.state_hash

    def test_engine_tick_with_ai_router(self):
        """Test that tick with MockAIRouter records AI calls."""
        config = SimulationConfig(population_size=10, seed=42)
        engine = SimulationEngine(config)
        ai_router = MockAIRouter()
        engine.start(ai_router=ai_router)
        result = engine.tick()
        assert result.ai_calls > 0
        assert result.ambiguity_count >= 0

    def test_engine_tick_returns_metrics(self):
        """Test that tick duration is recorded."""
        config = SimulationConfig(population_size=5, seed=42)
        engine = SimulationEngine(config)
        engine.start()
        result = engine.tick()
        assert result.duration_ms >= 0


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    def test_register_agent(self, sample_agent_state):
        """Test agent can be registered."""
        # TODO: Implement after agent registry is complete
        pass

    def test_unregister_agent(self, sample_agent_state):
        """Test agent can be unregistered."""
        # TODO: Implement after agent registry is complete
        pass

    def test_get_agent(self, sample_agent_state):
        """Test agent can be retrieved by ID."""
        # TODO: Implement after agent registry is complete
        pass

    def test_get_all_agents(self):
        """Test all agents can be retrieved."""
        # TODO: Implement after agent registry is complete
        pass

    def test_agent_count(self):
        """Test agent count is accurate."""
        # TODO: Implement after agent registry is complete
        pass
