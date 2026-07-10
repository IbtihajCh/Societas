"""
Community System
================

Handles community formation (grid-proximity + social-connection clustering),
per-tick community effects (social connection boost, preferred befriending
targets), and community norm enforcement (witness effects on crime).

All randomness uses DeterministicRNG.
"""

from shared.constants.defaults import (
    COMMUNITY_MAX_SIZE,
    COMMUNITY_MIN_SIZE,
    LEADER_REPUTATION_GAIN,
    LEADER_SAFETY_BONUS,
)
from shared.schemas.agent_state import AgentState
from shared.types.enums import JobType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.action_executor import get_nearby_agents

__all__ = [
    "get_community_members",
    "update_communities",
    "community_effects",
    "enforce_community_norms",
]


def get_community_members(
    agent: AgentState,
    all_agents: list[AgentState],
) -> list[AgentState]:
    """Return all living agents sharing the same community_id (excluding self).

    Args:
        agent: The agent whose community to look up.
        all_agents: All agents in the simulation.

    Returns:
        List of living community members (excluding self).
    """
    if agent.community_id is None:
        return []
    return [
        a for a in all_agents
        if a.is_alive
        and a.id != agent.id
        and a.community_id == agent.community_id
    ]


def update_communities(
    all_agents: list[AgentState],
    rng: DeterministicRNG,
) -> None:
    """Recluster living agents into communities based on proximity and social
    connections.

    Communities are groups of ``COMMUNITY_MIN_SIZE`` to ``COMMUNITY_MAX_SIZE``
    agents within ``INTERACTION_RADIUS`` who share at least one social
    connection.

    Uses simple greedy BFS clustering (not complex graph algorithms):
      1. Clear all existing community IDs.
      2. For each unassigned agent, BFS out to nearby agents that share a
         social connection.
      3. If the cluster size >= ``COMMUNITY_MIN_SIZE``, assign a community ID.

    Args:
        all_agents: All agents in the simulation (modified in place).
        rng: Deterministic RNG for deterministic ordering.
    """
    _ = rng  # deterministic via sort-by-id, not stochastic

    # Clear existing communities
    for agent in all_agents:
        if agent.is_alive:
            agent.community_id = None

    living = [a for a in all_agents if a.is_alive]

    # Sort by ID for deterministic tie-breaking
    living.sort(key=lambda a: a.id)

    cluster_id = 0
    unassigned: set[str] = {a.id for a in living}

    for seed_agent in living:
        if seed_agent.id not in unassigned:
            continue

        # Greedy BFS
        queue: list[AgentState] = [seed_agent]
        cluster: list[AgentState] = []
        visited: set[str] = set()

        while queue and len(cluster) < COMMUNITY_MAX_SIZE:
            current = queue.pop(0)
            if current.id in visited:
                continue
            visited.add(current.id)

            if current.id in unassigned:
                cluster.append(current)
                unassigned.discard(current.id)

            if len(cluster) >= COMMUNITY_MAX_SIZE:
                break

            nearby = get_nearby_agents(current, all_agents)
            for nb in nearby:
                # Must share at least one social connection and be unassigned
                if (
                    nb.id not in visited
                    and nb.id in unassigned
                    and (nb.id in current.social_connections or current.id in nb.social_connections)
                ):
                    queue.append(nb)

        if len(cluster) >= COMMUNITY_MIN_SIZE:
            cid = f"community_{cluster_id}"
            cluster_id += 1
            for a in cluster:
                a.community_id = cid


def community_effects(
    agent: AgentState,
    all_agents: list[AgentState],
) -> None:
    """Apply per-tick community effects to an agent.

    - Agents in the same community get a small social connection boost
      (+0.005 per tick).
    - If any community member is a COMMUNITY_LEADER, the agent receives a
      safety bonus (+LEADER_SAFETY_BONUS per tick).
    - Community leaders gain +LEADER_REPUTATION_GAIN reputation per tick.
    - Community members are noted in metadata as preferred befriending targets
      (``agent.metadata["community_befriend_targets"]`` list).

    Args:
        agent: The agent to apply effects to (modified in place).
        all_agents: All agents in the simulation.
    """
    members = get_community_members(agent, all_agents)
    if not members:
        # Remove stale metadata
        agent.metadata.pop("community_befriend_targets", None)
        return

    # Social connection boost
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.005)

    # Record preferred targets for befriending
    agent.metadata["community_befriend_targets"] = [m.id for m in members]

    # Community leader effects
    leader_present = any(
        m.job_type == JobType.COMMUNITY_LEADER for m in members
    ) or agent.job_type == JobType.COMMUNITY_LEADER
    if leader_present:
        safety = agent.needs.get_level(NeedType.SAFETY)
        agent.needs.set_level(NeedType.SAFETY, safety + LEADER_SAFETY_BONUS)

    if agent.job_type == JobType.COMMUNITY_LEADER:
        rep = agent.needs.get_level(NeedType.REPUTATION)
        agent.needs.set_level(NeedType.REPUTATION, rep + LEADER_REPUTATION_GAIN)


def enforce_community_norms(
    agent: AgentState,
    community_members: list[AgentState],
) -> None:
    """Check if any community member witnessed a crime committed by the agent
    this tick and apply consequences.

    A witness is a community member who is nearby on the grid (using basic
    proximity - they're already in the same community cluster so they're
    assumed to be relatively close).

    Effects on witnesses:
      - ``trust_in_govt`` drops slightly (by 0.02).
      - If the witness has aggressive traits, their chance of reporting
        is reduced (simulated via a "crime_reporting_chance" metadata flag
        set to a lower value).

    Args:
        agent: The agent who may have committed a crime.
        community_members: Other members of the same community (potential
                          witnesses). Not modified; effects are applied
                          directly to the witnessing agents.
    """
    if agent.crimes_committed <= 0:
        return

    # Each community member who is nearby is a witness
    for member in community_members:
        if member.id == agent.id:
            continue
        if not member.is_alive:
            continue

        # Distrust effect
        member.trust_in_govt = max(0.0, member.trust_in_govt - 0.02)

        # Mark reduced crime-reporting willingness
        report_chance = member.metadata.get(
            "crime_reporting_chance", 1.0
        )
        member.metadata["crime_reporting_chance"] = max(
            0.0, report_chance - 0.05
        )
