"""Family support — parent/child financial support during each tick."""

from typing import List

from shared.constants.defaults import (
    CHILD_ELDERLY_SUPPORT,
    PARENT_EDUCATION_SUPPORT,
    SUPPORT_FAMILY_EDUCATION_AGE_MAX,
    SUPPORT_FAMILY_PARENT_AGE_MIN,
    SUPPORT_FAMILY_PROBABILITY,
    SUPPORT_FAMILY_UNLUST_RELIEF,
)
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.aliases import AgentId, EventId
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "process_family_support",
    "get_living_parents",
    "get_living_children",
]


def get_living_parents(
    agent: AgentState,
    all_agents: List[AgentState],
) -> List[AgentState]:
    """Return living parent agents for the given agent.

    Args:
        agent: The child agent.
        all_agents: All agents in the simulation.

    Returns:
        List of living parent AgentState objects.
    """
    if not agent.parent_ids:
        return []
    living: List[AgentState] = []
    parent_id_set = set(agent.parent_ids)
    for other in all_agents:
        if other.id in parent_id_set and other.is_alive:
            living.append(other)
    return living


def get_living_children(
    agent: AgentState,
    all_agents: List[AgentState],
) -> List[AgentState]:
    """Return living child agents for the given agent.

    Args:
        agent: The parent agent.
        all_agents: All agents in the simulation.

    Returns:
        List of living child AgentState objects.
    """
    if not agent.children_ids:
        return []
    living: List[AgentState] = []
    child_id_set = set(agent.children_ids)
    for other in all_agents:
        if other.id in child_id_set and other.is_alive:
            living.append(other)
    return living


def process_family_support(
    agents: List[AgentState],
    world_state: SimulationState,
    rng: DeterministicRNG,
) -> int:
    """Process family support transactions for all agents this tick.

    Two directions of support:

    1. **Education support** — parents send money to children who are
       still within the education age bracket (age <
       ``SUPPORT_FAMILY_EDUCATION_AGE_MAX``).
    2. **Elderly support** — adult children send money to elderly parents
       (both parent and child must meet age thresholds).

    Each eligible transaction occurs with probability
    ``SUPPORT_FAMILY_PROBABILITY`` per tick and requires the paying party
    to have more than 20 money. Both parties receive a small unlust
    relief per transaction.

    Args:
        agents: All agents (living and dead) — used to look up family
            relationships.
        world_state: Current world state (used for event logging).
        rng: Deterministic RNG.

    Returns:
        Number of support transactions that occurred this tick.
    """
    transaction_count = 0
    events: List[EventId] = []

    for agent in agents:
        if not agent.is_alive:
            continue

        # --- Education support: parent -> child ---
        if agent.age < SUPPORT_FAMILY_EDUCATION_AGE_MAX:
            parents = get_living_parents(agent, agents)
            for parent in parents:
                if parent.resources.money > 20 and rng.random() < SUPPORT_FAMILY_PROBABILITY:
                    parent.resources.money -= PARENT_EDUCATION_SUPPORT
                    parent.resources.wealth = parent.resources.money
                    agent.resources.money += PARENT_EDUCATION_SUPPORT
                    agent.resources.wealth = agent.resources.money

                    parent.support_given += PARENT_EDUCATION_SUPPORT
                    agent.support_received += PARENT_EDUCATION_SUPPORT

                    parent.unlust = max(0.0, parent.unlust - SUPPORT_FAMILY_UNLUST_RELIEF)
                    agent.unlust = max(0.0, agent.unlust - SUPPORT_FAMILY_UNLUST_RELIEF)

                    transaction_count += 1
                    events.append(EventId(f"family_support_education:{agent.id}<-{parent.id}"))

        # --- Elderly support: child -> parent ---
        if agent.age >= SUPPORT_FAMILY_PARENT_AGE_MIN:
            parents = get_living_parents(agent, agents)
            eligible_parents = [
                p for p in parents
                if p.age >= SUPPORT_FAMILY_PARENT_AGE_MIN
            ]
            for parent in eligible_parents:
                if agent.resources.money > 20 and rng.random() < SUPPORT_FAMILY_PROBABILITY:
                    agent.resources.money -= CHILD_ELDERLY_SUPPORT
                    agent.resources.wealth = agent.resources.money
                    parent.resources.money += CHILD_ELDERLY_SUPPORT
                    parent.resources.wealth = parent.resources.money

                    agent.support_given += CHILD_ELDERLY_SUPPORT
                    parent.support_received += CHILD_ELDERLY_SUPPORT

                    agent.unlust = max(0.0, agent.unlust - SUPPORT_FAMILY_UNLUST_RELIEF)
                    parent.unlust = max(0.0, parent.unlust - SUPPORT_FAMILY_UNLUST_RELIEF)

                    transaction_count += 1
                    events.append(EventId(f"family_support_elderly:{agent.id}->{parent.id}"))

    world_state.metadata["family_support_count"] = transaction_count
    if events:
        existing = world_state.metadata.get("family_support_events", [])
        world_state.metadata["family_support_events"] = existing + events

    return transaction_count
