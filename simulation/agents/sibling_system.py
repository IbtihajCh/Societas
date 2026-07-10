"""Sibling relationships system — birth linking, dynamics, and support.

Provides functions to link siblings at birth, update sibling dynamics
(jealousy, bond) each tick, and trigger supportive behaviour between
close siblings.
"""

from typing import List, Optional

from shared.constants.defaults import (
    SIBLING_AFFECT_UNLUST_WEIGHT,
    SIBLING_BOND_DECREASE_RATE,
    SIBLING_BOND_INCREASE_RATE,
    SIBLING_JEALOUSY_DECAY_RATE,
    SIBLING_JEALOUSY_SUCCESS_WEIGHT,
    SIBLING_JEALOUSY_WEALTH_WEIGHT,
    SIBLING_SUPPORT_PROBABILITY,
)
from shared.schemas.agent_state import AgentState
from shared.types.aliases import AgentId
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "link_siblings_at_birth",
    "update_sibling_dynamics",
    "maybe_sibling_support",
]


def link_siblings_at_birth(
    new_agent: AgentState,
    parents: list[AgentId],
    existing_children: list[AgentState],
) -> list[AgentId]:
    """Link a newborn agent with existing siblings sharing the same parents.

    Scans *existing_children* for agents whose ``metadata['parent_ids']``
    match the given *parents*.  Each existing sibling gets the new agent
    added to its ``siblings`` list and vice versa.

    Args:
        new_agent: The newly created agent (modified in place).
        parents: List of parent AgentIds (e.g. ``[mother_id, father_id]``).
        existing_children: All agents in the simulation (only living agents
            with matching parent IDs are considered).

    Returns:
        List of sibling AgentIds that were linked.
    """
    parent_set = set(parents)
    sibling_ids: list[AgentId] = []

    for candidate in existing_children:
        if candidate.id == new_agent.id:
            continue
        if set(candidate.parent_ids) == parent_set:
            candidate.siblings.append(new_agent.id)
            sibling_ids.append(candidate.id)

    new_agent.siblings = list(sibling_ids)
    return sibling_ids


def update_sibling_dynamics(
    agent: AgentState,
    all_agents: list[AgentState],
    rng: DeterministicRNG,
) -> None:
    """Update jealousy and bond for an agent against each living sibling.

    For every living sibling the agent has:

    - If wealth disparity > 50 % **or** notoriety disparity > 0.3,
      *sibling_jealousy* increases.
    - If both wealth disparity < 10 % and notoriety disparity < 0.1,
      *sibling_bond* increases (similar status).
    - If extreme disparity exists, *sibling_bond* decreases.
    - Jealousy is decayed unconditionally each tick.
    - ``sibling_jealousy * SIBLING_AFFECT_UNLUST_WEIGHT`` is added to
      ``agent.unlust``.

    Args:
        agent: The agent being updated (modified in place).
        all_agents: All agents (used to look up sibling objects by ID).
        rng: Deterministic RNG (reserved for future use).
    """
    if not agent.siblings:
        agent.sibling_jealousy = max(
            0.0, agent.sibling_jealousy - SIBLING_JEALOUSY_DECAY_RATE
        )
        return

    sibling_objs = [a for a in all_agents if a.id in agent.siblings and a.is_alive]
    if not sibling_objs:
        agent.sibling_jealousy = max(
            0.0, agent.sibling_jealousy - SIBLING_JEALOUSY_DECAY_RATE
        )
        return

    max_jealousy_delta = 0.0
    for sibling in sibling_objs:
        wealth_diff = abs(agent.resources.money - sibling.resources.money) / max(
            agent.resources.money, sibling.resources.money, 1
        )
        success_diff = abs(agent.notoriety - sibling.notoriety)

        if wealth_diff > 0.5 or success_diff > 0.3:
            delta = (
                wealth_diff * SIBLING_JEALOUSY_WEALTH_WEIGHT
                + success_diff * SIBLING_JEALOUSY_SUCCESS_WEIGHT
            )
            max_jealousy_delta = max(max_jealousy_delta, delta)
            agent.sibling_bond = max(0.0, agent.sibling_bond - SIBLING_BOND_DECREASE_RATE)

        if wealth_diff < 0.1 and success_diff < 0.1:
            agent.sibling_bond = min(1.0, agent.sibling_bond + SIBLING_BOND_INCREASE_RATE)

    agent.sibling_jealousy = min(
        1.0, agent.sibling_jealousy + max_jealousy_delta
    )
    agent.sibling_jealousy = max(
        0.0, agent.sibling_jealousy - SIBLING_JEALOUSY_DECAY_RATE
    )

    agent.unlust = min(
        1.0, agent.unlust + agent.sibling_jealousy * SIBLING_AFFECT_UNLUST_WEIGHT
    )


def maybe_sibling_support(
    agent: AgentState,
    all_agents: list[AgentState],
    rng: DeterministicRNG,
) -> Optional[str]:
    """Attempt supportive actions toward close siblings.

    For each living sibling with ``sibling_bond > 0.6``, there is a
    ``SIBLING_SUPPORT_PROBABILITY`` (5 %) chance per tick that the agent
    will either share money (if the sibling has substantially less) or
    console them (improve emotional state).

    Args:
        agent: The agent potentially providing support (modified in place).
        all_agents: All agents (used to look up sibling objects by ID).
        rng: Deterministic RNG for the probability roll.

    Returns:
        ``"shared_money"``, ``"consoled_sibling"``, or ``None``.
    """
    if not agent.siblings:
        return None

    sibling_objs = [a for a in all_agents if a.id in agent.siblings and a.is_alive]
    for sibling in sibling_objs:
        if sibling.sibling_bond > 0.6 and rng.random() < SIBLING_SUPPORT_PROBABILITY:
            if (
                sibling.resources.money < agent.resources.money * 0.5
                and agent.resources.money > 10
            ):
                gift = agent.resources.money * 0.1
                agent.resources.money -= gift
                sibling.resources.money += gift
                agent.good_acts += 1
                return "shared_money"
            else:
                sibling.emotions.happiness_score = min(
                    1.0, sibling.emotions.happiness_score + 0.05
                )
                return "consoled_sibling"

    return None
