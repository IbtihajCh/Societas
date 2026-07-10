"""
Inter-Community Conflict
========================

Tracks and resolves inter-community tension and conflict events.
All randomness uses DeterministicRNG.
"""

from math import sqrt
from typing import Dict, List

from shared.constants.defaults import (
    CONFLICT_GANG_RECRUIT_THRESHOLD,
    CONFLICT_HATE_CRIME_THRESHOLD,
    CONFLICT_PROPERTY_DAMAGE_THRESHOLD,
    GRID_SIZE,
    TENSION_BASE_DECAY,
    TENSION_PROXIMITY_WEIGHT,
    TENSION_WEALTH_GAP_WEIGHT,
)
from shared.schemas.agent_state import AgentState
from shared.types.enums import NeedType
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "check_conflict_events",
    "compute_community_tensions",
    "get_community_stats",
    "resolve_tension_decay",
]


def get_community_stats(
    agents: List[AgentState],
) -> Dict[str, Dict]:
    """Compute per-community statistics from the agent list.

    Args:
        agents: All living agents with community_id set.

    Returns:
        Dict mapping community_id to a dict with keys:
            size, avg_wealth, avg_morality, avg_unlust, centroid (x, y).
    """
    communities: Dict[str, Dict] = {}

    for agent in agents:
        cid = agent.community_id
        if cid is None:
            continue
        if cid not in communities:
            communities[cid] = {
                "size": 0,
                "total_wealth": 0.0,
                "total_morality": 0.0,
                "total_unlust": 0.0,
                "sum_x": 0,
                "sum_y": 0,
            }
        stats = communities[cid]
        stats["size"] += 1
        stats["total_wealth"] += agent.resources.wealth
        stats["total_morality"] += agent.traits.morality
        stats["total_unlust"] += agent.unlust
        stats["sum_x"] += agent.grid_x
        stats["sum_y"] += agent.grid_y

    result: Dict[str, Dict] = {}
    for cid, raw in communities.items():
        s = raw["size"]
        result[cid] = {
            "size": s,
            "avg_wealth": raw["total_wealth"] / s,
            "avg_morality": raw["total_morality"] / s,
            "avg_unlust": raw["total_unlust"] / s,
            "centroid": (raw["sum_x"] / s, raw["sum_y"] / s),
        }
    return result


def _toroidal_distance(
    x1: float, y1: float, x2: float, y2: float, grid_size: int
) -> float:
    """Compute Euclidean distance on a toroidal grid.

    Args:
        x1, y1: First point coordinates.
        x2, y2: Second point coordinates.
        grid_size: Size of the grid (assumed square, both dimensions equal).

    Returns:
        Euclidean distance respecting toroidal wrap-around.
    """
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    if dx > grid_size / 2:
        dx = grid_size - dx
    if dy > grid_size / 2:
        dy = grid_size - dy
    return sqrt(dx * dx + dy * dy)


def compute_community_tensions(
    agents: List[AgentState],
    rng: DeterministicRNG,
) -> Dict[str, Dict[str, float]]:
    """Compute a tension matrix between all community pairs.

    Factors considered:
      - Wealth disparity between communities.
      - Population ratio (size imbalance).
      - Grid proximity (closer communities have more interaction potential).

    Args:
        agents: All living agents with community_id set.
        rng: Deterministic RNG (reserved for future stochastic factors).

    Returns:
        Nested dict: ``tensions[c_a][c_b]`` = tension score in [0, 1].
    """
    _ = rng  # reserved for future stochastic factors

    stats = get_community_stats(agents)
    community_ids = list(stats.keys())

    # Pre-compute max distance for normalization
    max_dist = _toroidal_distance(0, 0, GRID_SIZE / 2, GRID_SIZE / 2, GRID_SIZE)

    tensions: Dict[str, Dict[str, float]] = {}
    for cid in community_ids:
        tensions[cid] = {}

    pop_weight = 1.0 - TENSION_WEALTH_GAP_WEIGHT - TENSION_PROXIMITY_WEIGHT

    for i, c_a in enumerate(community_ids):
        for j, c_b in enumerate(community_ids):
            if i >= j:
                continue

            sa = stats[c_a]
            sb = stats[c_b]

            # Wealth disparity (normalized difference)
            max_w = max(sa["avg_wealth"], sb["avg_wealth"], 1.0)
            wealth_gap = abs(sa["avg_wealth"] - sb["avg_wealth"]) / max_w

            # Population ratio tension
            pop_ratio = min(sa["size"], sb["size"]) / max(sa["size"], sb["size"], 1)
            pop_tension = 1.0 - pop_ratio

            # Proximity (closer = more interaction potential -> more tension)
            dist = _toroidal_distance(
                sa["centroid"][0], sa["centroid"][1],
                sb["centroid"][0], sb["centroid"][1],
                GRID_SIZE,
            )
            proximity = 1.0 - (dist / max_dist) if max_dist > 0 else 0.0

            tension = (
                wealth_gap * TENSION_WEALTH_GAP_WEIGHT
                + pop_tension * pop_weight
                + proximity * TENSION_PROXIMITY_WEIGHT
            )
            tension = max(0.0, min(1.0, tension))

            tensions[c_a][c_b] = tension
            tensions[c_b][c_a] = tension

    return tensions


