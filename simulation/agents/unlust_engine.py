"""Unlust engine — computes the Freudian Unlust (dissatisfaction) score.

The Unlust score measures how far below satisfactory each core need is.
Only deficits below 0.5 count — being above 0.5 on a need does NOT reduce Unlust.
Range: 0.0 (fully satisfied) to 1.0 (maximally desperate).
"""

from shared.types.enums import NeedType
from shared.schemas.agent_state import AgentState
from shared.constants.defaults import (
    ANGRY_UNLUST_THRESHOLD,
    DESPAIR_UNLUST_THRESHOLD,
    UNLUST_FINANCIAL_DIVISOR,
    UNLUST_FINANCIAL_WEIGHT,
    UNLUST_FOOD_WEIGHT,
    UNLUST_MORALITY_GATE,
    UNLUST_SAFETY_WEIGHT,
    UNLUST_SOCIAL_WEIGHT,
    UNLUST_WATER_WEIGHT,
)

__all__ = [
    "compute_unlust",
    "morality_active",
    "is_thanatos_active",
    "get_unlust_state",
]


def compute_unlust(agent: AgentState) -> float:
    """Compute the Freudian Unlust score (0.0-1.0).

    Formula (exact from Guide):
        unlust = (max(0, 0.5 - food)    * 0.28)
               + (max(0, 0.5 - water)   * 0.22)
               + (max(0, 0.5 - safety)  * 0.20)
               + (max(0, 0.5 - social)  * 0.12)
               + (max(0, 1.0 - (money/600)) * 0.18)

    Only counts deficit below 0.5 for each need.
    Money deficit is relative to the 600 threshold.

    Args:
        agent: The agent to compute Unlust for.

    Returns:
        Unlust score in [0.0, 1.0].
    """
    food = agent.needs.get_level(NeedType.FOOD)
    water = agent.needs.get_level(NeedType.WATER)
    safety = agent.needs.get_level(NeedType.SAFETY)
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    money_ratio = min(1.0, agent.resources.money / UNLUST_FINANCIAL_DIVISOR)

    unlust = (
        max(0.0, 0.5 - food) * UNLUST_FOOD_WEIGHT
        + max(0.0, 0.5 - water) * UNLUST_WATER_WEIGHT
        + max(0.0, 0.5 - safety) * UNLUST_SAFETY_WEIGHT
        + max(0.0, 0.5 - social) * UNLUST_SOCIAL_WEIGHT
        + max(0.0, 1.0 - money_ratio) * UNLUST_FINANCIAL_WEIGHT
    )

    return min(1.0, max(0.0, unlust))


def morality_active(unlust: float, morality: float) -> bool:
    """Check if morality gate is active for this agent.

    - Unlust < 0.58: fully moral (returns True)
    - Unlust 0.58-0.82: partial — only if morality > 0.6
    - Unlust > 0.82: morality completely bypassed (returns False)

    Args:
        unlust: Current Unlust score (0.0-1.0).
        morality: Agent's morality trait (0.0-1.0).

    Returns:
        True if morality should gate criminal/harmful actions.
    """
    if unlust < UNLUST_MORALITY_GATE:
        return True
    elif unlust < DESPAIR_UNLUST_THRESHOLD:
        return morality > 0.6
    else:
        return False


def is_thanatos_active(unlust: float, morality: float) -> bool:
    """Check if the Thanatos (death drive) is active.

    Thanatos activates when unlust > 0.65 AND morality is NOT active.
    This unlocks harm_other and steal actions even outside critical survival.

    Args:
        unlust: Current Unlust score.
        morality: Agent's morality trait.

    Returns:
        True if Thanatos drive is active.
    """
    return unlust > 0.65 and not morality_active(unlust, morality)


def get_unlust_state(unlust: float) -> str:
    """Return the unlust state label.

    Args:
        unlust: Unlust score (0.0-1.0).

    Returns:
        One of: "content", "stressed", "driven", "desperate".
    """
    if unlust < 0.30:
        return "content"
    elif unlust < ANGRY_UNLUST_THRESHOLD:
        return "stressed"
    elif unlust < DESPAIR_UNLUST_THRESHOLD:
        return "driven"
    else:
        return "desperate"
