"""Agent factory — creates agents with Beta-distributed traits and socioeconomic status."""

from shared.types.aliases import AgentId
from shared.types.enums import (
    Culture,
    EducationLevel,
    EmploymentStatus,
    Gender,
    JobType,
    NeedType,
    WealthClass,
)
from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
    get_age_bracket,
)
from shared.constants.defaults import GRID_SIZE
from shared.constants.simulation_constants import (
    BETA_PARAMS,
    CREATIVE_MIN_CREATIVITY,
    EDUCATION_BY_WEALTH,
    JOBS_BY_EDUCATION,
    LEADER_MIN_MORALITY,
    LEADER_MIN_REPUTATION,
    PROPERTY_OWNERSHIP,
    SALARY_RANGES,
    WEALTH_CLASS_DISTRIBUTION,
    WEALTH_CLASS_MONEY_RANGES,
)
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = ["create_agent", "create_initial_population"]


def _generate_traits(rng: DeterministicRNG) -> AgentTraits:
    """Generate Beta-distributed traits for a new agent.

    All traits use Beta(2,2) except anger_tendency which uses Beta(2,3)
    (skewed low — most agents are slow to anger).

    Args:
        rng: Deterministic RNG instance.

    Returns:
        AgentTraits with Beta-distributed values.
    """
    return AgentTraits(
        creativity=rng.beta(BETA_PARAMS["creativity"][0], BETA_PARAMS["creativity"][1]),
        morality=rng.beta(BETA_PARAMS["morality"][0], BETA_PARAMS["morality"][1]),
        anger_tendency=rng.beta(
            BETA_PARAMS["anger_tendency"][0], BETA_PARAMS["anger_tendency"][1]
        ),
        extraversion=rng.beta(
            BETA_PARAMS["extraversion"][0], BETA_PARAMS["extraversion"][1]
        ),
        ambition=rng.beta(BETA_PARAMS["ambition"][0], BETA_PARAMS["ambition"][1]),
        resilience=rng.beta(BETA_PARAMS["resilience"][0], BETA_PARAMS["resilience"][1]),
        dominance_urge=rng.beta(
            BETA_PARAMS["dominance_urge"][0], BETA_PARAMS["dominance_urge"][1]
        ),
        risk_tolerance=rng.beta(
            BETA_PARAMS["risk_tolerance"][0], BETA_PARAMS["risk_tolerance"][1]
        ),
    )


def _generate_socioeconomic(
    rng: DeterministicRNG,
) -> tuple[WealthClass, float, bool, EducationLevel, bool]:
    """Generate initial socioeconomic status.

    Args:
        rng: Deterministic RNG instance.

    Returns:
        Tuple of (wealth_class, money, employed, education, property_owned).
    """
    wealth_classes = list(WEALTH_CLASS_DISTRIBUTION.keys())
    weights = list(WEALTH_CLASS_DISTRIBUTION.values())
    wealth_class = rng.weighted_choice(wealth_classes, weights)

    low, high = WEALTH_CLASS_MONEY_RANGES[wealth_class]
    money = rng.uniform(low, high)

    employed = rng.random() < 0.88

    edu_classes = list(EDUCATION_BY_WEALTH[wealth_class].keys())
    edu_weights = list(EDUCATION_BY_WEALTH[wealth_class].values())
    education = rng.weighted_choice(edu_classes, edu_weights)

    property_owned = rng.random() < PROPERTY_OWNERSHIP[wealth_class]

    return wealth_class, money, employed, education, property_owned


def _generate_needs(
    rng: DeterministicRNG, property_owned: bool
) -> AgentNeeds:
    """Generate initial needs for a new agent.

    All needs start at moderately satisfied levels.

    Args:
        rng: Deterministic RNG instance.
        property_owned: Whether the agent owns property.

    Returns:
        AgentNeeds with initial values.
    """
    needs = AgentNeeds()
    needs.set_level(NeedType.FOOD, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.WATER, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.SLEEP, rng.uniform(0.6, 0.9))
    needs.set_level(NeedType.SEXUAL_TENSION, 0.0)
    needs.set_level(NeedType.SAFETY, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.FINANCIAL_SECURITY, 0.5)
    needs.set_level(NeedType.SHELTER, 1.0 if property_owned else 0.3)
    needs.set_level(NeedType.SOCIAL_CONNECTION, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.FAMILY_BOND, 0.5)
    needs.set_level(NeedType.ROMANTIC_BOND, 0.0)
    needs.set_level(NeedType.SELF_ESTEEM, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.REPUTATION, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.INFERIORITY_GAP, 0.0)
    return needs