def check_conflict_events(
    tensions: Dict[str, Dict[str, float]],
    agents: List[AgentState],
    rng: DeterministicRNG,
    tick_number: int,
) -> List[str]:
    """Check if any community pair exceeds conflict thresholds and trigger events.

    Event types (by tension threshold):
      - Gang recruitment (``> CONFLICT_GANG_RECRUIT_THRESHOLD``).
      - Property damage / vandalism (``> CONFLICT_PROPERTY_DAMAGE_THRESHOLD``).
      - Hate crimes (``> CONFLICT_HATE_CRIME_THRESHOLD``).

    Args:
        tensions: Tension matrix from ``compute_community_tensions``.
        agents: All living agents (modified in place by conflict effects).
        rng: Deterministic RNG for probabilistic event triggers.
        tick_number: Current tick number (used for event ID generation).

    Returns:
        List of event ID strings describing triggered events.
    """
    events: List[str] = []

    community_ids = list(tensions.keys())
    if len(community_ids) < 2:
        return events

    # Build a lookup for agents by community
    agents_by_community: Dict[str, List[AgentState]] = {}
    for agent in agents:
        cid = agent.community_id
        if cid is not None:
            agents_by_community.setdefault(cid, []).append(agent)

    for i, c_a in enumerate(community_ids):
        for j, c_b in enumerate(community_ids):
            if i >= j:
                continue
            tension = tensions.get(c_a, {}).get(c_b, 0.0)

            # --- Gang recruitment (lowest threshold) ---
            if tension > CONFLICT_GANG_RECRUIT_THRESHOLD and rng.random() < 0.15:
                source_pool = agents_by_community.get(c_a, [])
                target_pool = agents_by_community.get(c_b, [])
                if source_pool and target_pool:
                    rng.shuffle(source_pool)
                    recruits = source_pool[:max(1, len(source_pool) // 3)]
                    for rec in recruits:
                        rec.metadata["gang_recruit"] = True
                        rec.metadata["gang_target_community"] = c_b
                    events.append(
                        f"gang_recruitment:{c_a}_vs_{c_b}@tick={tick_number}"
                    )

            # --- Property damage / vandalism ---
            if tension > CONFLICT_PROPERTY_DAMAGE_THRESHOLD and rng.random() < 0.30:
                target_pool = agents_by_community.get(c_b, [])
                if target_pool:
                    rng.shuffle(target_pool)
                    victims = target_pool[:max(1, len(target_pool) // 2)]
                    for vic in victims:
                        vic.resources.wealth *= 0.95
                        vic.resources.property = False
                    events.append(
                        f"vandalism:{c_a}_vs_{c_b}@tick={tick_number}"
                    )

            # --- Hate crimes ---
            if tension > CONFLICT_HATE_CRIME_THRESHOLD and rng.random() < 0.20:
                target_pool = agents_by_community.get(c_b, [])
                if target_pool:
                    rng.shuffle(target_pool)
                    victims = target_pool[:max(1, len(target_pool) // 3)]
                    for vic in victims:
                        safety = vic.needs.get_level(NeedType.SAFETY)
                        vic.needs.set_level(NeedType.SAFETY, safety - 0.2)
                        vic.trust_in_govt = max(0.0, vic.trust_in_govt - 0.05)
                    events.append(
                        f"hate_crime:{c_a}_vs_{c_b}@tick={tick_number}"
                    )

    return events


def resolve_tension_decay(
    tensions: Dict[str, Dict[str, float]],
    rng: DeterministicRNG,
) -> Dict[str, Dict[str, float]]:
    """Decay all inter-community tensions by ``TENSION_BASE_DECAY`` per tick.

    Args:
        tensions: Current tension matrix (modified and returned).
        rng: Deterministic RNG (reserved for future stochastic decay factors).

    Returns:
        Modified tension matrix with decayed values.
    """
    _ = rng  # reserved for future stochastic decay factors

    for c_a in tensions:
        for c_b in list(tensions[c_a].keys()):
            new_val = tensions[c_a][c_b] - TENSION_BASE_DECAY
            tensions[c_a][c_b] = max(0.0, new_val)

    return tensions
