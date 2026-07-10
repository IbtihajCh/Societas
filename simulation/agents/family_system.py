"""Marriage and family formation system for SOCIETAS.

Provides functions for forming marriages between eligible agents,
spouse lookup, and marriage status checks.
"""

from typing import Optional

from shared.constants.defaults import (
    GRID_SIZE,
    MARRIAGE_AGE_MAX,
    MARRIAGE_AGE_MIN,
    MARRIAGE_BASE_PROBABILITY,
    MARRIAGE_GRID_PROXIMITY,
    MARRIAGE_MAX_AGE_GAP,
    MARRIAGE_WEALTH_COMPAT,
)
from shared.schemas.agent_state import AgentState
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "try_form_marriages",
    "get_spouse",
    "are_married",
]


def _grid_distance(a: AgentState, b: AgentState) -> int:
    """Chebyshev distance on a toroidal grid."""
    dx = abs(int(a.grid_x) - int(b.grid_x))
    dy = abs(int(a.grid_y) - int(b.grid_y))
    dx = min(dx, GRID_SIZE - dx)
    dy = min(dy, GRID_SIZE - dy)
    return max(dx, dy)


def _is_eligible_for_marriage(agent: AgentState) -> bool:
    """Check if an agent is eligible for marriage."""
    if not agent.is_alive:
        return False
    if agent.spouse is not None:
        return False
    if agent.age < MARRIAGE_AGE_MIN or agent.age > MARRIAGE_AGE_MAX:
        return False
    return True


def _wealth_compatible(a: AgentState, b: AgentState) -> bool:
    """Check if two agents are wealth-compatible for marriage."""
    if a.resources.money <= 0 and b.resources.money <= 0:
        return True
    max_wealth = max(a.resources.money, b.resources.money)
    min_wealth = min(a.resources.money, b.resources.money)
    if max_wealth <= 0:
        return True
    ratio = min_wealth / max_wealth if max_wealth > 0 else 1.0
    return ratio >= (1.0 - MARRIAGE_WEALTH_COMPAT)


def try_form_marriages(
    agents: list[AgentState],
    rng: DeterministicRNG,
    world_state: object = None,
) -> int:
    """Attempt to form marriages between eligible unmarried agents.

    Iterates over young-adult and middle-adult agents and attempts to pair
    them based on compatibility (age, wealth, proximity) with a per-tick
    probability.

    Args:
        agents: List of living agents (modified in place).
        rng: Deterministic RNG for probability rolls.
        world_state: Unused, reserved for future context (e.g. cultural norms).

    Returns:
        Number of new marriages formed this tick.
    """
    eligible = [a for a in agents if _is_eligible_for_marriage(a)]

    rng.shuffle(eligible)

    married_set: set[str] = set()
    marriage_count = 0

    for i, agent in enumerate(eligible):
        if str(agent.id) in married_set:
            continue

        candidates: list[AgentState] = []
        for j, other in enumerate(eligible):
            if i == j:
                continue
            if str(other.id) in married_set:
                continue
            if other.gender == agent.gender:
                continue
            if abs(agent.age - other.age) > MARRIAGE_MAX_AGE_GAP:
                continue
            if not _wealth_compatible(agent, other):
                continue
            if _grid_distance(agent, other) > MARRIAGE_GRID_PROXIMITY:
                continue
            if other.id in agent.enemies or agent.id in other.enemies:
                continue
            candidates.append(other)

        if not candidates:
            continue

        if rng.random() < MARRIAGE_BASE_PROBABILITY:
            partner = candidates[int(rng.choice(len(candidates)))]

            family_id = f"family_{min(agent.id, partner.id)}_{max(agent.id, partner.id)}"

            agent.spouse = partner.id
            partner.spouse = agent.id
            agent.family_id = family_id
            partner.family_id = family_id
            agent.marriage_tick = 0
            partner.marriage_tick = 0

            married_set.add(str(agent.id))
            married_set.add(str(partner.id))
            marriage_count += 1

    return marriage_count


def get_spouse(agent: AgentState, agents: list[AgentState]) -> Optional[AgentState]:
    """Look up the spouse of an agent in the agents list.

    Args:
        agent: The agent whose spouse to find.
        agents: All agents in the simulation.

    Returns:
        The spouse AgentState, or None if unmarried or spouse not found.
    """
    if agent.spouse is None:
        return None
    for other in agents:
        if other.id == agent.spouse and other.is_alive:
            return other
    return None


def are_married(a: AgentState, b: AgentState) -> bool:
    """Check if two agents are married to each other.

    Args:
        a: First agent.
        b: Second agent.

    Returns:
        True if a.spouse == b.id and b.spouse == a.id.
    """
    return a.spouse is not None and a.spouse == b.id and b.spouse is not None and b.spouse == a.id
