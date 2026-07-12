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
    # Debt grows proportional to economic pressure, with minimum growth
    # so a flat-pressure economy still accumulates some structural debt.
    debt_growth = max(0.0, economic_pressure * 0.005 - 0.0005)
    world.national_debt = max(0.0, world.national_debt + debt_growth)
    # Cap debt at 100× initial to prevent runaway.
    world.national_debt = min(world.national_debt, 1000.0)

    # ── GDP: exponential moving average of system-wide money ──────────
    # (Avoids double-counting; tracks actual currency in the system.)
    total_money = sum(getattr(a.resources, "money", 0.0) for a in living)
    if world.economy.gdp <= 0.0:
        world.economy.gdp = total_money
    else:
        # α=0.05 gives ~20-tick memory. Decay toward current total_money
        # so GDP can't run away.
        world.economy.gdp = 0.95 * world.economy.gdp + 0.05 * total_money

    # Tax revenue: rolling stock of recent tax income (EMA, no runaway decay).
    # Tax revenue accumulates from WORK actions in action_executor (small
    # additions per work). Here we apply gentle EMA so it tracks recent flow
    # without exponential blow-up.
    if world.economy.tax_revenue < 0.0:
        world.economy.tax_revenue = 0.0
    # Cap at a sensible multiple of GDP so it cannot exceed the economy.
    world.economy.tax_revenue = min(world.economy.tax_revenue, world.economy.gdp * 0.5)

    # Government spending: 70% of recent tax revenue.
    world.economy.government_spending = world.economy.tax_revenue * 0.7

    # ── Compute baseline metrics using CURRENT energy_price, BEFORE the
    # random walk shifts it. This keeps tests deterministic. ─────
    energy_amplifier = 1.0 + world.energy_price * 0.5
    baseline_crime = 0.02 + 0.12 * world.unemployment_rate + 0.08 * economic_pressure * energy_amplifier + 0.05 * scarcity
    world.crime_rate = min(1.0, baseline_crime + agent_crime_rate * 0.5)

    # ── Energy price: random walk with mean reversion to 0.6 ──────────
    # Symmetric oscillation around 0.6. Sign alternates with tick parity,
    # giving a bounded walk without monotonic drift.
    target_energy = 0.6
    noise_sign = 1.0 if (int(world.time_step) % 2 == 0) else -1.0
    world.energy_price = max(
        0.0,
        min(2.0, world.energy_price + (target_energy - world.energy_price) * 0.01 + 0.005 * noise_sign),
    )

    # ── Remittance income: random walk with mean reversion to 0.08 ─────
    target_remit = 0.08
    noise_sign2 = 1.0 if (int(world.time_step) % 2 == 0) else -1.0
    world.remittance_income = max(
        0.0,
        min(0.5, world.remittance_income + (target_remit - world.remittance_income) * 0.02 + 0.003 * noise_sign2),
    )

    # Protest driven by discontent, joblessness, and inflation
    inflation_pressure = world.economy.inflation_rate * 0.5
    baseline_protest = world.unlust * 0.25 + world.unemployment_rate * 0.35 + inflation_pressure
    world.protest_intensity = min(1.0, baseline_protest + agent_protest_rate * 0.5)

    # Crime erodes public order — also has positive recovery from peace
    decay_order = world.crime_rate * 0.015 + world.protest_intensity * 0.005 + inflation_pressure * 0.01
    recovery_order = (
        0.001
        + (1.0 - world.crime_rate) * 0.002
        + (1.0 - world.unemployment_rate) * 0.001
    )
    # Public order has friction: only recovers toward 0.9, not 1.0, so it
    # can never pin at ceiling and the system stays sensitive.
    target_order = 0.9
    world.public_order = max(
        0.0,
        min(1.0, world.public_order - decay_order + recovery_order * (target_order - world.public_order) * 5.0),
    )

    decay_cohesion = world.crime_rate * 0.01 + world.protest_intensity * 0.008 + inflation_pressure * 0.005
    recovery_cohesion = (
        0.001
        + (1.0 - world.crime_rate) * 0.0015
        + world.morality * 0.001
    )
    target_cohesion = 0.9
    world.social_cohesion = max(
        0.0,
        min(1.0, world.social_cohesion - decay_cohesion + recovery_cohesion * (target_cohesion - world.social_cohesion) * 5.0),
    )

    # Economic health: crime/unemployment/inflation/debt drag; work/wages/tax pull
    econ_decay = (
        world.crime_rate * 0.005
        + world.unemployment_rate * 0.005
        + world.economy.inflation_rate * 0.01
        + debt_servicing * 0.1
    )
    econ_recovery = (
        0.001
        + (1.0 - world.unemployment_rate) * 0.002
        + (1.0 - world.crime_rate) * 0.001
        + world.food_availability * 0.0005
    )
    world.economic_health = max(0.01, min(1.0, world.economic_health - econ_decay + econ_recovery))

    # ── Population and time ──────────────────────────────────────────
    world.population = alive_count
    world.time_step = TickNumber(int(world.time_step) + 1)

    # Apply environmental regression and clamp (handled in
    # apply_environmental_tick, but ensure bounds here too).
    world.food_availability = max(0.0, min(1.0, world.food_availability))
    world.water_availability = max(0.0, min(1.0, world.water_availability))

    # ── Wire previously-dead top-level world fields ─────────────
    # Environmental quality tracks food/water availability average
    world.environmental_quality = max(0.0, min(1.0, (world.food_availability + world.water_availability) / 2.0))

    # Innovation index: gradual drift with R&D proxy (work actions)
    # Currently constant; will be wired to action counts in Phase 4
    work_count = sum(getattr(a, "last_action", None) == "WORK" for a in living)
    if hasattr(world, "_last_innovation_update_tick") and int(world.time_step) - world._last_innovation_update_tick >= 10:
        # Slow drift: innovation rises with employment, falls with unrest
        target = 0.5 + (1.0 - world.unemployment_rate) * 0.2 - world.protest_intensity * 0.15
        world.innovation_index = max(0.0, min(1.0, world.innovation_index + (target - world.innovation_index) * 0.05))
        world._last_innovation_update_tick = int(world.time_step)
    elif not hasattr(world, "_last_innovation_update_tick"):
        world._last_innovation_update_tick = int(world.time_step)

    # Remittance income: random walk with mean reversion
    world.remittance_income = max(0.0, min(1.0, world.remittance_income + (0.08 - world.remittance_income) * 0.01))

    # ── Wired sub-state writers (Phase 2: kill the dead fields) ───
    avg_morality = world.morality
    avg_happiness = world.unlust and (1.0 - world.unlust) or 0.5  # placeholder
    if living:
        avg_happiness = sum(a.emotions.happiness_score for a in living) / alive_count
    avg_unlust_world = world.unlust

    # EconomyState: track actual economy activity
    employed_count = sum(1 for a in living if a.resources.employed)
    world.economy.employment_rate = employed_count / alive_count
    world.economy.consumer_confidence = max(0.0, min(1.0, 0.5 + (avg_happiness - 0.5) * 0.6 - avg_unlust_world * 0.3))
    world.economy.market_stability = max(0.0, min(1.0, 1.0 - world.crime_rate * 0.5 - world.protest_intensity * 0.4 - world.economy.inflation_rate * 0.3))

    # CrimeState: track actual crime dynamics
    world.crime.overall_crime_rate = world.crime_rate
    world.crime.public_safety_index = max(0.0, min(1.0, 1.0 - world.crime_rate * 1.5 - world.protest_intensity * 0.5))
    world.crime.crime_victims_total = int(total_crimes)
    world.crime.crimes_reported = int(total_crimes)
    world.crime.crimes_resolved = int(total_crimes * world.crime.enforcement_effectiveness)

    # PsychologyState: aggregate psychological well-being
    world.psychology.average_morality = avg_morality
    world.psychology.average_happiness = avg_happiness
    world.psychology.average_stress = max(0.0, min(1.0, avg_unlust_world * 0.7 + (1.0 - world.economic_health) * 0.3))
    world.psychology.mental_health_index = max(0.0, min(1.0, avg_happiness * 0.6 + (1.0 - avg_unlust_world) * 0.4))
    world.psychology.social_satisfaction = max(0.0, min(1.0, world.social_cohesion * 0.5 + avg_happiness * 0.3 + (1.0 - avg_unlust_world) * 0.2))
    world.psychology.life_satisfaction = max(0.0, min(1.0, avg_happiness * 0.4 + world.economic_health * 0.3 + world.public_order * 0.2 + (1.0 - avg_unlust_world) * 0.1))


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
