"""Economy system — rent, welfare, debt interest, and money flow management."""

from typing import Optional

from shared.constants.defaults import DEFAULT_WELFARE_AMOUNT
from shared.constants.simulation_constants import RENT_COST, SALARY_RANGES
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
<<<<<<< HEAD
from shared.constants.defaults import DEFAULT_WELFARE_AMOUNT, DEBT_INTEREST_RATE
from shared.constants.simulation_constants import RENT_COST

__all__ = ["apply_rent", "apply_welfare", "apply_debt_interest", "process_economy_tick"]
=======
from shared.types.enums import EmploymentStatus, JobType, WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.world.labor_market import (
    adjust_salaries,
    compute_job_demand,
    maybe_change_job,
    update_unemployment_rate,
)

__all__ = ["apply_rent", "apply_welfare", "apply_tax", "process_economy_tick"]
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)


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


def apply_tax(agent: AgentState, world: SimulationState) -> float:
    """Apply income tax based on world tax_rate and agent wealth class.

    Tax is a percentage of the agent's current money, with higher
    effective rates for wealthier classes to simulate progressive taxation.

    Args:
        agent: The agent to tax (modified in place).
        world: World state (checks tax_rate).

    Returns:
        The tax amount collected (0.0 if tax_rate is 0).
    """
    rate = world.tax_rate
    if rate <= 0.0:
        return 0.0
    effective_rate = rate
    if agent.wealth_class == WealthClass.MIDDLE:
        effective_rate = rate * 1.2
    elif agent.wealth_class == WealthClass.RICH:
        effective_rate = rate * 1.5
    effective_rate = min(effective_rate, 0.8)
    tax = agent.resources.money * effective_rate
    agent.resources.money = max(0.0, agent.resources.money - tax)
    agent.resources.wealth = agent.resources.money
    return tax


def process_economy_tick(
    agents: list[AgentState],
    world: SimulationState,
    rng: Optional[DeterministicRNG] = None,
) -> dict[str, float]:
    """Process economy-wide effects for all agents in one tick.

    Computes job demand, adjusts salaries, handles job changes,
    then applies rent to non-property-owners and welfare to unemployed agents.

    Args:
        agents: All living agents.
        world: World state.
        rng: Deterministic RNG (required for job change logic).

    Returns:
        Dict with 'total_rent', 'total_welfare', 'rent_payers', 'welfare_recipients'.
    """
    # Labor market: compute job demand and adjust salaries
    job_demand = compute_job_demand(agents, world)
    world.job_demand = job_demand

    if rng is not None:
        adjust_salaries(agents, world, job_demand, rng)

    # Job change attempts for unemployed or low-morale agents
    if rng is not None:
        for agent in agents:
            if not agent.is_alive:
                continue
            new_job = maybe_change_job(agent, agents, job_demand, world, rng)
            if new_job is not None:
                agent.job_type = JobType(new_job)
                agent.resources.employed = True
                salary_range = SALARY_RANGES.get(agent.job_type, (0.0, 0.0))
                multiplier = world.job_salary_multipliers.get(new_job, 1.0)
                agent.resources.base_salary = (
                    (salary_range[0] + salary_range[1]) / 2.0 * multiplier
                )

    total_rent = 0.0
    total_welfare = 0.0
    total_tax = 0.0
    rent_payers = 0
    welfare_recipients = 0
    tax_payers = 0

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

        tax = apply_tax(agent, world)
        if tax > 0:
            total_tax += tax
            tax_payers += 1

    # Update unemployment rate after all employment changes
    update_unemployment_rate(agents, world)

    return {
        "total_rent": total_rent,
        "total_welfare": total_welfare,
        "total_tax": total_tax,
        "rent_payers": float(rent_payers),
        "welfare_recipients": float(welfare_recipients),
        "tax_payers": float(tax_payers),
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