def _assign_job_by_education(
    education: EducationLevel, rng: DeterministicRNG
) -> JobType:
    """Assign a job type based on education level.

    Args:
        education: The agent's education level.
        rng: Deterministic RNG instance.

    Returns:
        A JobType appropriate for the education level.
    """
    available_jobs = JOBS_BY_EDUCATION.get(education, [])
    if not available_jobs:
        return JobType.UNEMPLOYED
    return available_jobs[rng.choice(len(available_jobs))]


def _get_salary_for_job(job_type: JobType, rng: DeterministicRNG) -> float:
    """Generate a salary for a job type.

    Salary is per-tick (annual salary / 365 days, 1 tick = 1 day).

    Args:
        job_type: The job type.
        rng: Deterministic RNG instance.

    Returns:
        Salary per tick in pounds.
    """
    if job_type == JobType.UNEMPLOYED:
        return 0.0
    low, high = SALARY_RANGES.get(job_type, (10000, 20000))
    annual_salary = rng.uniform(low, high)
    return annual_salary / 365.0


def _generate_persona(age: int, gender: Gender, wealth_class: WealthClass, job_type: JobType, traits: AgentTraits) -> str:
    """Generate a rule-based persona description from agent attributes."""
    parts = []
    if age >= 66:
        if gender == Gender.MALE:
            parts.append("An elderly man")
        else:
            parts.append("An elderly woman")
    elif gender == Gender.MALE:
        if age < 19:
            parts.append("A young man")
        elif age < 41:
            parts.append("A man in early adulthood")
        else:
            parts.append("A man in midlife")
    else:
        if age < 19:
            parts.append("A young woman")
        elif age < 41:
            parts.append("A woman in early adulthood")
        else:
            parts.append("A woman in midlife")

    if job_type != JobType.UNEMPLOYED:
        parts.append(f"working as a {job_type.value.replace('_', ' ')}")
    else:
        parts.append("currently unemployed")

    if wealth_class == WealthClass.POOR:
        parts.append("with limited financial means")
    elif wealth_class == WealthClass.MIDDLE:
        parts.append("with a stable middle-class income")
    elif wealth_class == WealthClass.RICH:
        parts.append("enjoying comfortable wealth")
    elif wealth_class == WealthClass.BUSINESS_OWNER:
        parts.append("running their own business")

    if traits.creativity > 0.7:
        parts.append("curious and open to new experiences")
    elif traits.creativity < 0.3:
        parts.append("preferring routine and familiarity")

    if traits.ambition > 0.7:
        parts.append("disciplined and organized")
    elif traits.ambition < 0.3:
        parts.append("somewhat easygoing and spontaneous")

    if traits.extraversion > 0.7:
        parts.append("outgoing and sociable")
    elif traits.extraversion < 0.3:
        parts.append("reserved and introspective")

    if traits.morality > 0.7:
        parts.append("kind and cooperative")
    elif traits.morality < 0.3:
        parts.append("competitive and outspoken")

    if traits.resilience < 0.3 or traits.anger_tendency > 0.7:
        parts.append("prone to worry and stress")
    elif traits.resilience > 0.7 and traits.anger_tendency < 0.3:
        parts.append("emotionally resilient")

    if traits.morality > 0.7:
        parts.append("with a strong moral compass")
    elif traits.morality < 0.3:
        parts.append("with flexible ethics")

    if traits.creativity > 0.7:
        parts.append("and a creative mind")
    elif traits.creativity < 0.3:
        parts.append("with a practical mindset")

    return ". ".join(parts) + "."


