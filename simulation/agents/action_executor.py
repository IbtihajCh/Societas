"""Action executor — executes all 14 agent actions with deterministic state updates."""

from shared.types.enums import ActionType, EmotionType, NeedType, EmploymentStatus, WealthClass
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.constants.defaults import (
    BASE_FOOD_COST,
    SCARCITY_BASE,
    SEEK_JOB_BASE_CHANCE,
    BEG_MAX_AMOUNT,
    STEAL_PERCENTAGE_CAP,
    STEAL_AMOUNT_CAP,
    SHARE_PERCENTAGE,
    REPUTATION_CHANGE_GOOD,
    REPUTATION_CHANGE_CRIMINAL,
    SALARY_MULTIPLIER_POOR,
    SALARY_MULTIPLIER_MIDDLE,
    SALARY_MULTIPLIER_RICH,
    FOOD_COST_MULTIPLIER_POOR,
    FOOD_COST_MULTIPLIER_MIDDLE,
    FOOD_COST_MULTIPLIER_RICH,
)
from shared.constants.simulation_constants import (
    SALARY_RANGES,
    JOBS_BY_EDUCATION,
)
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.emotion_engine import emotion_productivity_mod
from simulation.agents.unlust_engine import morality_active

__all__ = ["execute_action", "get_nearby_agents", "compute_nearby_counts", "move_agent"]


def get_nearby_agents(agent: AgentState, all_agents: list[AgentState]) -> list[AgentState]:
    """Return all living agents within INTERACTION_RADIUS of the given agent.

    Uses toroidal Euclidean distance on the grid.

    Args:
        agent: The agent to find neighbors for.
        all_agents: All agents in the simulation.

    Returns:
        List of nearby living agents (excluding self).
    """
    from shared.constants.defaults import GRID_SIZE, INTERACTION_RADIUS

    nearby: list[AgentState] = []
    for other in all_agents:
        if other.id == agent.id or not other.is_alive:
            continue
        dist = _toroidal_distance(
            int(agent.grid_x), int(agent.grid_y),
            int(other.grid_x), int(other.grid_y),
            GRID_SIZE,
        )
        if dist <= INTERACTION_RADIUS:
            nearby.append(other)
    return nearby


def _toroidal_distance(x1: int, y1: int, x2: int, y2: int, grid_size: int) -> float:
    """Euclidean distance on a toroidal (wrapping) grid."""
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    dx = min(dx, grid_size - dx)
    dy = min(dy, grid_size - dy)
    return (dx * dx + dy * dy) ** 0.5


def compute_nearby_counts(agent: AgentState, all_agents: list[AgentState]) -> dict[str, int]:
    """Compute counts of nearby agent types for utility scoring and prompts.

    Args:
        agent: The agent to compute counts for.
        all_agents: All agents in the simulation.

    Returns:
        Dict with keys: 'agents', 'protesters', 'needy', 'sad', 'generous'.
    """
    nearby = get_nearby_agents(agent, all_agents)
    return {
        "agents": len(nearby),
        "protesters": sum(1 for a in nearby if a.emotions.primary == EmotionType.ANGRY),
        "needy": sum(1 for a in nearby if a.resources.money < 50),
        "sad": sum(
            1
            for a in nearby
            if a.emotions.primary in (EmotionType.SAD, EmotionType.DESPAIR)
        ),
        "generous": sum(1 for a in nearby if a.traits.morality > 0.6),
    }


def move_agent(agent: AgentState, rng: DeterministicRNG) -> None:
    """Move agent 1-2 random walk steps. Angry agents move more (restlessness).

    Args:
        agent: The agent to move (modified in place).
        rng: Deterministic RNG.
    """
    from shared.constants.defaults import GRID_SIZE

    steps = 1 + int(rng.integers(0, 2))
    if agent.emotions.primary == EmotionType.ANGRY:
        steps += 1

    for _ in range(steps):
        dx = int(rng.integers(-1, 2))
        dy = int(rng.integers(-1, 2))
        agent.grid_x = type(agent.grid_x)((int(agent.grid_x) + dx) % GRID_SIZE)
        agent.grid_y = type(agent.grid_y)((int(agent.grid_y) + dy) % GRID_SIZE)


