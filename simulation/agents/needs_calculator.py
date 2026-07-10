"""
Needs Calculator
================

Decays all 13 needs per tick according to deterministic formulas, checks
death conditions, and derives wealth class from current money.

All randomness uses DeterministicRNG (seeded numpy). No LLM calls.
"""

from shared.constants.defaults import (
    DESPAIR_MORTALITY_RATE,
    ECONOMIC_HARDSHIP_DEATH_RATE,
    FAMILY_DECAY_RATE,
    FOOD_DEATH_THRESHOLD,
    FOOD_DECAY_RATE,
    HEALTH_DEATH_THRESHOLD,
    JOB_LOSS_RATE,
    JOB_LOSS_ECON_SENSITIVITY,
    REPUTATION_DECAY_RATE,
    ROMANTIC_DECAY_RATE,
    SAFETY_DECAY_RATE,
    SCARCITY_BASE,
    SELF_ESTEEM_DECAY_RATE,
    SEXUAL_TENSION_GROWTH_RATE,
    SLEEP_DECAY_RATE,
    SLEEP_REPLENISH_RATE,
    SOCIAL_DECAY_RATE,
    UNLUST_FINANCIAL_DIVISOR,
    WATER_DEATH_THRESHOLD,
    WATER_DECAY_RATE,
)
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import EmotionType, EmploymentStatus, NeedType, WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "decay_needs",
    "check_death",
    "derive_wealth_class",
    "maybe_lose_job",
]


def decay_needs(
    agent: AgentState,
    world: SimulationState,
    rng: DeterministicRNG,
) -> None:
    """Decay all 13 needs for one tick based on deterministic formulas.

    Scarcity multiplier: ``SCARCITY_BASE - food_availability`` (higher
    scarcity = faster decay). Crime pressure adds to safety decay.
    Extraversion modulates social connection decay.

    Args:
        agent: The agent whose needs are being decayed (modified in place).
        world: The current world state (food_availability, crime_rate).
        rng: Deterministic RNG (reserved for future stochastic extensions;
             currently unused in this function).
    """
    scarcity = SCARCITY_BASE - world.food_availability
    crime_pressure = world.crime_rate * 0.01

    needs = agent.needs

    # --- Layer 1: Physiological ---
    # Food & water decay relative to scarcity
    needs.set_level(
        NeedType.FOOD,
        needs.get_level(NeedType.FOOD) - FOOD_DECAY_RATE * scarcity,
    )
    needs.set_level(
        NeedType.WATER,
        needs.get_level(NeedType.WATER) - WATER_DECAY_RATE * scarcity,
    )
    # Sleep decays but auto-replenishes partially each tick
    needs.set_level(
        NeedType.SLEEP,
        needs.get_level(NeedType.SLEEP) - SLEEP_DECAY_RATE + SLEEP_REPLENISH_RATE,
    )
    # Sexual tension builds up over time (not a decay)
    needs.set_level(
        NeedType.SEXUAL_TENSION,
        needs.get_level(NeedType.SEXUAL_TENSION) + SEXUAL_TENSION_GROWTH_RATE,
    )

    # --- Layer 2: Safety & Security ---
    needs.set_level(
        NeedType.SAFETY,
        needs.get_level(NeedType.SAFETY) - SAFETY_DECAY_RATE - crime_pressure,
    )
    # Financial security is derived from current money
    money_ratio = min(1.0, agent.resources.money / UNLUST_FINANCIAL_DIVISOR)
    needs.set_level(NeedType.FINANCIAL_SECURITY, money_ratio)
    # Shelter is derived from property ownership
    needs.set_level(
        NeedType.SHELTER,
        1.0 if agent.resources.property else 0.3,
    )

    # --- Layer 3: Love & Belonging ---
    extraversion_factor = 1.2 if agent.traits.extraversion > 0.5 else 0.8
    needs.set_level(
        NeedType.SOCIAL_CONNECTION,
        needs.get_level(NeedType.SOCIAL_CONNECTION)
        - SOCIAL_DECAY_RATE * extraversion_factor,
    )
    needs.set_level(
        NeedType.FAMILY_BOND,
        needs.get_level(NeedType.FAMILY_BOND) - FAMILY_DECAY_RATE,
    )
    needs.set_level(
        NeedType.ROMANTIC_BOND,
        needs.get_level(NeedType.ROMANTIC_BOND) - ROMANTIC_DECAY_RATE,
    )

    # --- Layer 4: Esteem ---
    needs.set_level(
        NeedType.SELF_ESTEEM,
        needs.get_level(NeedType.SELF_ESTEEM) - SELF_ESTEEM_DECAY_RATE,
    )
    needs.set_level(
        NeedType.REPUTATION,
        needs.get_level(NeedType.REPUTATION) - REPUTATION_DECAY_RATE,
    )
    # INFERIORITY_GAP is computed on social interaction, no passive decay.

    # Derive wealth class from current money each tick.
    agent.wealth_class = derive_wealth_class(agent.resources.money)
    # Keep legacy wealth field in sync with money.
    agent.resources.wealth = agent.resources.money


