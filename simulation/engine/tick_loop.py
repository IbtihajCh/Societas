"""Tick loop — the 10-step simulation tick that wires all modules together.

Steps:
1. Publish TickStartedEvent
2. Apply policy effects
3. Decay needs
4. Apply welfare + rent
5. Update emotions (unlust → happiness → sleep reset → state machine)
6. Action selection + execution (staggered)
7. Movement
8. Death check
9. World metrics update
10. State hash + TickCompletedEvent
"""

import time
from typing import Any

from shared.types.aliases import TickNumber
from shared.types.enums import ActionType, EmotionType
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult, TickResult
from shared.schemas.policy import GovernmentPolicy
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.needs_calculator import decay_needs, check_death, maybe_lose_job
from simulation.agents.unlust_engine import compute_unlust
from simulation.agents.emotion_engine import (
    compute_happiness,
    update_emotion,
    apply_sleep_reset,
)
from simulation.agents.decision_engine import (
    should_evaluate_this_tick,
    build_agent_prompt,
    build_moral_dilemma_prompt,
    is_moral_dilemma,
    parse_llm_response,
    validate_action,
    deterministic_fallback,
)
from simulation.agents.action_executor import (
    execute_action,
    compute_nearby_counts,
    move_agent,
)
from simulation.world.economy import process_economy_tick
from simulation.world.metrics_calculator import (
    update_world_metrics,
    compute_state_hash,
)
from simulation.policies.policy_effects import apply_all_policies
from models.router.vllm_router import VLLMRouter

__all__ = ["run_tick"]


def run_tick(
    tick_number: int,
    agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    policies: list[GovernmentPolicy] | None = None,
    ai_router: VLLMRouter | None = None,
) -> TickResult:
    """Execute one complete simulation tick.

    Args:
        tick_number: Current tick number.
        agents: All agents (living and dead).
        world: World state (modified in place).
        rng: Deterministic RNG.
        policies: Active government policies.
        ai_router: AI router for LLM calls (None = deterministic fallback only).

    Returns:
        TickResult with all actions, events, and metrics from this tick.
    """
    start_time = time.time()
    living_agents = [a for a in agents if a.is_alive]

    # Step 1: TickStartedEvent (logged, no event bus for now)
    # Step 2: Apply policy effects
    if policies:
        apply_all_policies(living_agents, policies, world)

    # Step 3: Decay needs
    for agent in living_agents:
        decay_needs(agent, world, rng)

    # Step 4: Apply welfare + rent
    process_economy_tick(living_agents, world)

    # Step 5: Update emotions
    for agent in living_agents:
        agent.unlust = compute_unlust(agent)
        agent.emotions.happiness_score = compute_happiness(agent)
        apply_sleep_reset(agent)
        update_emotion(agent, rng)

    # Step 6: Action selection + execution (staggered)
    action_results: list[AgentActionResult] = []
    llm_call_count = 0
    ambiguity_count = 0

    for agent in living_agents:
        # Probabilistic job loss before action selection
        maybe_lose_job(agent, rng)

        if not should_evaluate_this_tick(agent, tick_number):
            # Continue last action
            if agent.last_action != ActionType.IDLE:
                result = execute_action(
                    agent, agent.last_action, world, living_agents, rng
                )
                action_results.append(result)
            continue

        nearby_counts = compute_nearby_counts(agent, living_agents)

        # Determine action
        action: ActionType
        metadata: dict[str, Any] = {}

        if ai_router and ai_router.is_available():
            # Check for moral dilemma
            if is_moral_dilemma(agent, world):
                ambiguity_count += 1
                prompt = build_moral_dilemma_prompt(agent, world, nearby_counts)
                response = ai_router.moral_reasoning(prompt, agent, world)
                llm_call_count += 1
            else:
                prompt = build_agent_prompt(agent, world, nearby_counts)
                response = ai_router.agent_decide(prompt, agent, world)
                llm_call_count += 1

            parsed = parse_llm_response(response)
            if parsed:
                validated = validate_action(agent, parsed.get("action", ""), world)
                if validated:
                    action = validated
                    metadata = {
                        "source": "mock_ai_router",
                        "reasoning": parsed.get("reason", ""),
                        "feeling": parsed.get("feeling", ""),
                    }
                else:
                    action = deterministic_fallback(agent, world, rng)
                    metadata = {
                        "source": "deterministic_fallback",
                        "reasoning": "Invalid LLM action",
                    }
            else:
                action = deterministic_fallback(agent, world, rng)
                metadata = {
                    "source": "deterministic_fallback",
                    "reasoning": "Unparseable LLM response",
                }
        else:
            action = deterministic_fallback(agent, world, rng)
            metadata = {"source": "deterministic_fallback", "reasoning": "No AI router"}

        result = execute_action(agent, action, world, living_agents, rng)
        result.metadata = metadata
        action_results.append(result)

    # Step 7: Movement
    for agent in living_agents:
        move_agent(agent, rng)

    # Step 8: Death check
    for agent in living_agents:
        if check_death(agent, rng):
            agent.is_alive = False

    # Step 9: World metrics update
    update_world_metrics(world, agents)

    # Step 10: State hash + TickCompletedEvent
    state_hash = compute_state_hash(world, agents)
    duration_ms = (time.time() - start_time) * 1000.0

    return TickResult(
        tick=TickNumber(tick_number),
        agent_actions=action_results,
        state_changes={
            "crime_rate": world.crime_rate,
            "protest_intensity": world.protest_intensity,
            "unemployment_rate": world.unemployment_rate,
            "avg_unlust": world.unlust,
            "population": float(world.population),
        },
        events_generated=[],
        ambiguity_count=ambiguity_count,
        ai_calls=llm_call_count,
        duration_ms=duration_ms,
        state_hash=state_hash,
    )