def execute_action(
    agent: AgentState,
    action: ActionType,
    world: SimulationState,
    all_agents: list[AgentState],
    rng: DeterministicRNG,
) -> AgentActionResult:
    """Execute a selected action and return the result.

    Args:
        agent: The agent performing the action.
        action: The action to execute.
        world: Current world state.
        all_agents: All agents (for interactions).
        rng: Deterministic RNG.

    Returns:
        AgentActionResult with action, outcome, and score_delta.
    """
    result = AgentActionResult(
        agent_id=agent.id,
        action=action,
        outcome="",
        score_delta={},
    )

    if action == ActionType.WORK:
        _do_work(agent, world, result)
    elif action == ActionType.BUY_FOOD:
        _do_buy_food(agent, world, result)
    elif action == ActionType.REST:
        _do_rest(agent, rng, result)
    elif action == ActionType.SEEK_JOB:
        _do_seek_job(agent, world, rng, result)
    elif action == ActionType.BEG:
        _do_beg(agent, all_agents, world, rng, result)
    elif action == ActionType.BEFRIEND:
        _do_befriend(agent, all_agents, world, rng, result)
    elif action == ActionType.CONSOLE:
        _do_console(agent, all_agents, world, rng, result)
    elif action == ActionType.ISOLATE:
        _do_isolate(agent, result)
    elif action == ActionType.SHARE:
        _do_share(agent, all_agents, world, rng, result)
    elif action == ActionType.STEAL:
        _do_steal(agent, all_agents, world, rng, result)
    elif action == ActionType.HARM_OTHER:
        _do_harm_other(agent, all_agents, world, rng, result)
    elif action == ActionType.PROTEST:
        _do_protest(agent, world, result)
    elif action == ActionType.COMPLAIN:
        _do_complain(agent, all_agents, world, rng, result)
    elif action == ActionType.COMPLY:
        result.outcome = "complied"
    else:
        result.outcome = "idle"

    # Update last action
    agent.last_action = action

    return result


def _do_work(agent: AgentState, world: SimulationState, result: AgentActionResult) -> None:
    """Work action: earn salary minus tax, modified by productivity, creativity, and wealth class."""
    salary = agent.resources.base_salary * (1.0 - world.tax_rate)
    productivity = emotion_productivity_mod(agent.emotions.primary)
    creativity_mod = 1.0 + (agent.traits.creativity - 0.5) * 0.4
    if agent.wealth_class == WealthClass.POOR:
        salary_mult = SALARY_MULTIPLIER_POOR
    elif agent.wealth_class == WealthClass.MIDDLE:
        salary_mult = SALARY_MULTIPLIER_MIDDLE
    else:
        salary_mult = SALARY_MULTIPLIER_RICH
    income = salary * productivity * creativity_mod * salary_mult

    agent.resources.money += income
    agent.resources.wealth = agent.resources.money

    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.015)

    result.outcome = f"earned £{income:.2f}"
    result.score_delta = {"money": income}


def _do_buy_food(agent: AgentState, world: SimulationState, result: AgentActionResult) -> None:
    """Buy food action: spend money, increase food and water needs."""
    scarcity = SCARCITY_BASE - world.food_availability
    if agent.wealth_class == WealthClass.POOR:
        food_mult = FOOD_COST_MULTIPLIER_POOR
    elif agent.wealth_class == WealthClass.MIDDLE:
        food_mult = FOOD_COST_MULTIPLIER_MIDDLE
    else:
        food_mult = FOOD_COST_MULTIPLIER_RICH
    food_cost = BASE_FOOD_COST * scarcity * food_mult

    if agent.resources.money < food_cost:
        result.outcome = "insufficient_funds"
        result.score_delta = {"money": 0.0}
        return

    agent.resources.money -= food_cost
    agent.resources.wealth = agent.resources.money

    food = agent.needs.get_level(NeedType.FOOD)
    water = agent.needs.get_level(NeedType.WATER)
    agent.needs.set_level(NeedType.FOOD, food + 0.30)
    agent.needs.set_level(NeedType.WATER, water + 0.20)

    result.outcome = f"bought food for £{food_cost:.2f}"
    result.score_delta = {"food": 0.30, "water": 0.20, "money": -food_cost}


def _do_rest(agent: AgentState, rng: DeterministicRNG, result: AgentActionResult) -> None:
    """Rest action: increase sleep, may break angry state."""
    sleep = agent.needs.get_level(NeedType.SLEEP)
    agent.needs.set_level(NeedType.SLEEP, sleep + 0.30)

    if agent.emotions.primary == EmotionType.ANGRY:
        if rng.random() < 0.30:
            agent.emotions.primary = EmotionType.NORMAL
            agent.emotions.emotion_timer = 0

    result.outcome = "rested"
    result.score_delta = {"sleep": 0.30}


