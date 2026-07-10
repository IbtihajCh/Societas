"""
Riot Events
===========

Riot detection, triggering, and protest escalation mechanics.
All randomness uses DeterministicRNG.
"""

from shared.constants.defaults import (
    RIOT_FOOD_THRESHOLD,
    RIOT_JOIN_CHANCE,
    RIOT_PROTEST_THRESHOLD,
    RIOT_UNLUST_THRESHOLD,
)
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import ActionType, EmotionType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.action_executor import get_nearby_agents

__all__ = [
    "check_riot_conditions",
    "trigger_riot",
    "escalate_protests",
]


def check_riot_conditions(
    world: SimulationState,
    agents: list[AgentState],
) -> bool:
    """Check whether riot conditions are met this tick.

    Conditions (both must hold):
      - ``world.protest_intensity > RIOT_PROTEST_THRESHOLD``
      - ``world.unlust > RIOT_UNLUST_THRESHOLD`` **OR**
        ``world.food_availability < RIOT_FOOD_THRESHOLD``

    Args:
        world: Current world state.
        agents: All agents (used only for future extensibility).

    Returns:
        True if both conditions are satisfied.
    """
    _ = agents  # reserved for future extensibility
    if world.protest_intensity <= RIOT_PROTEST_THRESHOLD:
        return False
    return (
        world.unlust > RIOT_UNLUST_THRESHOLD
        or world.food_availability < RIOT_FOOD_THRESHOLD
    )


def trigger_riot(
    agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
) -> list[dict]:
    """Execute a riot event.

    Effects:
      - 30% of agents with ``protest_count > 0`` join the riot (random
        selection).
      - ``world.food_availability`` is reduced by 0.05.
      - ``world.crime_rate`` is increased by 0.02.
      - Participating agents have ``trust_in_govt`` reduced by 0.1.
      - Random nearby (non-participating) agents have their safety need
        reduced by 0.15.

    Args:
        agents: All agents in the simulation (modified in place).
        world: Current world state (modified in place).
        rng: Deterministic RNG for random selection.

    Returns:
        List of event dicts for logging, each containing:
          - ``"event_type"``: ``"riot"``
          - ``"participants"``: list of participating agent IDs
          - ``"food_availability_delta"``: -0.05
          - ``"crime_rate_delta"``: 0.02
    """
    # Select participants: 30% of agents with protest_count > 0
    eligible = [a for a in agents if a.is_alive and a.protest_count > 0]
    rng.shuffle(eligible)
    num_join = max(1, int(len(eligible) * RIOT_JOIN_CHANCE))
    participants = eligible[:num_join]

    participant_ids: list[str] = []

    for agent in participants:
        agent.trust_in_govt = max(0.0, agent.trust_in_govt - 0.1)
        participant_ids.append(agent.id)

        # Nearby non-participating agents get safety reduced
        nearby = get_nearby_agents(agent, agents)
        for nb in nearby:
            if nb in participants:
                continue
            if rng.random() < 0.5:  # 50% chance per nearby agent
                safety_val = nb.needs.get_level(NeedType.SAFETY)
                nb.needs.set_level(NeedType.SAFETY, safety_val - 0.15)

    # World-level damage
    world.food_availability = max(0.0, world.food_availability - 0.05)
    world.crime_rate = min(1.0, world.crime_rate + 0.02)

    return [
        {
            "event_type": "riot",
            "participants": participant_ids,
            "food_availability_delta": -0.05,
            "crime_rate_delta": 0.02,
        }
    ]


def escalate_protests(
    agent: AgentState,
    nearby_counts: dict,
) -> bool:
    """Check if a nearby crowd of protesters triggers an angry agent to join.

    If ``nearby_counts["protesters"] > 3`` and the agent's primary emotion
    is ANGRY, the agent joins the protest (sets ``last_action`` to PROTEST
    and increments ``protest_count``).

    Args:
        agent: The agent to evaluate (modified in place if escalation occurs).
        nearby_counts: Dict from ``compute_nearby_counts`` with at least
                       a ``"protesters"`` key.

    Returns:
        True if the agent escalated to protest, False otherwise.
    """
    if nearby_counts.get("protesters", 0) > 3 and agent.emotions.primary == EmotionType.ANGRY:
        agent.protest_count += 1
        agent.last_action = ActionType.PROTEST
        return True
    return False