def create_agent(agent_id: int, rng: DeterministicRNG) -> AgentState:
    """Create a complete agent with all v1 parameters.

    Args:
        agent_id: Sequential agent ID starting from 0.
        rng: Deterministic RNG instance.

    Returns:
        A fully initialized AgentState.
    """
    traits = _generate_traits(rng)
    wealth_class, money, employed, education, property_owned = _generate_socioeconomic(rng)
    needs = _generate_needs(rng, property_owned)

    job_type = JobType.UNEMPLOYED
    base_salary = 0.0
    if employed:
        job_type = _assign_job_by_education(education, rng)
        base_salary = _get_salary_for_job(job_type, rng)
        if traits.creativity > CREATIVE_MIN_CREATIVITY and rng.random() < 0.05:
            creative_jobs = [JobType.ARTIST, JobType.WRITER, JobType.MUSICIAN]
            job_type = creative_jobs[rng.choice(len(creative_jobs))]
            base_salary = _get_salary_for_job(job_type, rng)

    gender = Gender.MALE if rng.random() < 0.5 else Gender.FEMALE
    cultures = [Culture.A, Culture.B, Culture.C]
    culture = cultures[rng.choice(len(cultures))]

    health = rng.uniform(0.7, 1.0)

    # Initial age distribution: 60% young adult (19-40), 30% middle adult (41-65),
    # 10% elderly (66-100).  Age 18 belongs to the *child* bracket per
    # AGE_CHILD_MAX, so young adults start at 19.
    age_roll = rng.random()
    if age_roll < 0.6:
        age = int(rng.uniform(19, 41))
    elif age_roll < 0.9:
        age = int(rng.uniform(41, 66))
    else:
        age = int(rng.uniform(66, 101))

    age_bracket = get_age_bracket(age)

    persona = _generate_persona(age, gender, wealth_class, job_type, traits)

    return AgentState(
        id=AgentId(str(agent_id)),
        persona=persona,
        traits=traits,
        needs=needs,
        emotions=AgentEmotions(happiness_score=0.5),
        resources=AgentResources(
            money=money,
            wealth=money,
            base_salary=base_salary,
            employed=employed,
            education=education,
            property=property_owned,
            health=health,
        ),
        employment_status=EmploymentStatus.EMPLOYED if employed else EmploymentStatus.UNEMPLOYED,
        wealth_class=wealth_class,
        age=age,
        age_bracket=age_bracket,
        gender=gender,
        culture=culture,
        born_tick=0,
        grid_x=int(rng.integers(0, GRID_SIZE)),
        grid_y=int(rng.integers(0, GRID_SIZE)),
        job_type=job_type,
    )


def _assign_community_leader(
    agents: list[AgentState],
    rng: DeterministicRNG,
) -> None:
    """Assign up to one community leader from the initial population.

    An agent qualifies if their reputation need > LEADER_MIN_REPUTATION
    and their morality > LEADER_MIN_MORALITY.

    Args:
        agents: List of agents to scan (modified in place).
        rng: Deterministic RNG instance.
    """
    candidates = [
        a for a in agents
        if a.is_alive
        and a.needs.get_level(NeedType.REPUTATION) > LEADER_MIN_REPUTATION
        and a.traits.morality > LEADER_MIN_MORALITY
    ]
    if not candidates:
        return
    leader = candidates[0]
    leader.job_type = JobType.COMMUNITY_LEADER
    leader.resources.employed = True
    leader.resources.base_salary = _get_salary_for_job(JobType.COMMUNITY_LEADER, rng)


def create_initial_population(
    n_agents: int, rng: DeterministicRNG
) -> list[AgentState]:
    """Create the initial population of agents.

    After creation, up to one agent with high reputation and morality
    is assigned the COMMUNITY_LEADER job.

    Args:
        n_agents: Number of agents to create.
        rng: Deterministic RNG instance.

    Returns:
        List of AgentState objects.
    """
    agents = [create_agent(i, rng) for i in range(n_agents)]
    _assign_community_leader(agents, rng)
    return agents
