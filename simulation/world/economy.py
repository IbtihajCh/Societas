"""Economy system — rent, welfare, debt interest, and money flow management."""

from shared.types.enums import EmploymentStatus, WealthClass
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.constants.defaults import DEFAULT_WELFARE_AMOUNT, DEBT_INTEREST_RATE
from shared.constants.simulation_constants import RENT_COST

__all__ = ["apply_rent", "apply_welfare", "apply_debt_interest", "process_economy_tick"]


def apply_rent(agent: AgentState) -> float:
    """Apply rent cost if agent doesn't own property.

    Args:
        agent: The agent to apply rent to (modified in place).

    Returns:
        The rent amount paid (0.0 if owns property).
    """
    if agent.resources.property:
        return 0.0
    rent = RENT_COST.get(agent.wealth_class, 2.0)
    agent.resources.money = max(0.0, agent.resources.money - rent)
    agent.resources.wealth = agent.resources.money
    return rent


def apply_welfare(agent: AgentState, world: SimulationState) -> float:
    """Apply welfare payment if enabled and agent is unemployed.

    Args:
        agent: The agent to apply welfare to (modified in place).
        world: World state (checks welfare_enabled and welfare_amount).

    Returns:
        The welfare amount received (0.0 if not eligible).
    """
    if not world.welfare_enabled:
        return 0.0
    if agent.resources.employed:
        return 0.0
    amount = world.welfare_amount
    agent.resources.money += amount
    agent.resources.wealth = agent.resources.money
    return amount


def process_economy_tick(
    agents: list[AgentState], world: SimulationState
) -> dict[str, float]:
    """Process economy-wide effects for all agents in one tick.

    Applies rent to non-property-owners and welfare to unemployed agents.

    Args:
        agents: All living agents.
        world: World state.

    Returns:
        Dict with 'total_rent', 'total_welfare', 'rent_payers', 'welfare_recipients'.
    """
    total_rent = 0.0
    total_welfare = 0.0
    rent_payers = 0
    welfare_recipients = 0

    for agent in agents:
        if not agent.is_alive:
            continue
        rent = apply_rent(agent)
        if rent > 0:
            total_rent += rent
            rent_payers += 1

        welfare = apply_welfare(agent, world)
        if welfare > 0:
            total_welfare += welfare
            welfare_recipients += 1

    return {
        "total_rent": total_rent,
        "total_welfare": total_welfare,
        "rent_payers": float(rent_payers),
        "welfare_recipients": float(welfare_recipients),
    }


def apply_debt_interest(
    agents: list[AgentState], world: SimulationState
) -> dict[str, float]:
    """Apply debt interest to all agents and track national debt.

    Args:
        agents: All living agents.
        world: World state (national_debt updated in place).

    Returns:
        Dict with 'total_interest_paid', 'agents_in_debt'.
    """
    total_interest = 0.0
    in_debt = 0

    for agent in agents:
        if not agent.is_alive:
            continue
        if agent.resources.debt > 0:
            interest = agent.resources.debt * DEBT_INTEREST_RATE
            agent.resources.debt += interest
            total_interest += interest
            in_debt += 1

    return {
        "total_interest_paid": total_interest,
        "agents_in_debt": float(in_debt),
    }
