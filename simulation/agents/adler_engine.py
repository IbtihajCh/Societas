"""Adler comparison engine — social comparison on Maslow hierarchy.

When two agents interact, they compare their overall life situation.
Upward comparison (other is better off) -> inferiority_gap up, self_esteem down, unlust up.
Downward comparison (self is better off) -> self_esteem up, unlust down.
"""

from shared.types.enums import NeedType
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.constants.defaults import (
    ADLER_GAP_THRESHOLD,
    ADLER_INFERIORITY_GAIN_PER_GAP,
    ADLER_SELF_ESTEEM_CHANGE_PER_GAP,
    ADLER_UNLUST_CHANGE_PER_GAP,
    ADLER_DOMINANCE_CHANGE_PER_GAP,
    ADLER_SUPERIORITY_GAIN,
)

__all__ = ["compute_maslow_score", "adler_comparison"]


def compute_maslow_score(agent: AgentState) -> float:
    """Compute a weighted Maslow hierarchy score for comparison.

    Higher layers weighted more (self-actualization > esteem > social > safety > physiological).
    This represents the agent's overall life satisfaction across the hierarchy.

    Args:
        agent: The agent to compute the score for.

    Returns:
        A float score in [0.0, 1.0] representing overall hierarchy position.
    """
    needs = agent.needs
    score = (
        needs.get_level(NeedType.FOOD) * 0.10
        + needs.get_level(NeedType.WATER) * 0.10
        + needs.get_level(NeedType.SLEEP) * 0.08
        + needs.get_level(NeedType.SAFETY) * 0.12
        + needs.get_level(NeedType.FINANCIAL_SECURITY) * 0.10
        + needs.get_level(NeedType.SOCIAL_CONNECTION) * 0.12
        + needs.get_level(NeedType.SELF_ESTEEM) * 0.13
        + needs.get_level(NeedType.REPUTATION) * 0.10
        + agent.emotions.happiness_score * 0.15
    )
    return min(1.0, max(0.0, score))


def adler_comparison(
    agent: AgentState,
    other: AgentState,
    world: SimulationState,
) -> None:
    """Perform Adlerian social comparison between two agents.

    Compares the agent's Maslow score against the other's.
    If the other is more than ADLER_GAP_THRESHOLD better off (upward comparison):
        - inferiority_gap increases proportional to the gap
        - self_esteem decreases proportional to the gap
        - unlust increases proportional to the gap
        - dominance_urge increases (compensatory drive)
    If the agent is more than ADLER_GAP_THRESHOLD better off (downward comparison):
        - self_esteem increases
        - inferiority_gap decreases slightly
        - unlust decreases slightly

    Args:
        agent: The agent doing the comparing (modified in place).
        other: The agent being compared against.
        world: Current world state (unused but kept for interface).
    """
    self_score = compute_maslow_score(agent)
    other_score = compute_maslow_score(other)
    gap = other_score - self_score

    if gap > ADLER_GAP_THRESHOLD:
        # Upward comparison -- other is better off
        inferiority = agent.needs.get_level(NeedType.INFERIORITY_GAP)
        agent.needs.set_level(
            NeedType.INFERIORITY_GAP,
            inferiority + gap * ADLER_INFERIORITY_GAIN_PER_GAP,
        )

        self_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
        agent.needs.set_level(
            NeedType.SELF_ESTEEM,
            self_esteem - gap * ADLER_SELF_ESTEEM_CHANGE_PER_GAP,
        )

        agent.unlust = min(1.0, agent.unlust + gap * ADLER_UNLUST_CHANGE_PER_GAP)

        agent.traits.dominance_urge = min(
            1.0, agent.traits.dominance_urge + gap * ADLER_DOMINANCE_CHANGE_PER_GAP
        )

    elif gap < -ADLER_GAP_THRESHOLD:
        # Downward comparison -- self is better off
        self_esteem = agent.needs.get_level(NeedType.SELF_ESTEEM)
        agent.needs.set_level(
            NeedType.SELF_ESTEEM,
            self_esteem + ADLER_SUPERIORITY_GAIN,
        )

        inferiority = agent.needs.get_level(NeedType.INFERIORITY_GAP)
        agent.needs.set_level(
            NeedType.INFERIORITY_GAP,
            inferiority - 0.02,
        )

        agent.unlust = max(0.0, agent.unlust - 0.02)
