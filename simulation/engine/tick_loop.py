"""Tick loop — the 10-step simulation tick that wires all modules together.

Steps:
1. Publish TickStartedEvent
2. Apply policy effects
3. Decay needs
4. Apply welfare + rent
5. Update emotions (unlust → happiness → sleep reset → state machine)
5b. Social systems — reputation update, gossip, reputation effects,
    community reclustering (every 10 ticks), community effects
6. Action selection + execution (staggered)
7. Movement
7b. Riot events check + trigger
8. Death check
9. World metrics update
10. State hash + TickCompletedEvent
"""

from collections import Counter
import time
from typing import Any

from shared.interfaces.i_ai_router import IAIRouter
from shared.schemas.agent_state import AgentState
from shared.schemas.policy import GovernmentPolicy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult, TickResult
from shared.types.aliases import TickNumber
from shared.types.enums import ActionType
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.action_executor import (
    compute_nearby_counts,
    execute_action,
    move_agent,
)
from simulation.agents.memory_system import collect_tick_memories
from simulation.agents.community_system import (
    community_effects,
    update_communities,
)
from simulation.agents.gang_system import (
    apply_gang_effects,
    process_gang_actions,
    try_form_gangs,
    update_gang_power,
)
from simulation.agents.decision_engine import (
    build_agent_prompt,
    build_moral_dilemma_prompt,
    deterministic_fallback,
    is_moral_dilemma,
    parse_llm_response,
    should_evaluate_this_tick,
    validate_action,
)
from simulation.agents.emotion_engine import (
    apply_sleep_reset,
    compute_happiness,
    update_emotion,
)
from simulation.agents.family_support import process_family_support
from simulation.agents.family_system import try_form_marriages
from simulation.agents.sibling_system import (
    maybe_sibling_support,
    update_sibling_dynamics,
)
from simulation.agents.lifecycle import try_birth
from simulation.agents.needs_calculator import (
    check_death,
    decay_needs,
    maybe_lose_job,
    progress_age,
    update_insomnia,
)
from simulation.agents.political_system import (
    process_political_influence,
    track_political_career,
)
from simulation.agents.purpose_system import (
    apply_self_actualization_effects,
    assign_purpose,
    check_self_actualization_death,
    update_purpose_fulfillment,
)
from simulation.agents.reputation_system import (
    apply_rumor_effects,
    decay_rumors,
    propagate_rumors,
    reputation_effects,
    spread_reputation,
    update_reputation,
)
from simulation.agents.unlust_engine import compute_unlust
from simulation.events.inter_community_conflict import (
    check_conflict_events,
    compute_community_tensions,
)
from simulation.events.riot_events import (
    check_riot_conditions,
    trigger_riot,
)
from simulation.policies.policy_effects import apply_all_policies
from simulation.world.economy import process_economy_tick, apply_debt_interest
from simulation.world.property_market import assign_initial_housing, update_property_market
from simulation.world.environmental_events import (
    apply_environmental_tick,
    environmental_effects_on_agents,
)
from simulation.world.metrics_calculator import (
    compute_state_hash,
    update_world_metrics,
)

__all__ = ["run_tick"]


