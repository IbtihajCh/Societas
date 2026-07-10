"""Property market — property ownership, rent, and market dynamics."""

from typing import Any

from shared.types.enums import WealthClass
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.utilities.deterministic_rng import DeterministicRNG

# Property tiers: 0=homeless, 1=slum, 2=standard, 3=premium
TIER_NAMES = {0: "homeless", 1: "slum", 2: "standard", 3: "premium"}
BASE_PROPERTY_PRICES: dict[int, float] = {0: 0.0, 1: 50.0, 2: 200.0, 3: 500.0}
RENT_COST_BY_TIER: dict[int, float] = {0: 0.0, 1: 5.0, 2: 25.0, 3: 80.0}

__all__ = [
    "compute_property_values",
    "assign_initial_housing",
    "process_rent",
    "try_buy_property",
    "update_property_market",
]


def compute_property_values(
    world: SimulationState, agents: list[AgentState]
) -> dict[int, float]:
    """Compute current market property prices per tier.

    Base prices are adjusted by crime rate (inverse) and economic prosperity (direct).

    Args:
        world: World state with crime_rate and economic_health.
        agents: All living agents (used for aggregate market context).

    Returns:
        Dict mapping property tier (int) to current price (float).
    """
    crime_mod = 1.0 - world.crime_rate * 0.5
    prosperity_mod = 1.0 + (world.economic_health - 0.5) * 0.4
    values: dict[int, float] = {}
    for tier, base in BASE_PROPERTY_PRICES.items():
        adjusted = base * crime_mod * prosperity_mod
        values[tier] = max(0.0, round(adjusted, 2))
    return values


def assign_initial_housing(agent: AgentState) -> None:
    """Assign initial housing based on wealth class.

    Distribution:
      POOR:          20% homeless, 40% slum, 30% standard, 10% premium
      MIDDLE:         5% homeless, 25% slum, 50% standard, 20% premium
      RICH:           0% homeless, 10% slum, 30% standard, 60% premium
      BUSINESS_OWNER: 0% homeless,  5% slum, 25% standard, 70% premium

    Args:
        agent: Agent to assign housing to (modified in place).
    """
    from shared.constants.simulation_constants import (
        WEALTH_CLASS_DISTRIBUTION,
        WEALTH_CLASS_MONEY_RANGES,
    )

    wc = agent.wealth_class

    if wc == WealthClass.POOR:
        tier_probs = {0: 0.20, 1: 0.40, 2: 0.30, 3: 0.10}
    elif wc == WealthClass.MIDDLE:
        tier_probs = {0: 0.05, 1: 0.25, 2: 0.50, 3: 0.20}
    elif wc == WealthClass.RICH:
        tier_probs = {0: 0.00, 1: 0.10, 2: 0.30, 3: 0.60}
    elif wc == WealthClass.BUSINESS_OWNER:
        tier_probs = {0: 0.00, 1: 0.05, 2: 0.25, 3: 0.70}
    else:
        tier_probs = {0: 0.10, 1: 0.30, 2: 0.40, 3: 0.20}

    tier = 0
    roll = agent.resources.money / max(WEALTH_CLASS_MONEY_RANGES.get(wc, (1, 1000))[1], 1)
    cumulative = 0.0
    for t, prob in sorted(tier_probs.items()):
        cumulative += prob
        if roll <= cumulative:
            tier = t
            break
    else:
        tier = 3

    agent.resources.property_tier = tier
    agent.resources.property = tier >= 1
    agent.resources.property_value = BASE_PROPERTY_PRICES.get(tier, 0.0)
    agent.resources.rent_cost = RENT_COST_BY_TIER.get(tier, 0.0)


def process_rent(
    agent: AgentState, property_values: dict[int, float], rng: DeterministicRNG
) -> bool:
    """Process rent payment for one agent each tick.

    Args:
        agent: Agent to process rent for (modified in place).
        property_values: Current market property prices per tier.
        rng: Deterministic RNG.

    Returns:
        True if the agent was evicted (downgraded), False otherwise.
    """
    if agent.resources.property_tier <= 0:
        return False

    rent = agent.resources.rent_cost
    if agent.resources.money >= rent:
        agent.resources.money -= rent
        agent.resources.wealth = agent.resources.money
        return False

    old_tier = agent.resources.property_tier
    new_tier = max(0, old_tier - 1)
    agent.resources.property_tier = new_tier
    agent.resources.property = new_tier >= 1
    agent.resources.property_value = property_values.get(new_tier, 0.0)
    agent.resources.rent_cost = RENT_COST_BY_TIER.get(new_tier, 0.0)
    agent.unlust = min(1.0, agent.unlust + 0.1)
    return True


def try_buy_property(
    agent: AgentState, property_values: dict[int, float], rng: DeterministicRNG
) -> bool:
    """Attempt to buy property at the next tier.

    Agent needs at least 2x the next tier's property value in liquid money.

    Args:
        agent: Agent attempting the purchase (modified in place).
        property_values: Current market property prices per tier.
        rng: Deterministic RNG.

    Returns:
        True if the purchase succeeded, False otherwise.
    """
    current_tier = agent.resources.property_tier
    if current_tier >= 3:
        return False

    next_tier = current_tier + 1
    cost = 2.0 * property_values.get(next_tier, BASE_PROPERTY_PRICES[next_tier])

    if agent.resources.money >= cost:
        agent.resources.money -= cost
        agent.resources.wealth = agent.resources.money
        agent.resources.property_tier = next_tier
        agent.resources.property = True
        agent.resources.property_value = property_values.get(next_tier, BASE_PROPERTY_PRICES[next_tier])
        agent.resources.rent_cost = RENT_COST_BY_TIER.get(next_tier, 0.0)
        return True

    return False


def update_property_market(
    world: SimulationState, agents: list[AgentState], rng: DeterministicRNG
) -> dict[str, Any]:
    """Run one tick of property market dynamics.

    Updates property values based on crime/economy, processes rent for all agents,
    and handles evictions.

    Args:
        world: World state (modified in place for market conditions).
        agents: All living agents.
        rng: Deterministic RNG.

    Returns:
        Summary dict with keys: 'evictions', 'upgrades'.
    """
    property_values = compute_property_values(world, agents)

    evictions = 0
    for agent in agents:
        if not agent.is_alive:
            continue
        if process_rent(agent, property_values, rng):
            evictions += 1

    return {
        "evictions": evictions,
        "upgrades": 0,
    }
