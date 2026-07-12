"""
Reputation System
=================

Manages agent reputation: decay, crime/good-act adjustments, gossip
propagation, rumor spreading, and self-esteem effects. All randomness uses DeterministicRNG.
"""

from typing import Dict

from shared.constants.defaults import (
    GOSSIP_SPREAD_CHANCE,
    REPUTATION_CRIME_PENALTY,
    REPUTATION_DECAY_RATE,
    REPUTATION_GOOD_BONUS,
    REPUTATION_KNOWN_DECAY,
    RUMOR_BFS_DEPTH,
    RUMOR_PROPAGATION_CHANCE,
)
from shared.schemas.agent_state import AgentState
from shared.types.enums import NeedType
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.action_executor import get_nearby_agents

__all__ = [
    "update_reputation",
    "spread_reputation",
    "reputation_effects",
    "apply_rumor_effects",
    "decay_rumors",
    "propagate_rumors",
]


def update_reputation(agent: AgentState, all_agents: list[AgentState]) -> None:
    """Update an agent's reputation for one tick.

    Three effects (applied in order on top of current reputation):
      1. Decay toward 0.5 at REPUTATION_DECAY_RATE.
      2. Crime penalty: lose REPUTATION_CRIME_PENALTY * min(crimes, 10) / 10.
      3. Good-acts bonus: gain REPUTATION_GOOD_BONUS * min(good_acts, 10) / 10.

    Args:
        agent: The agent whose reputation is being updated (modified in place).
        all_agents: All agents in the simulation (unused here, kept for API
                    consistency with the gossip method).
    """
    _ = all_agents  # unused
    current = agent.needs.get_level(NeedType.REPUTATION)

    # 1. Decay toward 0.5
    if current > 0.5:
        current = max(0.5, current - REPUTATION_DECAY_RATE)
    elif current < 0.5:
        current = min(0.5, current + REPUTATION_DECAY_RATE)

    # 2. Crime penalty (proportional, capped at 10 crimes)
    if agent.crimes_committed > 0:
        crime_factor = min(agent.crimes_committed, 10) / 10.0
        current -= REPUTATION_CRIME_PENALTY * crime_factor

    # 3. Good-acts bonus (proportional, capped at 10 acts)
    if agent.good_acts > 0:
        good_factor = min(agent.good_acts, 10) / 10.0
        current += REPUTATION_GOOD_BONUS * good_factor

    agent.needs.set_level(NeedType.REPUTATION, current)


def spread_reputation(
    agent: AgentState,
    all_agents: list[AgentState],
    rng: DeterministicRNG,
) -> None:
    """Gossip mechanic: nearby agents learn this agent's reputation.

    Each nearby agent has a GOSSIP_SPREAD_CHANCE to update their stored
    knowledge of this agent's reputation value.
    Known reputations are stored in ``agent.metadata["known_reputations"]``
    as a dict mapping other agent IDs to reputation values.

    Args:
        agent: The agent whose reputation is being gossiped about.
        all_agents: All agents in the simulation.
        rng: Deterministic RNG for the gossip probability roll.
    """
    agent_rep = agent.needs.get_level(NeedType.REPUTATION)
    nearby = get_nearby_agents(agent, all_agents)

    for other in nearby:
        if rng.random() < GOSSIP_SPREAD_CHANCE:
            if "known_reputations" not in other.metadata:
                other.metadata["known_reputations"] = {}
            # Decay existing known reputations before storing new one
            known = other.metadata["known_reputations"]
            for known_id in list(known.keys()):
                known[known_id] = max(0.0, known[known_id] - REPUTATION_KNOWN_DECAY)
            # Update knowledge of this agent
            known[agent.id] = agent_rep

    # Cleanup: remove dead agent entries from all known_reputations dicts.
    # This prevents indefinite accumulation of stale keys for agents that
    # have died during the simulation.
    alive_ids = {a.id for a in all_agents if a.is_alive}
    for other in all_agents:
        known = other.metadata.get("known_reputations")
        if known:
            for dead_id in list(known.keys()):
                if dead_id not in alive_ids:
                    del known[dead_id]


