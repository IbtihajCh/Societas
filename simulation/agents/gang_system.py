"""
Gang System — Organized Crime Gangs
====================================

Implements organized crime gangs: formation, recruitment, actions (extortion,
rival fights, protection), power/notoriety tracking, and per-agent effects.
All randomness uses DeterministicRNG.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from shared.constants.defaults import (
    GANG_EXTORT_AMOUNT,
    GANG_FORMATION_MIN_MEMBERS,
    GANG_FORMATION_PROBABILITY,
    GANG_MAX_NAME_LENGTH,
    GANG_POWER_MEMBER_WEIGHT,
    GANG_POWER_WEALTH_WEIGHT,
    GANG_RECRUIT_BASE_CHANCE,
    GRID_SIZE,
    INTERACTION_RADIUS,
)
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.aliases import AgentId
from shared.types.enums import NeedType, WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.action_executor import get_nearby_agents

__all__ = [
    "GangState",
    "try_form_gangs",
    "try_recruit",
    "process_gang_actions",
    "update_gang_power",
    "apply_gang_effects",
]

_GANG_NAMES = [
    "Crimson Serpents", "Iron Fists", "Shadow Syndicate",
    "Blood Wolves", "Night Vipers", "Dusk Reapers",
    "Rust Raiders", "Ashen Vultures", "Bone Collectors",
    "Dark Emissaries",
]


@dataclass
class GangState:
    """State for a single organized crime gang.

    Attributes:
        id: Unique gang identifier.
        name: Human-readable gang name.
        leader_id: AgentId of the gang leader.
        member_ids: List of agent IDs belonging to this gang.
        territory: Grid coordinates approximating gang territory.
        wealth: Collective gang wealth (accumulated from extortion, etc.).
        power: Gang power score (computed from wealth + member count).
        notoriety: Criminal notoriety (0.0 to 1.0).
        formed_tick: Tick number when the gang was formed.
    """

    id: str
    name: str
    leader_id: AgentId
    member_ids: List[AgentId] = field(default_factory=list)
    territory: List[Tuple[int, int]] = field(default_factory=list)
    wealth: float = 0.0
    power: float = 1.0
    notoriety: float = 0.0
    formed_tick: int = 0


def _toroidal_distance(x1: int, y1: int, x2: int, y2: int, grid_size: int) -> float:
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    dx = min(dx, grid_size - dx)
    dy = min(dy, grid_size - dy)
    return (dx * dx + dy * dy) ** 0.5


def _is_eligible_for_gang(agent: AgentState) -> bool:
    return (
        agent.is_alive
        and agent.unlust > 0.6
        and agent.traits.morality < 0.3
        and agent.wealth_class == WealthClass.POOR
    )


def _find_proximity_clusters(candidates: List[AgentState]) -> List[List[AgentState]]:
    """Cluster eligible agents by grid proximity (INTERACTION_RADIUS)."""
    if not candidates:
        return []
    clusters: List[List[AgentState]] = []
    assigned: set[str] = set()
    for seed in candidates:
        if seed.id in assigned:
            continue
        cluster: List[AgentState] = [seed]
        assigned.add(seed.id)
        changed = True
        while changed:
            changed = False
            for other in candidates:
                if other.id in assigned:
                    continue
                for member in cluster:
                    dist = _toroidal_distance(
                        int(member.grid_x), int(member.grid_y),
                        int(other.grid_x), int(other.grid_y),
                        GRID_SIZE,
                    )
                    if dist <= INTERACTION_RADIUS:
                        cluster.append(other)
                        assigned.add(other.id)
                        changed = True
                        break
        clusters.append(cluster)
    return clusters


def _pick_gang_name(existing_names: set[str]) -> str:
    for name in _GANG_NAMES:
        if name not in existing_names:
            return name
    return f"Gang-{len(existing_names)}"[:GANG_MAX_NAME_LENGTH]


def try_form_gangs(
    agents: List[AgentState],
    rng: DeterministicRNG,
    tick_number: int,
) -> List[GangState]:
    """Form gangs from eligible agents.

    Eligible: high unlust (>0.6), low morality (<0.3), POOR wealth class.
    Agents are clustered by grid proximity; clusters with 5+ members may
    form a gang based on GANG_FORMATION_PROBABILITY.

    Args:
        agents: All agents in the simulation.
        rng: Deterministic RNG.
        tick_number: Current tick number.

    Returns:
        List of newly formed GangState objects.
    """
    eligible = [a for a in agents if _is_eligible_for_gang(a)]
    clusters = _find_proximity_clusters(eligible)
    new_gangs: List[GangState] = []
    existing_names: set[str] = set()
    for cluster in clusters:
        if len(cluster) < GANG_FORMATION_MIN_MEMBERS:
            continue
        if rng.random() >= GANG_FORMATION_PROBABILITY:
            continue
        rng.shuffle(cluster)
        leader = cluster[0]
        gang_id = f"gang_{tick_number}_{len(new_gangs)}"
        name = _pick_gang_name(existing_names)
        existing_names.add(name)
        territory = [(int(a.grid_x), int(a.grid_y)) for a in cluster[:3]]
        gang = GangState(
            id=gang_id,
            name=name,
            leader_id=leader.id,
            member_ids=[a.id for a in cluster],
            territory=territory,
            wealth=sum(a.resources.money for a in cluster) * 0.1,
            power=1.0,
            notoriety=0.0,
            formed_tick=tick_number,
        )
        for a in cluster:
            a.metadata["gang_id"] = gang_id
        new_gangs.append(gang)
    return new_gangs


def try_recruit(
    agent: AgentState,
    gangs: List[GangState],
    all_agents: List[AgentState],
    rng: DeterministicRNG,
) -> Optional[str]:
    """Attempt to recruit a marginalized agent into a nearby gang.

    Eligible: POOR wealth class, unlust > 0.6, not already in a gang.
    Recruitment chance is GANG_RECRUIT_BASE_CHANCE.

    Args:
        agent: The agent to potentially recruit.
        gangs: All existing gangs.
        all_agents: All agents in the simulation.
        rng: Deterministic RNG.

    Returns:
        The gang ID if recruited, None otherwise.
    """
    if not agent.is_alive:
        return None
    if agent.wealth_class != WealthClass.POOR:
        return None
    if agent.unlust <= 0.6:
        return None
    if "gang_id" in agent.metadata:
        return None
    nearby = get_nearby_agents(agent, all_agents)
    nearby_gangs: List[GangState] = []
    for gang in gangs:
        for member_id in gang.member_ids:
            member = next((a for a in nearby if a.id == member_id), None)
            if member is not None:
                nearby_gangs.append(gang)
                break
    if not nearby_gangs:
        return None
    target = nearby_gangs[int(rng.choice(len(nearby_gangs)))]
    if rng.random() < GANG_RECRUIT_BASE_CHANCE:
        target.member_ids.append(agent.id)
        agent.metadata["gang_id"] = target.id
        return target.id
    return None


def process_gang_actions(
    gangs: List[GangState],
    agents: List[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    tick_number: int,
) -> List[str]:
    """Execute per-tick gang actions.

    Each gang performs one action per tick:
    - Extort (40%): Take money from a nearby non-member agent.
    - Fight (30%): Attack a nearby rival gang; losing side loses a member.
    - Protect (30%): Shield members from crime detection.

    Args:
        gangs: All existing gangs.
        agents: All agents in the simulation.
        world: World state (for context).
        rng: Deterministic RNG.
        tick_number: Current tick number.

    Returns:
        List of event ID strings for this tick.
    """
    _ = world
    event_ids: List[str] = []
    for gang in gangs:
        if not gang.member_ids:
            continue
        action_roll = rng.random()
        if action_roll < 0.4:
            victims: List[AgentState] = []
            for agent in agents:
                if not agent.is_alive:
                    continue
                if "gang_id" in agent.metadata and agent.metadata["gang_id"] == gang.id:
                    continue
                for member_id in gang.member_ids:
                    member = next((a for a in agents if a.id == member_id and a.is_alive), None)
                    if member is None:
                        continue
                    dist = _toroidal_distance(
                        int(member.grid_x), int(member.grid_y),
                        int(agent.grid_x), int(agent.grid_y),
                        GRID_SIZE,
                    )
                    if dist <= INTERACTION_RADIUS:
                        victims.append(agent)
                        break
            if victims:
                target = victims[int(rng.choice(len(victims)))]
                amount = min(target.resources.money, GANG_EXTORT_AMOUNT)
                target.resources.money -= amount
                target.resources.wealth = target.resources.money
                gang.wealth += amount
                gang.notoriety = min(1.0, gang.notoriety + 0.02)
                event_ids.append(f"gang_extort:{gang.id}->{target.id}@tick={tick_number}")
        elif action_roll < 0.7:
            for other_gang in gangs:
                if other_gang.id == gang.id:
                    continue
                if not other_gang.member_ids:
                    continue
                in_proximity = False
                for gid in gang.member_ids:
                    g_member = next((a for a in agents if a.id == gid and a.is_alive), None)
                    if g_member is None:
                        continue
                    for oid in other_gang.member_ids:
                        o_member = next((a for a in agents if a.id == oid and a.is_alive), None)
                        if o_member is None:
                            continue
                        dist = _toroidal_distance(
                            int(g_member.grid_x), int(g_member.grid_y),
                            int(o_member.grid_x), int(o_member.grid_y),
                            GRID_SIZE,
                        )
                        if dist <= INTERACTION_RADIUS:
                            in_proximity = True
                            break
                    if in_proximity:
                        break
                if in_proximity:
                    if rng.random() < 0.5:
                        if other_gang.member_ids:
                            removed = other_gang.member_ids.pop(
                                int(rng.choice(len(other_gang.member_ids)))
                            )
                            for a in agents:
                                if a.id == removed:
                                    a.metadata.pop("gang_id", None)
                                    break
                            gang.notoriety = min(1.0, gang.notoriety + 0.05)
                            event_ids.append(
                                f"gang_fight:{gang.id}->{other_gang.id}@tick={tick_number}"
                            )
                    else:
                        if gang.member_ids:
                            removed = gang.member_ids.pop(
                                int(rng.choice(len(gang.member_ids)))
                            )
                            for a in agents:
                                if a.id == removed:
                                    a.metadata.pop("gang_id", None)
                                    break
                            other_gang.notoriety = min(1.0, other_gang.notoriety + 0.05)
                            event_ids.append(
                                f"gang_fight:{other_gang.id}->{gang.id}@tick={tick_number}"
                            )
                    break
        else:
            for member_id in gang.member_ids:
                member = next((a for a in agents if a.id == member_id and a.is_alive), None)
                if member is not None and member.crimes_committed > 0:
                    member.metadata["gang_protected"] = True
                    event_ids.append(f"gang_protect:{gang.id}->{member_id}@tick={tick_number}")
    return event_ids


def update_gang_power(gangs: List[GangState]) -> None:
    """Update power and notoriety for all gangs.

    Power = wealth * GANG_POWER_WEALTH_WEIGHT + len(members) * GANG_POWER_MEMBER_WEIGHT.
    Notoriety increases with crimes committed by members (tracked via action events).

    Args:
        gangs: All existing gangs (modified in place).
    """
    for gang in gangs:
        gang.power = (
            gang.wealth * GANG_POWER_WEALTH_WEIGHT
            + len(gang.member_ids) * GANG_POWER_MEMBER_WEIGHT
        )


def apply_gang_effects(agent: AgentState, gangs: List[GangState]) -> None:
    """Apply per-tick effects for agents who belong to a gang.

    Effects:
    - Safety boost (+0.02)
    - Crime immunity for small crimes (1 or fewer) via metadata flag
    - Reputation loss with non-gang agents (-0.005)

    Args:
        agent: The agent to apply effects to (modified in place).
        gangs: All existing gangs.
    """
    if "gang_id" not in agent.metadata:
        return
    gang_id = agent.metadata["gang_id"]
    gang = next((g for g in gangs if g.id == gang_id), None)
    if gang is None:
        return
    safety = agent.needs.get_level(NeedType.SAFETY)
    agent.needs.set_level(NeedType.SAFETY, safety + 0.02)
    if agent.crimes_committed <= 1:
        agent.metadata["gang_crime_immunity"] = True
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep - 0.005)
