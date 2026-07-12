"""
Needs Calculator
================

Decays all 13 needs per tick according to deterministic formulas, checks
death conditions, and derives wealth class from current money.

All randomness uses DeterministicRNG (seeded numpy). No LLM calls.
"""

from shared.constants.defaults import (
    AGE_MORTALITY_BASE,
    AGE_MORTALITY_ELDERLY,
    AGE_PROGRESSION_INTERVAL,
    DESPAIR_MORTALITY_RATE,
    ECONOMIC_HARDSHIP_DEATH_RATE,
    ENV_NEED_DECAY_FOOD_MULTIPLIER,
    ENV_NEED_DECAY_WATER_MULTIPLIER,
    EXISTENTIAL_DEATH_CHANCE,
    FAMILY_DECAY_RATE,
    FOOD_DEATH_THRESHOLD,
    FOOD_DECAY_RATE,
    HEALTH_DEATH_THRESHOLD,
    INSOMNIA_DECAY_RATE,
    INSOMNIA_INCREASE_RATE,
    INSOMNIA_MAX,
    INSOMNIA_SAFETY_THRESHOLD,
    INSOMNIA_STRESS_THRESHOLD,
    JOB_LOSS_RATE,
    JOB_LOSS_ECON_SENSITIVITY,
    REPUTATION_DECAY_RATE,
    ROMANTIC_DECAY_RATE,
    SAFETY_DECAY_RATE,
    SCARCITY_BASE,
    SELF_ESTEEM_DECAY_RATE,
    SEXUAL_TENSION_GROWTH_RATE,
    SLEEP_DEATH_THRESHOLD,
    SLEEP_DECAY_RATE,
    SLEEP_RECOVERY_NATURAL,
    SOCIAL_DECAY_RATE,
    UNLUST_FINANCIAL_DIVISOR,
    WATER_DEATH_THRESHOLD,
    WATER_DECAY_RATE,
)
from shared.schemas.agent_state import AgentState, get_age_bracket
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import EmotionType, EmploymentStatus, NeedType, WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "decay_needs",
    "check_death",
    "derive_wealth_class",
    "maybe_lose_job",
    "progress_age",
    "update_insomnia",
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

    # Environmental crisis multipliers: when food/water availability is
    # critically low (< 0.4), decay rates increase by configured multiplier.
    food_multiplier = (
        ENV_NEED_DECAY_FOOD_MULTIPLIER
        if world.food_availability < 0.4
        else 1.0
    )
    water_multiplier = (
        ENV_NEED_DECAY_WATER_MULTIPLIER
        if world.water_availability < 0.4
        else 1.0
    )

    needs = agent.needs

    # --- Layer 1: Physiological ---
    # Food & water decay relative to scarcity, multiplied during crisis
    needs.set_level(
        NeedType.FOOD,
        needs.get_level(NeedType.FOOD)
        - FOOD_DECAY_RATE * scarcity * food_multiplier,
    )
    needs.set_level(
        NeedType.WATER,
        needs.get_level(NeedType.WATER)
        - WATER_DECAY_RATE * scarcity * water_multiplier,
    )
    # Sleep decays with natural recovery each tick
    needs.set_level(
        NeedType.SLEEP,
        needs.get_level(NeedType.SLEEP) - SLEEP_DECAY_RATE + SLEEP_RECOVERY_NATURAL,
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

    # Gradual health decay each tick.
    agent.resources.health = max(0.0, agent.resources.health - 0.001)

    # Derive wealth class from current money each tick.
    agent.wealth_class = derive_wealth_class(agent.resources.money)
    # Keep legacy wealth field in sync with money.
    agent.resources.wealth = agent.resources.money


def progress_age(agent: AgentState) -> None:
    """Advance the agent's age by one tick and update the age bracket.

    Args:
        agent: The agent to age (modified in place).
    """
    agent.age += AGE_PROGRESSION_INTERVAL
    agent.age_bracket = get_age_bracket(agent.age)


def check_death(agent: AgentState, rng: DeterministicRNG, world: SimulationState | None = None) -> bool:
    """Check whether the agent meets any death condition this tick.

    Death conditions:
    - Food <= ``FOOD_DEATH_THRESHOLD`` (starvation).
    - Water <= ``WATER_DEATH_THRESHOLD`` (dehydration).
    - Health <= ``HEALTH_DEATH_THRESHOLD`` (health failure).
    - Primary emotion is DESPAIR with a per-tick mortality roll.
    - Elderly agents face ``AGE_MORTALITY_BASE + AGE_MORTALITY_ELDERLY`` per-tick
      mortality.
    - Economic hardship: unemployed + low money + high inflation (per-tick roll).

    On death, sets ``agent.cause_of_death`` to the reason.

    Args:
        agent: The agent to evaluate (modified in place on death).
        rng: Deterministic RNG for the despair and age mortality rolls.
        world: Current world state (for inflation check).

    Returns:
        True if the agent should die this tick, False otherwise.
    """
    if not agent.is_alive:
        return False

    # ── Phase 5: smooth probability curves (no sudden cliffs) ──────────
    # Each need is checked against its threshold, but instead of binary
    # death at threshold, we use a sigmoid-shaped probability curve so
    # an agent at threshold has ~0% chance, at 0 has ~5% chance, and the
    # curve ramps smoothly between them.

    food = agent.needs.get_level(NeedType.FOOD)
    if food < FOOD_DEATH_THRESHOLD * 3:  # start fading before threshold
        # Map food in [0, FOOD_DEATH_THRESHOLD*3] -> death prob [0.05, 0.0]
        ratio = (food - 0.0) / max(0.001, FOOD_DEATH_THRESHOLD * 3)
        ratio = max(0.0, min(1.0, ratio))
        death_prob = 0.05 * (1.0 - ratio)
        if death_prob > 0 and rng.random() < death_prob:
            agent.cause_of_death = "food_starvation"
            return True

    water = agent.needs.get_level(NeedType.WATER)
    if water < WATER_DEATH_THRESHOLD * 3:
        ratio = (water - 0.0) / max(0.001, WATER_DEATH_THRESHOLD * 3)
        ratio = max(0.0, min(1.0, ratio))
        death_prob = 0.04 * (1.0 - ratio)
        if death_prob > 0 and rng.random() < death_prob:
            agent.cause_of_death = "water_dehydration"
            return True

    if agent.resources.health < HEALTH_DEATH_THRESHOLD * 3:
        ratio = agent.resources.health / max(0.001, HEALTH_DEATH_THRESHOLD * 3)
        ratio = max(0.0, min(1.0, ratio))
        death_prob = 0.5 * (1.0 - ratio)
        if death_prob > 0 and rng.random() < death_prob:
            agent.cause_of_death = "health_failure"
            return True

    if agent.ticks_without_sleep >= 30:
        # Sleep death ramps with ticks_without_sleep: 0 at 30, 0.3 at 80
        sleep_age = agent.ticks_without_sleep - 30
        death_prob = min(0.3, sleep_age / 200.0)
        if rng.random() < death_prob:
            agent.cause_of_death = "insomnia_exhaustion"
            return True

    if agent.emotions.primary == EmotionType.DESPAIR:
        if rng.random() < DESPAIR_MORTALITY_RATE:
            agent.cause_of_death = "despair"
            return True

    if agent.purpose_fulfillment < 0.1 and rng.random() < EXISTENTIAL_DEATH_CHANCE:
        agent.cause_of_death = "existential_despair"
        return True

    if agent.age_bracket == "elderly":
        # Age-graded elderly mortality: lower for "young-elderly" (66-79),
        # ramps up for 80-89, peaks for 90+. Without this gradient the
        # entire initial cohort dies at the same time, causing a population
        # crash before grandchildren can mature.
        if agent.age < 80:
            mortality_chance = AGE_MORTALITY_BASE + AGE_MORTALITY_ELDERLY
        elif agent.age < 90:
            mortality_chance = AGE_MORTALITY_BASE + AGE_MORTALITY_ELDERLY * 2.5
        else:
            mortality_chance = AGE_MORTALITY_BASE + AGE_MORTALITY_ELDERLY * 5.0
        if rng.random() < mortality_chance:
            agent.cause_of_death = "old_age"
            return True

    if world is not None:
        # Smooth hardship: scales continuously with unemployment + low money + inflation
        # Max risk ~ 0.5% per tick when fully destitute in hyperinflation
        hardship_risk = (
            (1.0 - agent.resources.employed)
            * (1.0 - min(1.0, agent.resources.money / 500.0))
            * max(0.0, world.economy.inflation_rate) * 5.0
            * ECONOMIC_HARDSHIP_DEATH_RATE
        )
        if hardship_risk > 0 and rng.random() < hardship_risk:
            return True

    return False


def update_insomnia(agent: AgentState, world: SimulationState) -> None:
    """Update insomnia severity and track sleep deprivation.

    - Ticks without sleep are incremented when sleep < 0.3, reset when > 0.5.
    - Insomnia increases when sleep is low or when stress (unlust) is high
      combined with low safety.
    - Insomnia decreases otherwise.
    - High insomnia feeds back into unlust (sleep deprivation effects).

    Args:
        agent: The agent to update (modified in place).
        world: Current world state (used for safety checks).
    """
    if not agent.is_alive:
        return

    sleep_level = agent.needs.get_level(NeedType.SLEEP)

    # Track consecutive ticks without adequate sleep
    if sleep_level < 0.3:
        agent.ticks_without_sleep += 1
    elif sleep_level > 0.5:
        agent.ticks_without_sleep = 0

    # Determine insomnia change
    unlust = agent.unlust
    safety = agent.needs.get_level(NeedType.SAFETY)

    if sleep_level < 0.3:
        agent.insomnia_severity = min(
            INSOMNIA_MAX,
            agent.insomnia_severity + INSOMNIA_INCREASE_RATE,
        )
    elif unlust > INSOMNIA_STRESS_THRESHOLD and safety < INSOMNIA_SAFETY_THRESHOLD:
        agent.insomnia_severity = min(
            INSOMNIA_MAX,
            agent.insomnia_severity + INSOMNIA_INCREASE_RATE,
        )
    else:
        agent.insomnia_severity = max(
            0.0,
            agent.insomnia_severity - INSOMNIA_DECAY_RATE,
        )

    # Sleep deprivation feedback effects
    if agent.insomnia_severity > 0.5:
        agent.unlust = min(1.0, agent.unlust + 0.01)
    if agent.insomnia_severity > 0.7:
        agent.unlust = min(1.0, agent.unlust + 0.02)


def derive_wealth_class(money: float) -> WealthClass:
    """Derive wealth classification from current money amount.

    Args:
        money: Current liquid money in pounds.

    Returns:
        ``WealthClass.POOR`` if money < 500,
        ``WealthClass.MIDDLE`` if 500 <= money < 5000,
        ``WealthClass.RICH`` otherwise.
    """
    if money < 500.0:
        return WealthClass.POOR
    if money < 5000.0:
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