def reputation_effects(agent: AgentState) -> None:
    """Apply self-esteem adjustments based on current reputation.

    - Low reputation (< 0.3): reduces self_esteem by 0.01.
    - High reputation (> 0.7): boosts self_esteem by 0.005.
    - Gossip social proof: an agent's reputation is gently nudged toward
      the average of what nearby agents think of them (stored in
      ``agent.metadata["known_reputations"]``). This makes the gossip
      mechanic (spread_reputation) actually influence reputation rather
      than being a dead write.

    Args:
        agent: The agent to apply effects to (modified in place).
    """
    rep = agent.needs.get_level(NeedType.REPUTATION)
    current_se = agent.needs.get_level(NeedType.SELF_ESTEEM)

    if rep < 0.3:
        agent.needs.set_level(NeedType.SELF_ESTEEM, current_se - 0.01)
    elif rep > 0.7:
        agent.needs.set_level(NeedType.SELF_ESTEEM, current_se + 0.005)

    # Social-proof nudge: converge rep toward the **maximum** perception others
    # hold of this agent. Using max (not mean) makes this robust to the
    # known_reputations values decaying to 0 over time (REPUTATION_KNOWN_DECAY
    # in spread_reputation) — a 0 pulls the mean down but not the max.
    # 2% pull per tick keeps it gentle so individual deeds still matter
    # more than crowd opinion.
    known = agent.metadata.get("known_reputations") if hasattr(agent, "metadata") else None
    if known:
        perceptions = [v for v in known.values() if v is not None and v > 0.0]
        if perceptions:
            best_perception = max(perceptions)
            nudged = rep + 0.02 * (best_perception - rep)
            agent.needs.set_level(NeedType.REPUTATION, max(0.0, min(1.0, nudged)))


def apply_rumor_effects(
    rumors: dict, all_agents: list[AgentState]
) -> None:
    """Apply ongoing rumor penalties to target agents each tick.

    Each active rumor reduces its target's reputation by magnitude/10 per tick,
    spreading the total penalty evenly over the rumor's 10-tick lifetime.

    Args:
        rumors: Dict of active rumors from world.metadata["active_rumors"].
        all_agents: All agents in the simulation.
    """
    agents_by_id: dict[str, AgentState] = {a.id: a for a in all_agents if a.is_alive}
    for rumor in list(rumors.values()):
        target = agents_by_id.get(rumor["target_id"])
        if target is None:
            continue
        per_tick = rumor["magnitude"] / 10.0
        current_rep = target.needs.get_level(NeedType.REPUTATION)
        target.needs.set_level(NeedType.REPUTATION, max(0.0, current_rep - per_tick))


def decay_rumors(rumors: dict) -> None:
    """Reduce remaining_ticks on all rumors and remove expired ones.

    Args:
        rumors: Dict of active rumors (modified in place).
    """
    for rumor_id in list(rumors.keys()):
        rumors[rumor_id]["remaining_ticks"] -= 1
        if rumors[rumor_id]["remaining_ticks"] <= 0:
            del rumors[rumor_id]


def propagate_rumors(
    rumors: dict, all_agents: list[AgentState], rng: DeterministicRNG
) -> None:
    """Spread rumors through the social graph (BFS-limited).

    Each tick, agents who have heard a rumor may spread it to their social
    connections. Propagation is limited to RUMOR_BFS_DEPTH hops, and each
    connection has a RUMOR_PROPAGATION_CHANCE of hearing it per tick.

    Args:
        rumors: Dict of active rumors (modified in place).
        all_agents: All agents in the simulation.
        rng: Deterministic RNG for propagation probability checks.
    """
    agents_by_id: dict[str, AgentState] = {a.id: a for a in all_agents if a.is_alive}
    for rumor in list(rumors.values()):
        spread_depth: dict = rumor["spread_depth"]
        heard_by: list = rumor["heard_by"]
        # Collect agents who can still spread this rumor
        rumormongers = [
            aid
            for aid, depth in spread_depth.items()
            if depth < RUMOR_BFS_DEPTH and aid in agents_by_id
        ]
        for monger_id in rumormongers:
            monger = agents_by_id[monger_id]
            current_depth = spread_depth[monger_id]
            for conn_id in monger.social_connections:
                if conn_id in heard_by or conn_id not in agents_by_id:
                    continue
                if rng.random() < RUMOR_PROPAGATION_CHANCE:
                    heard_by.append(conn_id)
                    spread_depth[conn_id] = current_depth + 1
