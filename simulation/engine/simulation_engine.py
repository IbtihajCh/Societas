"""
Simulation Engine
=================

Main simulation engine implementation.
"""

from typing import List, Optional

from shared.types.aliases import AgentId, TickNumber
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.metrics import SimulationMetrics
from shared.schemas.tick_result import TickResult
from shared.schemas.policy import Policy
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.utilities.deterministic_rng import DeterministicRNG
from shared.constants.defaults import DEFAULT_SIMULATION_SEED

from simulation.engine.config import SimulationConfig
from simulation.agents.agent_registry import AgentRegistry
from simulation.agents.agent_factory import create_initial_population
from simulation.world.world_state import WorldStateManager
from simulation.policies.policy_engine import PolicyEngine
from simulation.metrics.metrics_collector import MetricsCollector
from simulation.events.event_bus import EventBus
from simulation.scheduler.tick_scheduler import TickScheduler
from models.router.vllm_router import VLLMRouter
from simulation.engine.tick_loop import run_tick


class SimulationEngine(ISimulationEngine):
    """
    Main simulation engine for SOCIETAS.
    
    Coordinates all simulation subsystems and manages the tick loop.
    Implements deterministic execution with seeded RNG.
    
    Attributes:
        config: Simulation configuration
        _current_tick: Current tick number
        _is_running: Whether simulation is running
        _agent_registry: Registry of all agents
        _world_state: World state manager
        _policy_engine: Policy application engine
        _metrics_collector: Metrics collection system
        _event_bus: Event publishing system
        _tick_scheduler: Tick execution scheduler
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize the simulation engine.
        
        Args:
            config: Simulation configuration. Uses defaults if None.
        """
        self.config = config or SimulationConfig()
        self._current_tick = TickNumber(0)
        self._is_running = False
        
        # Initialize subsystems
        self._agent_registry = AgentRegistry()
        self._world_state = WorldStateManager()
        self._policy_engine = PolicyEngine()
        self._metrics_collector = MetricsCollector()
        self._event_bus = EventBus()
        self._tick_scheduler = TickScheduler()
        
        # Runtime state (initialized by start())
        self._rng: Optional[DeterministicRNG] = None
        self._ai_router: Optional[VLLMRouter] = None
        self._agents: list[AgentState] = []
    
    def start(self, ai_router: Optional[VLLMRouter] = None) -> None:
        """Initialize the simulation with agents and world state.
        
        Must be called before tick(). Creates the initial population,
        seeds the RNG, and optionally connects an AI router.
        
        Args:
            ai_router: Optional mock AI router for LLM-driven decisions.
        """
        seed = self.config.seed if self.config.seed is not None else DEFAULT_SIMULATION_SEED
        self._rng = DeterministicRNG(seed=seed)
        self._ai_router = ai_router
        self._agents = create_initial_population(
            n_agents=self.config.population_size,
            rng=self._rng,
        )
        self._is_running = True
    
    def set_ai_router(self, router: VLLMRouter) -> None:
        """Set or replace the AI router for LLM-driven decisions.
        
        Args:
            router: The mock AI router instance.
        """
        self._ai_router = router
    
    def stop(self) -> None:
        """
        Stop the simulation execution.
        """
        self._is_running = False

    def tick(self) -> TickResult:
        """
        Advance the simulation by one tick.
        
        Delegates to run_tick() from tick_loop.py which implements
        the 10-step tick: policy effects, needs decay, economy, emotions,
        action selection+execution, movement, death, metrics, state hash.
        
        Returns:
            TickResult containing all changes and events from the tick
            
        Raises:
            RuntimeError: If the simulation has not been started via start().
        """
        if not self._is_running or self._rng is None:
            raise RuntimeError("Simulation not started. Call start() first.")
        
        result = run_tick(
            tick_number=int(self._current_tick),
            agents=self._agents,
            world=self._world_state.get_state(),
            rng=self._rng,
            policies=self._policy_engine.get_active_policies(),
            ai_router=self._ai_router,
        )
        
        self._current_tick = TickNumber(self._current_tick + 1)
        self._metrics_collector.record_tick(self._current_tick, {"tick": result.tick, "duration_ms": result.duration_ms})
        return result
    
    def reset(self, seed: Optional[int] = None) -> None:
        """
        Reset the simulation to initial state.
        
        Args:
            seed: Optional random seed for deterministic replay
        """
        self._current_tick = TickNumber(0)
        self._is_running = False
        self._agent_registry.clear()
        self._world_state.reset()
        self._policy_engine = PolicyEngine()
        self._metrics_collector.reset()
        self._event_bus.clear_history()
        self._tick_scheduler.reset()
        self._rng = None
        self._ai_router = None
        self._agents = []
        if seed is not None:
            self.config = SimulationConfig(seed=seed)
    
    def apply_policy(self, policy: Policy) -> None:
        """
        Apply a government policy to the simulation.
        
        Args:
            policy: The policy to apply
            
        TODO: Implement policy application
            - Register policy with policy engine
            - Calculate policy effects
            - Publish PolicyEnactedEvent
        """
        self._policy_engine.apply_policy(policy)
    
    def revoke_policy(self, policy_id: str) -> None:
        """
        Revoke an active government policy.
        
        Args:
            policy_id: ID of the policy to revoke
            
        TODO: Implement policy revocation
            - Remove policy from policy engine
            - Recalculate effects
        """
        self._policy_engine.revoke_policy(policy_id)
    
    def get_state(self) -> SimulationState:
        """
        Get the current world state.
        
        Returns:
            Current SimulationState
        """
        return self._world_state.get_state()
    
    def get_metrics(self) -> SimulationMetrics:
        """
        Get aggregated simulation metrics.
        
        Returns:
            Current SimulationMetrics
        """
        return self._metrics_collector.get_metrics()
    
    def get_agent(self, agent_id: AgentId) -> Optional[AgentState]:
        """
        Get the state of a specific agent.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            AgentState if found, None otherwise
        """
        for agent in self._agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def get_agents(self) -> List[AgentState]:
        """
        Get all active agents.
        
        Returns:
            List of all active AgentState objects
        """
        return list(self._agents)
    
    def get_current_tick(self) -> TickNumber:
        """
        Get the current tick number.
        
        Returns:
            Current TickNumber
        """
        return self._current_tick
    
    def is_running(self) -> bool:
        """
        Check if the simulation is currently running.
        
        Returns:
            True if running, False otherwise
        """
        return self._is_running