def _do_seek_job(
    agent: AgentState, world: SimulationState, rng: DeterministicRNG, result: AgentActionResult
) -> None:
    """Seek job action: chance to become employed based on unemployment rate and ambition."""
    chance = SEEK_JOB_BASE_CHANCE * (1.0 - world.unemployment_rate) * (0.5 + agent.traits.ambition)

    if rng.random() < chance:
        agent.resources.employed = True
        agent.employment_status = EmploymentStatus.EMPLOYED
        available_jobs = JOBS_BY_EDUCATION.get(agent.resources.education, [])
        if available_jobs:
            agent.job_type = available_jobs[int(rng.choice(len(available_jobs)))]
        else:
            agent.job_type = available_jobs[0] if available_jobs else agent.job_type

        low, high = SALARY_RANGES.get(agent.job_type, (10000, 20000))
        agent.resources.base_salary = rng.uniform(low, high) / 365.0

        result.outcome = f"got job: {agent.job_type.name}"
        result.score_delta = {"employment": 1.0}
    else:
        result.outcome = "still_looking"
        result.score_delta = {}


def _do_beg(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Beg action: receive small money from nearby generous agents."""
    nearby = get_nearby_agents(agent, all_agents)
    generous = [a for a in nearby if a.traits.morality > 0.6]

    total_received = 0.0
    for g in generous:
        if g.resources.money > 10:
            donation = min(g.resources.money * 0.02, BEG_MAX_AMOUNT)
            g.resources.money -= donation
            g.resources.wealth = g.resources.money
            total_received += donation

    agent.resources.money += total_received
    agent.resources.wealth = agent.resources.money

    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep - 0.02)

    result.outcome = f"received £{total_received:.2f}"
    result.score_delta = {"money": total_received, "reputation": -0.02}


def _do_befriend(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Befriend action: increase social connection for both agents."""
    nearby = get_nearby_agents(agent, all_agents)
    if not nearby:
        result.outcome = "no_one_nearby"
        return

    eligible = [
        a for a in nearby
        if a.id not in agent.enemies
        and agent.needs.get_level(NeedType.REPUTATION) > 0.25
    ]
    if not eligible:
        result.outcome = "no_eligible_targets"
        return

    other = eligible[int(rng.choice(len(eligible)))]

    if rng.random() < 0.55:
        social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
        agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.12)

        other_social = other.needs.get_level(NeedType.SOCIAL_CONNECTION)
        other.needs.set_level(NeedType.SOCIAL_CONNECTION, other_social + 0.10)

        if other.id not in agent.social_connections:
            agent.social_connections.append(other.id)
        if agent.id not in other.social_connections:
            other.social_connections.append(agent.id)

        agent.needs.set_level(
            NeedType.REPUTATION,
            agent.needs.get_level(NeedType.REPUTATION) + 0.02,
        )
        other.needs.set_level(
            NeedType.REPUTATION,
            other.needs.get_level(NeedType.REPUTATION) + 0.02,
        )

        result.outcome = f"befriended {other.id}"
        result.score_delta = {"social": 0.12}
    else:
        result.outcome = "rejected"