def run_tick(
    tick_number: int,
    agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    policies: list[GovernmentPolicy] | None = None,
    ai_router: IAIRouter | None = None,
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
    living_agents.sort(key=lambda a: a.id)

    # Step 1: TickStartedEvent (logged, no event bus for now)
    # Step 2: Apply policy effects & aggregate weights
    if policies:
        apply_all_policies(living_agents, policies, world)

    # Compute aggregate policy weights and store in world metadata so that
    # the decision engine / action scoring can access them.
    if policies:
        total = PolicyWeights()
        for gp in policies:
            w = gp.policy_weights
            total.economic_freedom += w.economic_freedom
            total.social_welfare += w.social_welfare
            total.environmental_protection += w.environmental_protection
            total.public_order += w.public_order
            total.innovation += w.innovation
            total.cultural_preservation += w.cultural_preservation
        # Clamp to [-1, 1]
        total.economic_freedom = max(-1.0, min(1.0, total.economic_freedom))
        total.social_welfare = max(-1.0, min(1.0, total.social_welfare))
        total.environmental_protection = max(-1.0, min(1.0, total.environmental_protection))
        total.public_order = max(-1.0, min(1.0, total.public_order))
        total.innovation = max(-1.0, min(1.0, total.innovation))
        total.cultural_preservation = max(-1.0, min(1.0, total.cultural_preservation))
        world.metadata["aggregate_policy_weights"] = total
    elif "aggregate_policy_weights" in world.metadata:
        del world.metadata["aggregate_policy_weights"]

    # Step 2.5: Age progression (before needs decay so the updated age bracket
    #            is available for mortality checks later this tick)
    for agent in living_agents:
        progress_age(agent)

    # Step 3: Decay needs + environmental effects on agents
    for agent in living_agents:
        decay_needs(agent, world, rng)
        environmental_effects_on_agents(agent, world, rng)

    # Step 3a: Update insomnia for all living agents
    for agent in living_agents:
        update_insomnia(agent, world)

    # Step 3b: Environmental event processing
    new_env_events, remaining_events = apply_environmental_tick(
        world, tick_number, rng, world.active_env_events,
    )
    world.active_env_events = remaining_events
    env_event_ids: list[str] = [
        f"env_event:{e['type']}@tick={tick_number}"
        for e in new_env_events
    ]

    # 2.6 Marriage formation for eligible adults
    marriage_count = try_form_marriages(living_agents, rng, world)
    if marriage_count > 0:
        env_event_ids.append(f"marriage:tick={tick_number},count={marriage_count}")

    # Step 4: Apply welfare + rent + debt interest (includes labor market dynamics)
    process_economy_tick(living_agents, world, rng)
    apply_debt_interest(living_agents, world)

    # Step 4b: Property market
    property_changes = update_property_market(world, living_agents, rng)
    if property_changes.get("evictions", 0) > 0:
        env_event_ids.append(f"evictions:{property_changes['evictions']}")
    if property_changes.get("upgrades", 0) > 0:
        env_event_ids.append(f"property_upgrades:{property_changes['upgrades']}")

    # Step 5: Update emotions
    for agent in living_agents:
        agent.unlust = compute_unlust(agent)
        agent.emotions.happiness_score = compute_happiness(agent)
        apply_sleep_reset(agent)
        update_emotion(agent, rng)

    # Step 5a: Purpose/Meaning system (Maslow Layer 5)
    for agent in living_agents:
        assign_purpose(agent, rng)
        update_purpose_fulfillment(agent, agent.last_action, {}, rng)
        apply_self_actualization_effects(agent)

    # Step 5a.5: Political influence and career tracking
    for agent in living_agents:
        process_political_influence(agent, living_agents, world)
        track_political_career(agent, world)

    # Step 5b: Social systems — reputation, communities, rumors
    for agent in living_agents:
        update_reputation(agent, living_agents)
        spread_reputation(agent, living_agents, rng)
        reputation_effects(agent)

    # Rumor propagation, effect application, and decay
    rumors = world.metadata.get("active_rumors", {})
    propagate_rumors(rumors, living_agents, rng)
    apply_rumor_effects(rumors, living_agents)
    decay_rumors(rumors)
    world.metadata["active_rumors"] = rumors

    if tick_number % 10 == 0:
        update_communities(living_agents, rng)

    for agent in living_agents:
        community_effects(agent, living_agents)

    # Step 5b-collect: Collect episodic memories for all agents
    for agent in living_agents:
        collect_tick_memories(agent, None, world, tick_number)

    # Step 5b.5: Gang system — formation, actions, effects
    gangs = world.metadata.get("gangs", [])
    new_gangs = try_form_gangs(living_agents, rng, tick_number)
    gangs.extend(new_gangs)
    gang_events = process_gang_actions(gangs, living_agents, world, rng, tick_number)
    env_event_ids.extend(gang_events)
    update_gang_power(gangs)
    for agent in living_agents:
        apply_gang_effects(agent, gangs)
    world.metadata["gangs"] = gangs

    # Step 5c: Sibling dynamics
    for agent in living_agents:
        update_sibling_dynamics(agent, living_agents, rng)
        support_action = maybe_sibling_support(agent, living_agents, rng)
        if support_action:
            env_event_ids.append(f"sibling_{support_action}:{agent.id}")

    # Step 5d: Family support transactions
    support_count = process_family_support(living_agents, world, rng)
    if support_count > 0:
        env_event_ids.append(f"family_support:tick={tick_number},count={support_count}")

    # Step 6: Action selection + execution (staggered)
    action_results: list[AgentActionResult] = []
    llm_call_count = 0
    ambiguity_count = 0
    llm_log: list[dict[str, Any]] = []

    if ai_router and ai_router.is_available():
        # Pass 1: Collect prompts for all evaluating agents
        normal_prompts: list[tuple[int, str]] = []
        dilemma_prompts: list[tuple[int, str]] = []
        normal_agents: list[AgentState] = []
        dilemma_agents: list[AgentState] = []

        for idx, agent in enumerate(living_agents):
            maybe_lose_job(agent, rng, world)
            if not should_evaluate_this_tick(agent, tick_number):
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results.append(result)
                    collect_tick_memories(agent, result, world, tick_number)
                continue

            nearby_counts = compute_nearby_counts(agent, living_agents)
            if is_moral_dilemma(agent, world):
                ambiguity_count += 1
                prompt = build_moral_dilemma_prompt(agent, world, nearby_counts)
                dilemma_prompts.append((idx, prompt))
                dilemma_agents.append(agent)
            else:
                prompt = build_agent_prompt(agent, world, nearby_counts)
                normal_prompts.append((idx, prompt))
                normal_agents.append(agent)

        # Batch call: normal decisions → E2B
        normal_responses: list[str] = []
        if normal_prompts:
            normal_responses = ai_router.agent_decide_batch(
                [p for _, p in normal_prompts],
                normal_agents,
                world,
            )
            llm_call_count += len(normal_prompts)

        # Batch call: moral dilemmas → 26B A4B
        dilemma_responses: list[str] = []
        if dilemma_prompts:
            dilemma_responses = ai_router.moral_reasoning_batch(
                [p for _, p in dilemma_prompts],
                dilemma_agents,
                world,
            )
            llm_call_count += len(dilemma_prompts)

        # Pass 2: Execute actions from batched results
        action_results = [None] * len(living_agents)

        model_type = "agent_decide"
        for (idx, _), response in zip(normal_prompts, normal_responses):
            agent = living_agents[idx]
            parsed = parse_llm_response(response)
            if parsed:
                validated = validate_action(agent, parsed.get("action", ""), world)
                if validated:
                    action = validated
                    metadata = {
                        "source": "vllm_router",
                        "reasoning": parsed.get("reason", ""),
                        "feeling": parsed.get("feeling", ""),
                    }
                    if len(llm_log) < 50:
                        llm_log.append({
                            "tick": tick_number,
                            "agent_id": str(agent.id),
                            "model_type": model_type,
                            "action": str(validated),
                            "reason": str(parsed.get("reason", ""))[:200],
                            "feeling": str(parsed.get("feeling", ""))[:100],
                        })
                else:
                    action = deterministic_fallback(agent, world, rng)
                    metadata = {"source": "deterministic_fallback", "reasoning": "Invalid LLM action"}
            else:
                action = deterministic_fallback(agent, world, rng)
                metadata = {"source": "deterministic_fallback", "reasoning": "Unparseable LLM response"}
            result = execute_action(agent, action, world, living_agents, rng)
            result.metadata = metadata
            action_results[idx] = result
            collect_tick_memories(agent, result, world, tick_number)

        model_type = "moral_reasoning"
        for (idx, _), response in zip(dilemma_prompts, dilemma_responses):
            agent = living_agents[idx]
            parsed = parse_llm_response(response)
            if parsed:
                validated = validate_action(agent, parsed.get("action", ""), world)
                if validated:
                    action = validated
                    metadata = {
                        "source": "vllm_router",
                        "reasoning": parsed.get("reason", ""),
                        "feeling": parsed.get("feeling", ""),
                    }
                    if len(llm_log) < 50:
                        llm_log.append({
                            "tick": tick_number,
                            "agent_id": str(agent.id),
                            "model_type": model_type,
                            "action": str(validated),
                            "reason": str(parsed.get("reason", ""))[:200],
                            "feeling": str(parsed.get("feeling", ""))[:100],
                        })
                else:
                    action = deterministic_fallback(agent, world, rng)
                    metadata = {"source": "deterministic_fallback", "reasoning": "Invalid LLM action"}
            else:
                action = deterministic_fallback(agent, world, rng)
                metadata = {"source": "deterministic_fallback", "reasoning": "Unparseable LLM response"}
            result = execute_action(agent, action, world, living_agents, rng)
            result.metadata = metadata
            action_results[idx] = result
            collect_tick_memories(agent, result, world, tick_number)

        # Fill in skipped agents (non-evaluating)
        # NOTE: maybe_lose_job already called for all agents in Pass 1 above — do NOT duplicate.
        for idx, agent in enumerate(living_agents):
            if action_results[idx] is not None:
                continue
            if not should_evaluate_this_tick(agent, tick_number):
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results[idx] = result
                    collect_tick_memories(agent, result, world, tick_number)
            else:
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results[idx] = result
                    collect_tick_memories(agent, result, world, tick_number)

        action_results = [r for r in action_results if r is not None]

    else:
        # No AI router — deterministic fallback for all agents
        for idx, agent in enumerate(living_agents):
            maybe_lose_job(agent, rng, world)
            if not should_evaluate_this_tick(agent, tick_number):
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results.append(result)
                    collect_tick_memories(agent, result, world, tick_number)
                continue
            nearby_counts = compute_nearby_counts(agent, living_agents)
            if is_moral_dilemma(agent, world):
                ambiguity_count += 1
            action = deterministic_fallback(agent, world, rng)
            metadata = {"source": "deterministic_fallback", "reasoning": "No AI router"}
            result = execute_action(agent, action, world, living_agents, rng, tick_number)
            collect_tick_memories(agent, result, world, tick_number)
            result.metadata = metadata
            action_results.append(result)

    action_counts_result = Counter()
    for agent in living_agents:
        if hasattr(agent, 'last_action') and agent.last_action:
            action_counts_result[str(agent.last_action)] += 1
    result_action_counts = dict(action_counts_result)

    # Step 7: Movement
    for agent in living_agents:
        move_agent(agent, rng)

    # Step 7b: Riot events check
    if check_riot_conditions(world, agents):
        trigger_riot(agents, world, rng)
        env_event_ids.append(f"riot:tick={tick_number}")

    # Step 7c: Inter-community tension and conflict
    tensions = compute_community_tensions(living_agents, rng)
    conflict_events = check_conflict_events(tensions, living_agents, rng, tick_number)
    env_event_ids.extend(conflict_events)

    # Step 8: Death check
    for agent in living_agents:
        if check_death(agent, rng, world):
            agent.is_alive = False
        elif check_self_actualization_death(agent, rng):
            agent.is_alive = False

    # Step 8.5: Birth — eligible living agents may produce offspring
    new_agents: list[AgentState] = []
    for agent in agents:
        if agent.is_alive:
            child = try_birth(agent, agents, rng, tick_number)
            if child is not None:
                new_agents.append(child)
    agents.extend(new_agents)

    # Step 9: World metrics update
    update_world_metrics(world, agents)

    # Step 10: State hash + TickCompletedEvent
    # Media engine — generate news and apply effects
    from simulation.events.media_engine import process_media_tick
    news_articles = process_media_tick(world, tick_number, living_agents, rng)
    if news_articles:
        articles_list = world.media_state.setdefault("articles", [])
        articles_list.extend(
            [{"tick": a.tick, "headline": a.headline, "body": a.body, "category": a.category, "is_fake": a.is_fake} for a in news_articles]
        )
        # Keep only the last 200 articles to prevent unbounded growth
        while len(articles_list) > 200:
            articles_list.pop(0)
    env_event_ids.extend(
        f"news:{a.headline[:40]}" for a in news_articles
    )
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
            "food_availability": world.food_availability,
            "water_availability": world.water_availability,
        },
        events_generated=env_event_ids,
        action_counts=result_action_counts,
        llm_log=llm_log,
        ambiguity_count=ambiguity_count,
        ai_calls=llm_call_count,
        duration_ms=duration_ms,
        state_hash=state_hash,
    )
