"""Purpose/Meaning System — Maslow Layer 5 for SOCIETAS agents.

Handles purpose assignment, purpose fulfillment tracking, self-actualization
effects, and existential despair death conditions.
"""

from shared.constants.defaults import (
    EXISTENTIAL_DEATH_CHANCE,
    PURPOSE_ASSIGN_CHANCE,
    PURPOSE_DESPAIR_RISK,
    PURPOSE_FULFILLMENT_DECAY,
    PURPOSE_FULFILLMENT_GAIN,
    PURPOSE_HAPPINESS_BONUS,
)
from shared.schemas.agent_state import AgentState
from shared.types.enums import ActionType, JobType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG

_PURPOSE_LIST = ["art", "community", "knowledge", "power", "family"]


def assign_purpose(agent: AgentState, rng: DeterministicRNG) -> None:
    """Assign a purpose to an agent if they are eligible and unassigned.

    Eligibility: self-esteem > 0.6 AND food > 0.5 AND water > 0.5 AND safety > 0.5.
    Purpose is assigned with PURPOSE_ASSIGN_CHANCE per tick from a curated list.

    Args:
        agent: Agent to potentially assign a purpose to (modified in place).
        rng: Deterministic RNG for the probability roll.
    """
    if agent.purpose is not None:
        return
    if agent.needs.get_level(NeedType.SELF_ESTEEM) <= 0.6:
        return
    if agent.needs.get_level(NeedType.FOOD) <= 0.5:
        return
    if agent.needs.get_level(NeedType.WATER) <= 0.5:
        return
    if agent.needs.get_level(NeedType.SAFETY) <= 0.5:
        return
    if rng.random() < PURPOSE_ASSIGN_CHANCE:
        agent.purpose = rng.choice(len(_PURPOSE_LIST))
        agent.purpose = _PURPOSE_LIST[agent.purpose]


def update_purpose_fulfillment(
    agent: AgentState,
    last_action: ActionType,
    action_result: dict,
    rng: DeterministicRNG,
) -> float:
    """Update an agent's purpose fulfillment based on their last action.

    Each purpose type has specific actions that increase fulfillment.
    Irrelevant actions cause fulfillment to decay.

    Args:
        agent: Agent whose fulfillment is being updated (modified in place).
        last_action: The action the agent last performed.
        action_result: Result data from the last action (unused currently).
        rng: Deterministic RNG (reserved for future stochastic extensions).

    Returns:
        The net change in fulfillment for this tick.
    """
    if agent.purpose is None or agent.purpose == "none":
        return 0.0

    change = -PURPOSE_FULFILLMENT_DECAY

    if agent.purpose == "art":
        if last_action == ActionType.WORK and agent.traits.creativity > 0.6:
            change = PURPOSE_FULFILLMENT_GAIN

    elif agent.purpose == "community":
        if last_action in (ActionType.BEFRIEND, ActionType.CONSOLE, ActionType.SHARE):
            change = 0.015

    elif agent.purpose == "knowledge":
        if last_action == ActionType.WORK and agent.job_type in (
            JobType.ENGINEER,
            JobType.COMPUTER_SCIENTIST,
        ):
            change = 0.01

    elif agent.purpose == "power":
        if last_action in (ActionType.PROTEST, ActionType.HARM_OTHER, ActionType.SPREAD_RUMOR):
            change = 0.01

    elif agent.purpose == "family":
        if last_action == ActionType.SUPPORT_FAMILY:
            change = 0.01

    agent.purpose_fulfillment = max(0.0, min(1.0, agent.purpose_fulfillment + change))
    return change


def apply_self_actualization_effects(agent: AgentState) -> None:
    """Apply happiness, unlust, and creativity effects based on purpose fulfillment.

    High fulfillment (>0.6): happiness bonus, unlust reduction, creative professions unlocked.
    Low fulfillment (<0.3): despair risk increase, happiness penalty.

    Args:
        agent: Agent to apply effects to (modified in place).
    """
    if agent.purpose is None or agent.purpose == "none":
        return

    fulfillment = agent.purpose_fulfillment
    agent.self_actualization_drive = fulfillment

    if fulfillment > 0.6:
        agent.emotions.happiness_score = min(
            1.0, agent.emotions.happiness_score + PURPOSE_HAPPINESS_BONUS
        )
        agent.unlust = max(0.0, agent.unlust - 0.02)
        agent.creativity_unlocked = True
    elif fulfillment < 0.3:
        agent.emotions.happiness_score = max(
            0.0, agent.emotions.happiness_score - 0.03
        )
        agent.unlust = min(1.0, agent.unlust + PURPOSE_DESPAIR_RISK)


def check_self_actualization_death(agent: AgentState, rng: DeterministicRNG) -> bool:
    """Check if an agent dies from existential despair.

    Conditions: purpose_fulfillment < 0.05 for 10+ consecutive ticks
    AND all basic needs (food, water, safety) > 0.5.

    On death, sets agent.cause_of_death to "existential_despair".

    Args:
        agent: Agent to evaluate (modified in place on death).
        rng: Deterministic RNG for the probability roll.

    Returns:
        True if the agent should die this tick, False otherwise.
    """
    if not agent.is_alive:
        return False
    if agent.purpose is None or agent.purpose == "none":
        return False

    if agent.purpose_fulfillment >= 0.05:
        agent.metadata["purpose_despair_ticks"] = 0
        return False

    despair_ticks = agent.metadata.get("purpose_despair_ticks", 0) + 1
    agent.metadata["purpose_despair_ticks"] = despair_ticks

    if despair_ticks >= 10:
        food = agent.needs.get_level(NeedType.FOOD)
        water = agent.needs.get_level(NeedType.WATER)
        safety = agent.needs.get_level(NeedType.SAFETY)
        if food > 0.5 and water > 0.5 and safety > 0.5:
            if rng.random() < EXISTENTIAL_DEATH_CHANCE:
                agent.cause_of_death = "existential_despair"
                return True

    return False