def _do_console(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Console action: help a sad nearby agent, increase both social."""
    nearby = get_nearby_agents(agent, all_agents)
    sad_agents = [
        a for a in nearby
        if a.emotions.primary in (EmotionType.SAD, EmotionType.DESPAIR)
    ]

    if not sad_agents:
        result.outcome = "no_sad_nearby"
        return

    other = sad_agents[int(rng.choice(len(sad_agents)))]

    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.05)
    agent.good_acts += 1

    other_social = other.needs.get_level(NeedType.SOCIAL_CONNECTION)
    other.needs.set_level(NeedType.SOCIAL_CONNECTION, other_social + 0.08)
    other.emotions.emotion_timer = 0

    result.outcome = f"consoled {other.id}"
    result.score_delta = {"social": 0.05}


def _do_isolate(agent: AgentState, result: AgentActionResult) -> None:
    """Isolate action: further reduce social connection (despair state)."""
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social - 0.02)
    result.outcome = "isolated"
    result.score_delta = {"social": -0.02}


def _do_share(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Share action: give 6% of money to a nearby needy agent."""
    nearby = get_nearby_agents(agent, all_agents)
    needy = [a for a in nearby if a.resources.money < 50]

    if not needy:
        result.outcome = "no_needy_nearby"
        return

    other = needy[int(rng.choice(len(needy)))]

    amount = agent.resources.money * SHARE_PERCENTAGE
    agent.resources.money -= amount
    agent.resources.wealth = agent.resources.money
    other.resources.money += amount
    other.resources.wealth = other.resources.money

    agent.emotions.happiness_score = min(1.0, agent.emotions.happiness_score + 0.04)

    other_food = other.needs.get_level(NeedType.FOOD)
    other.needs.set_level(NeedType.FOOD, other_food + 0.05)

    agent.good_acts += 1
    agent.needs.set_level(
        NeedType.REPUTATION,
        agent.needs.get_level(NeedType.REPUTATION) + 0.03,
    )

    result.outcome = f"shared £{amount:.2f} with {other.id}"
    result.score_delta = {"money": -amount, "happiness": 0.04}


def _do_steal(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Steal action: take up to 18% of victim's money, capped at £60."""
    nearby = get_nearby_agents(agent, all_agents)
    if not nearby:
        result.outcome = "no_victim_nearby"
        return

    victim = nearby[int(rng.choice(len(nearby)))]

    stolen = min(victim.resources.money * STEAL_PERCENTAGE_CAP, STEAL_AMOUNT_CAP)
    if stolen <= 0:
        result.outcome = "victim_has_no_money"
        return

    agent.resources.money += stolen
    agent.resources.wealth = agent.resources.money
    victim.resources.money -= stolen
    victim.resources.wealth = victim.resources.money

    food = agent.needs.get_level(NeedType.FOOD)
    agent.needs.set_level(NeedType.FOOD, food + 0.08)

    agent.crimes_committed += 1
    agent.notoriety = min(1.0, agent.notoriety + 0.05)

    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep + REPUTATION_CHANGE_CRIMINAL)

    victim_safety = victim.needs.get_level(NeedType.SAFETY)
    victim.needs.set_level(NeedType.SAFETY, victim_safety - 0.12)

    if victim.emotions.primary not in (EmotionType.ANGRY, EmotionType.DESPAIR):
        victim.emotions.primary = EmotionType.ANGRY
        victim.emotions.emotion_timer = 2

    result.outcome = f"stole £{stolen:.2f} from {victim.id}"
    result.score_delta = {"money": stolen}


def _do_harm_other(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Harm other action: reduce victim's safety, make them angry."""
    nearby = get_nearby_agents(agent, all_agents)
    if not nearby:
        result.outcome = "no_victim_nearby"
        return

    victim = nearby[int(rng.choice(len(nearby)))]

    agent.crimes_committed += 1
    agent.notoriety = min(1.0, agent.notoriety + 0.05)

    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep - 0.10)

    victim_safety = victim.needs.get_level(NeedType.SAFETY)
    victim.needs.set_level(NeedType.SAFETY, victim_safety - 0.18)

    if victim.emotions.primary not in (EmotionType.ANGRY, EmotionType.DESPAIR):
        victim.emotions.primary = EmotionType.ANGRY
        victim.emotions.emotion_timer = 3

    agent.resources.health = max(0.0, agent.resources.health - 0.01)

    result.outcome = f"harmed {victim.id}"
    result.score_delta = {"reputation": -0.10}


def _do_protest(agent: AgentState, world: SimulationState, result: AgentActionResult) -> None:
    """Protest action: increase protest count, boost social solidarity."""
    agent.protest_count += 1

    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    agent.needs.set_level(NeedType.SOCIAL_CONNECTION, social + 0.06)

    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep + 0.01)

    agent.trust_in_govt = max(0.0, agent.trust_in_govt - 0.02)

    result.outcome = "protested"
    result.score_delta = {"social": 0.06}


def _do_complain(
    agent: AgentState,
    all_agents: list[AgentState],
    world: SimulationState,
    rng: DeterministicRNG,
    result: AgentActionResult,
) -> None:
    """Complain action: spread discontent to nearby agents (mild contagion)."""
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep + 0.02)

    nearby = get_nearby_agents(agent, all_agents)
    for other in nearby:
        if rng.random() < 0.15:
            other.trust_in_govt = max(0.0, other.trust_in_govt - 0.01)

    result.outcome = "complained"
    result.score_delta = {"reputation": 0.02}
