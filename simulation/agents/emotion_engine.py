"""Emotion engine — 5-state emotion machine with timers, happiness, and sleep reset.

Emotion states: HAPPY, NORMAL, SAD, ANGRY, DESPAIR.
Priority: despair > angry > sad > happy > normal.
Timers use hysteresis — once in a state with a timer, agent is locked until timer expires.
Resilience shortens timers: timer = base * (1 - resilience * 0.5).
"""

from shared.constants.defaults import (
    ANGRY_TENDENCY_THRESHOLD,
    ANGRY_TIMER,
    ANGRY_UNLUST_THRESHOLD,
    DESPAIR_TIMER,
    DESPAIR_UNLUST_THRESHOLD,
    HAPPINESS_EMPLOYED_BONUS,
    HAPPINESS_FINANCIAL_WEIGHT,
    HAPPINESS_FOOD_WEIGHT,
    HAPPINESS_HEALTH_WEIGHT,
    HAPPINESS_REPUTATION_WEIGHT,
    HAPPINESS_SAFETY_WEIGHT,
    HAPPINESS_SELF_ESTEEM_WEIGHT,
    HAPPINESS_SLEEP_WEIGHT,
    HAPPINESS_SOCIAL_WEIGHT,
    HAPPINESS_UNLUST_WEIGHT,
    HAPPINESS_WATER_WEIGHT,
    HAPPY_THRESHOLD,
    SAD_THRESHOLD,
    SAD_TIMER,
    SLEEP_HALF_TIMER_THRESHOLD,
    SLEEP_RESET_THRESHOLD,
)
from shared.schemas.agent_state import AgentState
from shared.types.enums import EmotionType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "compute_happiness",
    "update_emotion",
    "apply_sleep_reset",
    "emotion_productivity_mod",
    "emotion_creativity_mod",
    "emotion_social_mod",
]


def compute_happiness(agent: AgentState, world: object = None) -> float:
    """Compute the composite happiness score (0.0-1.0).

    Weighted sum of need satisfaction, Unlust inverse, health, and employment.
    Weights reflect Maslow priority — physiological needs weighted highest.

    Optional `world` (a SimulationState) is consulted for:
      - Wealth-based happiness bonus (peaks at 50k money)
      - Tax pain for rich when tax_rate > 0.2

    Args:
        agent: The agent to compute happiness for.
        world: Optional world state (for tax_rate, etc.). If None, no
            wealth or tax adjustments applied (backwards compatible).

    Returns:
        Happiness score in [0.0, 1.0].
    """
    needs = agent.needs

    score = (
        needs.get_level(NeedType.FOOD) * HAPPINESS_FOOD_WEIGHT
        + needs.get_level(NeedType.WATER) * HAPPINESS_WATER_WEIGHT
        + needs.get_level(NeedType.SAFETY) * HAPPINESS_SAFETY_WEIGHT
        + needs.get_level(NeedType.SOCIAL_CONNECTION) * HAPPINESS_SOCIAL_WEIGHT
        + needs.get_level(NeedType.SLEEP) * HAPPINESS_SLEEP_WEIGHT
        + needs.get_level(NeedType.SELF_ESTEEM) * HAPPINESS_SELF_ESTEEM_WEIGHT
        + needs.get_level(NeedType.FINANCIAL_SECURITY) * HAPPINESS_FINANCIAL_WEIGHT
        + agent.resources.health * HAPPINESS_HEALTH_WEIGHT
        + needs.get_level(NeedType.REPUTATION) * HAPPINESS_REPUTATION_WEIGHT
        + (1.0 - agent.unlust) * HAPPINESS_UNLUST_WEIGHT
        + (HAPPINESS_EMPLOYED_BONUS if agent.resources.employed else 0.0)
    )

    # Wealth-based happiness bonus: peaks at £50k money, with diminishing
    # returns. Being rich is positive but doesn't dominate. Uses 0.05 max
    # so it can't override physiological needs. Threshold of £100 to avoid
    # rounding artifacts at near-zero money (e.g. destitute agents).
    money = getattr(agent.resources, "money", 0.0)
    wealth_bonus = 0.05 * min(1.0, max(0.0, money - 100.0) / 49900.0)
    score += wealth_bonus

    # Tax pain: rich agents suffer when tax_rate is high (>0.2). Linear
    # ramp from 0 at tax=0.2 to -0.15 at tax=0.9. Only applied to RICH
    # class (the user wants being rich to be good but taxes to hurt).
    if world is not None and getattr(agent, "wealth_class", None) is not None:
        from shared.types.enums import WealthClass

        if agent.wealth_class == WealthClass.RICH:
            tax_rate = getattr(world, "tax_rate", 0.0)
            if tax_rate > 0.2:
                tax_pain = -0.15 * (tax_rate - 0.2) / 0.7
                score += tax_pain

    return min(1.0, max(0.0, score))