def check_death(agent: AgentState, rng: DeterministicRNG, world: SimulationState | None = None) -> bool:
    """Check whether the agent meets any death condition this tick.

    Death conditions:
    - Food <= ``FOOD_DEATH_THRESHOLD`` (starvation).
    - Water <= ``WATER_DEATH_THRESHOLD`` (dehydration).
    - Health <= ``HEALTH_DEATH_THRESHOLD`` (health failure).
    - Primary emotion is DESPAIR with a per-tick mortality roll.
    - Economic hardship: unemployed + low money + high inflation (per-tick roll).

    Args:
        agent: The agent to evaluate.
        rng: Deterministic RNG for probability rolls.
        world: Current world state (for inflation check).

    Returns:
        True if the agent should die this tick, False otherwise.
    """
    if not agent.is_alive:
        return False

    if agent.needs.get_level(NeedType.FOOD) <= FOOD_DEATH_THRESHOLD:
        return True

    if agent.needs.get_level(NeedType.WATER) <= WATER_DEATH_THRESHOLD:
        return True

    if agent.resources.health <= HEALTH_DEATH_THRESHOLD:
        return True

    if agent.emotions.primary == EmotionType.DESPAIR:
        if rng.random() < DESPAIR_MORTALITY_RATE:
            return True

    if world is not None:
        hardship_risk = (
            (1.0 - agent.resources.employed)
            * (1.0 - min(1.0, agent.resources.money / 500.0))
            * max(0.0, world.economy.inflation_rate) * 10.0
            * ECONOMIC_HARDSHIP_DEATH_RATE * 2.0
        )
        if hardship_risk > 0 and rng.random() < hardship_risk:
            return True

    return False


def derive_wealth_class(money: float) -> WealthClass:
    """Derive wealth classification from current money amount.

    Args:
        money: Current liquid money in pounds.

    Returns:
        ``WealthClass.POOR`` if money < 1000,
        ``WealthClass.MIDDLE`` if 1000 <= money < 15000,
        ``WealthClass.RICH`` otherwise.
    """
    if money < 1000.0:
        return WealthClass.POOR
    if money < 15000.0:
        return WealthClass.MIDDLE
    return WealthClass.RICH


def maybe_lose_job(agent: AgentState, rng: DeterministicRNG, world: SimulationState | None = None) -> bool:
    """Probabilistic job loss. Returns True if agent lost job this tick.

    Base rate is ``JOB_LOSS_RATE`` (default 0.002 = 0.2% per tick).
    Scales with economic pressure: higher unemployment + weaker economy = more layoffs.
    Only affects employed agents. On job loss, sets employed=False,
    employment_status=UNEMPLOYED, base_salary=0.0.

    Args:
        agent: The agent to evaluate for job loss (modified in place).
        rng: Deterministic RNG for the probability roll.
        world: Current world state (for economic pressure scaling).

    Returns:
        True if the agent lost their job this tick, False otherwise.
    """
    if not agent.resources.employed:
        return False
    economic_pressure = max(0.0, 1.0 - world.economic_health) if world else 0.0
    effective_rate = JOB_LOSS_RATE * (1.0 + JOB_LOSS_ECON_SENSITIVITY * economic_pressure)
    if rng.random() < effective_rate:
        agent.resources.employed = False
        agent.employment_status = EmploymentStatus.UNEMPLOYED
        agent.resources.base_salary = 0.0
        return True
    return False
