"""Metrics calculator — computes world-level and wealth-stratified metrics each tick."""

from collections import Counter

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.types.aliases import TickNumber
from shared.types.enums import ActionType, EmotionType, NeedType, WealthClass

__all__ = [
    "update_world_metrics",
    "compute_wealth_stratified_metrics",
    "compute_action_frequencies",
    "compute_state_hash",
]


def update_world_metrics(
    world: SimulationState, all_agents: list[AgentState]
) -> None:
    """Recompute world-level metrics from all living agents.

    Updates: crime_rate, protest_intensity, unemployment_rate, unlust (avg),
    morality (avg), population, time_step, public_order, social_cohesion,
    economic_health.

    Variables are coupled realistically: unemployment drives crime, crime
    erodes public order and social cohesion, economic health affects
    employment, and discontent fuels protest.

    Args:
        world: World state to update (modified in place).
        all_agents: All agents in the simulation.
    """
    living = [a for a in all_agents if a.is_alive]
    alive_count = len(living)

    if alive_count == 0:
        return

    # ── Agent-based metrics ──────────────────────────────────────────
    total_crimes = sum(a.crimes_committed for a in living)
    agent_crime_rate = min(1.0, total_crimes / (alive_count * 8)) if alive_count else 0.0

    total_protests = sum(a.protest_count for a in living)
    agent_protest_rate = min(1.0, total_protests / (alive_count * 4)) if alive_count else 0.0

    unemployed = sum(1 for a in living if not a.resources.employed)
    world.unemployment_rate = unemployed / alive_count if alive_count else 0.0

    world.unlust = sum(a.unlust for a in living) / alive_count
    world.morality = sum(a.traits.morality for a in living) / alive_count

    # ── Socio-economic coupling (realistic variable interaction) ─────
    economic_pressure = max(0.0, 1.0 - world.economic_health)
    scarcity = 1.0 - (world.food_availability + world.water_availability) / 2.0

    # ── Dynamic inflation (driven by energy price + economic pressure) ─
    inflation_increase = world.energy_price * 0.003 + economic_pressure * 0.002
    inflation_decrease = 0.002
    world.economy.inflation_rate = max(0.0, min(0.5, world.economy.inflation_rate + inflation_increase - inflation_decrease))

    # ── National debt accumulates when economy is weak ────────────────
    debt_servicing = world.national_debt * 0.005
    world.national_debt = max(0.0, world.national_debt + economic_pressure * 0.002 - 0.001)

    # Energy price amplifies economic pressure (Pakistan-relevant)
    energy_amplifier = 1.0 + world.energy_price * 0.5
    baseline_crime = 0.02 + 0.12 * world.unemployment_rate + 0.08 * economic_pressure * energy_amplifier + 0.05 * scarcity
    world.crime_rate = min(1.0, baseline_crime + agent_crime_rate * 0.5)

    # Protest driven by discontent, joblessness, and inflation
    inflation_pressure = world.economy.inflation_rate * 0.5
    baseline_protest = world.unlust * 0.25 + world.unemployment_rate * 0.35 + inflation_pressure
    world.protest_intensity = min(1.0, baseline_protest + agent_protest_rate * 0.5)

    # Crime erodes public order — no recovery (order only decays)
    decay_order = world.crime_rate * 0.015 + world.protest_intensity * 0.005 + inflation_pressure * 0.01
    world.public_order = max(0.0, min(1.0, world.public_order - decay_order))

    decay_cohesion = world.crime_rate * 0.01 + world.protest_intensity * 0.008 + inflation_pressure * 0.005
    world.social_cohesion = max(0.0, min(1.0, world.social_cohesion - decay_cohesion))

    # Economic health: crime, unemployment, inflation, debt all drag
    econ_decay = (
        world.crime_rate * 0.005
        + world.unemployment_rate * 0.005
        + world.economy.inflation_rate * 0.01
        + debt_servicing * 0.1
    )
    world.economic_health = max(0.01, min(1.0, world.economic_health - econ_decay))

    # ── Population and time ──────────────────────────────────────────
    world.population = alive_count
    world.time_step = TickNumber(int(world.time_step) + 1)


def compute_wealth_stratified_metrics(
    all_agents: list[AgentState],
) -> dict[str, dict[str, float]]:
    """Compute metrics broken down by wealth class.

    Args:
        all_agents: All living agents.

    Returns:
        Dict mapping wealth class name to dict of metrics:
        {class: {avg_happiness, avg_unlust, avg_money, count, crime_rate}}
    """
    living = [a for a in all_agents if a.is_alive]
    result: dict[str, dict[str, float]] = {}

    for wc in WealthClass:
        class_agents = [a for a in living if a.wealth_class == wc]
        count = len(class_agents)
        if count == 0:
            result[wc.value] = {
                "avg_happiness": 0.0,
                "avg_unlust": 0.0,
                "avg_money": 0.0,
                "count": 0,
                "crime_rate": 0.0,
            }
            continue

        result[wc.value] = {
            "avg_happiness": sum(a.emotions.happiness_score for a in class_agents) / count,
            "avg_unlust": sum(a.unlust for a in class_agents) / count,
            "avg_money": sum(a.resources.money for a in class_agents) / count,
            "count": count,
            "crime_rate": sum(a.crimes_committed for a in class_agents) / (count * 8),
        }

    return result


def compute_action_frequencies(
    actions: list[AgentActionResult],
) -> dict[str, float]:
    """Compute action frequency distribution.

    Args:
        actions: List of action results from a tick.

    Returns:
        Dict mapping action name to frequency (0.0-1.0).
    """
    if not actions:
        return {}
    counter: Counter[str] = Counter()
    for a in actions:
        counter[a.action.value] += 1
    total = len(actions)
    return {action: count / total for action, count in counter.items()}


def compute_state_hash(
    world: SimulationState, all_agents: list[AgentState]
) -> str:
    """Compute a deterministic SHA-256 hash of the simulation state.

    Only includes deterministic state (excludes LLM reasoning, metadata).
    This hash verifies reproducibility — same seed + same config = same hash.

    Args:
        world: World state.
        all_agents: All agents.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    import hashlib

    parts: list[str] = []
    parts.append(f"tick:{world.time_step}")
    parts.append(f"pop:{world.population}")
    parts.append(f"food:{world.food_availability:.6f}")
    parts.append(f"water:{world.water_availability:.6f}")
    parts.append(f"crime:{world.crime_rate:.6f}")
    parts.append(f"protest:{world.protest_intensity:.6f}")
    parts.append(f"unemp:{world.unemployment_rate:.6f}")
    parts.append(f"tax:{world.tax_rate:.6f}")
    parts.append(f"welfare:{world.welfare_enabled}")
    parts.append(f"unlust:{world.unlust:.6f}")
    parts.append(f"morality:{world.morality:.6f}")

    for agent in sorted(all_agents, key=lambda a: str(a.id)):
        if not agent.is_alive:
            parts.append(f"{agent.id}:dead")
            continue
        parts.append(
            f"{agent.id}:"
            f"m={agent.resources.money:.2f}:"
            f"f={agent.needs.get_level(NeedType.FOOD):.4f}:"
            f"u={agent.unlust:.4f}:"
            f"e={agent.emotions.primary.value}:"
            f"h={agent.emotions.happiness_score:.4f}:"
            f"x={agent.grid_x}:y={agent.grid_y}:"
            f"la={agent.last_action.value}"
        )

    data = "|".join(parts).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