def update_emotion(agent: AgentState, rng: DeterministicRNG) -> None:
    """Update the agent's emotion state machine.

    Uses hysteresis: once in a state with a timer, the agent is locked
    until the timer expires. Resilience shortens the timer.

    Priority: despair > angry > sad > happy > normal.

    Args:
        agent: The agent whose emotion is being updated.
        rng: Deterministic RNG instance (unused but kept for interface consistency).
    """
    emotions = agent.emotions

    # If timer active, decrement and stay in current state
    if emotions.emotion_timer > 0:
        emotions.emotion_timer -= 1
        return

    # Re-evaluate (timer expired or was 0)
    unlust = agent.unlust
    happiness = emotions.happiness_score
    anger_tendency = agent.traits.anger_tendency
    resilience = agent.traits.resilience

    # Priority: despair > angry > sad > happy > normal
    if unlust > DESPAIR_UNLUST_THRESHOLD:
        emotions.primary = EmotionType.DESPAIR
        base_timer = DESPAIR_TIMER
        emotions.emotion_timer = max(1, int(base_timer * (1.0 - resilience * 0.5)))
    elif unlust > ANGRY_UNLUST_THRESHOLD and anger_tendency > ANGRY_TENDENCY_THRESHOLD:
        emotions.primary = EmotionType.ANGRY
        base_timer = ANGRY_TIMER
        emotions.emotion_timer = max(1, int(base_timer * (1.0 - resilience * 0.5)))
    elif happiness < SAD_THRESHOLD:
        emotions.primary = EmotionType.SAD
        base_timer = SAD_TIMER
        emotions.emotion_timer = max(1, int(base_timer * (1.0 - resilience * 0.5)))
    elif happiness > HAPPY_THRESHOLD:
        emotions.primary = EmotionType.HAPPY
        emotions.emotion_timer = 0
    else:
        emotions.primary = EmotionType.NORMAL
        emotions.emotion_timer = 0


def apply_sleep_reset(agent: AgentState) -> None:
    """Apply sleep-based emotional reset.

    Agents with unmet needs sleep less (insomnia), meaning
    negative states persist longer. Never overrides negative
    emotions (SAD, ANGRY, DESPAIR) — sleep may improve mood
    but does not cure despair, anger, or sadness.

    sleep_quality = safety * (1 - unlust) * resilience

    - sleep_quality > 0.5: reset to NORMAL immediately (only if
      current emotion is HAPPY or NORMAL)
    - sleep_quality > 0.3: halve the timer (only if current
      emotion is HAPPY or NORMAL)
    - else: insomnia, no reset

    Args:
        agent: The agent to apply sleep reset to.
    """
    # Never override negative emotions
    if agent.emotions.primary in (EmotionType.SAD, EmotionType.ANGRY, EmotionType.DESPAIR):
        return

    sleep_quality = (
        agent.needs.get_level(NeedType.SAFETY) * (1.0 - agent.unlust) * agent.traits.resilience
    )

    if sleep_quality > SLEEP_RESET_THRESHOLD:
        agent.emotions.primary = EmotionType.NORMAL
        agent.emotions.emotion_timer = 0
    elif sleep_quality > SLEEP_HALF_TIMER_THRESHOLD:
        agent.emotions.emotion_timer = agent.emotions.emotion_timer // 2


def emotion_productivity_mod(emotion: EmotionType) -> float:
    """Return the productivity multiplier for an emotion state.

    Args:
        emotion: The emotion state.

    Returns:
        Productivity multiplier (HAPPY=1.2, NORMAL=1.0, SAD=0.7, ANGRY=0.9, DESPAIR=0.4).
    """
    return {
        EmotionType.HAPPY: 1.20,
        EmotionType.NORMAL: 1.00,
        EmotionType.SAD: 0.70,
        EmotionType.ANGRY: 0.90,
        EmotionType.DESPAIR: 0.40,
    }.get(emotion, 1.0)


def emotion_creativity_mod(emotion: EmotionType) -> float:
    """Return the creativity multiplier for an emotion state.

    Args:
        emotion: The emotion state.

    Returns:
        Creativity multiplier (HAPPY=1.3, NORMAL=1.0, SAD=0.8, ANGRY=0.9, DESPAIR=0.5).
    """
    return {
        EmotionType.HAPPY: 1.30,
        EmotionType.NORMAL: 1.00,
        EmotionType.SAD: 0.80,
        EmotionType.ANGRY: 0.90,
        EmotionType.DESPAIR: 0.50,
    }.get(emotion, 1.0)


def emotion_social_mod(emotion: EmotionType) -> float:
    """Return the social action multiplier for an emotion state.

    Args:
        emotion: The emotion state.

    Returns:
        Social multiplier (HAPPY=1.4, NORMAL=1.0, SAD=0.7, ANGRY=0.5, DESPAIR=0.2).
    """
    return {
        EmotionType.HAPPY: 1.40,
        EmotionType.NORMAL: 1.00,
        EmotionType.SAD: 0.70,
        EmotionType.ANGRY: 0.50,
        EmotionType.DESPAIR: 0.20,
    }.get(emotion, 1.0)
