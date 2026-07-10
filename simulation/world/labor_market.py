"""Labor market dynamics — job demand, salary adjustment, and job change."""

from typing import Dict, Optional

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import JobType
from shared.utilities.deterministic_rng import DeterministicRNG

# Target employment ratios for each job type.
JOB_TARGET_RATIOS: Dict[JobType, float] = {
    JobType.ENGINEER: 0.15,
    JobType.COMPUTER_SCIENTIST: 0.10,
    JobType.PILOT: 0.03,
    JobType.DOCTOR: 0.05,
    JobType.THERAPIST: 0.04,
    JobType.MECHANIC: 0.08,
    JobType.ELECTRICIAN: 0.07,
    JobType.CONSTRUCTION_PLANNER: 0.03,
    JobType.CONSTRUCTION_WORKER: 0.12,
    JobType.CLEANER: 0.15,
    JobType.TAXI_DRIVER: 0.08,
}


def compute_job_demand(
    agents: list[AgentState], world: SimulationState
) -> Dict[str, int]:
    """Compute job demand for each job type.

    For each job type: count employed agents;
    demand = max(0, target_ratio * population - employed_count).

    Args:
        agents: All living agents.
        world: World state.

    Returns:
        Dict mapping job type strings to demand counts.
    """
    population = len([a for a in agents if a.is_alive])
    if population == 0:
        return {j.value: 0 for j in JobType if j != JobType.UNEMPLOYED}

    employed_counts: Dict[str, int] = {}
    for job_type in JobType:
        if job_type == JobType.UNEMPLOYED:
            continue
        employed_counts[job_type.value] = 0

    for agent in agents:
        if not agent.is_alive:
            continue
        jt = agent.job_type
        if jt != JobType.UNEMPLOYED and agent.resources.employed:
            employed_counts[jt.value] = employed_counts.get(jt.value, 0) + 1

    job_demand: Dict[str, int] = {}
    for job_type, target_ratio in JOB_TARGET_RATIOS.items():
        employed = employed_counts.get(job_type.value, 0)
        target = int(target_ratio * population)
        demand = max(0, target - employed)
        job_demand[job_type.value] = demand

    return job_demand


def adjust_salaries(
    agents: list[AgentState],
    world: SimulationState,
    job_demand: Dict[str, int],
    rng: DeterministicRNG,
) -> Dict[str, float]:
    """Adjust salary multipliers based on job demand.

    For each job type: if demand > 0 (unfilled), increase multiplier by 0.01
    (cap +0.2 from 1.0). If demand <= 0 and there are unemployed agents,
    decrease multiplier by 0.01 (cap -0.2 from 1.0).

    Args:
        agents: All living agents.
        world: World state (modified in place with job_salary_multipliers).
        job_demand: Current job demand per job type.
        rng: Deterministic RNG.

    Returns:
        Dict mapping job type strings to current salary multipliers.
    """
    unemployed_count = sum(
        1 for a in agents if a.is_alive and a.job_type == JobType.UNEMPLOYED
    )

    multipliers: Dict[str, float] = dict(world.job_salary_multipliers)

    for job_type in JobType:
        if job_type == JobType.UNEMPLOYED:
            continue
        key = job_type.value
        current = multipliers.get(key, 1.0)
        demand = job_demand.get(key, 0)

        if demand > 0:
            current = min(1.2, current + 0.01)
        elif demand <= 0 and unemployed_count > 0:
            current = max(0.8, current - 0.01)

        multipliers[key] = current

    world.job_salary_multipliers = multipliers
    return multipliers


def maybe_change_job(
    agent: AgentState,
    all_agents: list[AgentState],
    job_demand: Dict[str, int],
    world: SimulationState,
    rng: DeterministicRNG,
) -> Optional[str]:
    """Unemployed or low-morale agents may seek new jobs.

    2% chance per tick. Picks a job with high demand weighted by demand level.

    Args:
        agent: The agent to consider for job change.
        all_agents: All living agents.
        job_demand: Current job demand per job type.
        world: World state.
        rng: Deterministic RNG.

    Returns:
        New job type string if job change occurs, None otherwise.
    """
    is_unemployed = agent.job_type == JobType.UNEMPLOYED or not agent.resources.employed
    low_morale = agent.unlust > 0.5

    if not is_unemployed and not low_morale:
        return None

    if rng.random() >= 0.02:
        return None

    high_demand_jobs = [jt for jt, demand in job_demand.items() if demand > 0]
    if not high_demand_jobs:
        return None

    weights = [float(job_demand[jt]) for jt in high_demand_jobs]
    new_job = rng.weighted_choice(high_demand_jobs, weights)
    return new_job


def update_unemployment_rate(
    agents: list[AgentState], world: SimulationState
) -> None:
    """Calculate and set world unemployment rate based on employed/alive ratio.

    Args:
        agents: All agents.
        world: World state (modified in place).
    """
    alive = [a for a in agents if a.is_alive]
    if not alive:
        world.unemployment_rate = 0.0
        return

    employed = sum(1 for a in alive if a.resources.employed)
    world.unemployment_rate = 1.0 - (employed / len(alive))
