"""Tests for the Emotion engine — happiness, state machine, sleep reset, and modifiers.

Verifies compute_happiness, update_emotion, apply_sleep_reset, and
the three modifier functions (productivity, creativity, social).
"""

from copy import deepcopy

import pytest

from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
)
from shared.types.aliases import AgentId, NeedValue
from shared.types.enums import EmotionType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.emotion_engine import (
    apply_sleep_reset,
    compute_happiness,
    emotion_creativity_mod,
    emotion_productivity_mod,
    emotion_social_mod,
    update_emotion,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(
    *,
    food: float = 0.5,
    water: float = 0.5,
    safety: float = 0.5,
    social: float = 0.5,
    sleep: float = 0.5,
    self_esteem: float = 0.5,
    financial: float = 0.5,
    reputation: float = 0.5,
    health: float = 1.0,
    employed: bool = False,
    unlust: float = 0.0,
    resilience: float = 0.5,
    anger_tendency: float = 0.5,
    happiness_score: float = 0.5,
    primary_emotion: EmotionType = EmotionType.NORMAL,
    emotion_timer: int = 0,
) -> AgentState:
    """Build an AgentState with the given need levels, traits, and emotion state."""
    needs = AgentNeeds(
        levels={
            NeedType.FOOD: NeedValue(food),
            NeedType.WATER: NeedValue(water),
            NeedType.SAFETY: NeedValue(safety),
            NeedType.SOCIAL_CONNECTION: NeedValue(social),
            NeedType.SLEEP: NeedValue(sleep),
            NeedType.SELF_ESTEEM: NeedValue(self_esteem),
            NeedType.FINANCIAL_SECURITY: NeedValue(financial),
            NeedType.REPUTATION: NeedValue(reputation),
        }
    )
    resources = AgentResources(health=health, employed=employed)
    traits = AgentTraits(resilience=resilience, anger_tendency=anger_tendency)
    emotions = AgentEmotions(
        primary=primary_emotion,
        happiness_score=happiness_score,
        emotion_timer=emotion_timer,
    )
    return AgentState(
        id=AgentId("test-agent"),
        needs=needs,
        resources=resources,
        traits=traits,
        emotions=emotions,
        unlust=unlust,
    )


# ===========================================================================
# Happiness tests
# ===========================================================================


class TestHappiness:
    """Composite happiness score computation."""

    def test_happiness_all_satisfied(self) -> None:
        """All needs=1.0, health=1.0, unlust=0.0, employed=True -> happiness close to 1.0."""
        agent = _make_agent(
            food=1.0, water=1.0, safety=1.0, social=1.0, sleep=1.0,
            self_esteem=1.0, financial=1.0, reputation=1.0,
            health=1.0, employed=True, unlust=0.0,
        )
        score = compute_happiness(agent)
        # Max possible with employed bonus: weights sum to ~1.0, plus 0.05 bonus
        # 1.0 * (0.11+0.09+0.09+0.09+0.08+0.08+0.08) + 1.0*0.13 + 1.0*0.05 + (1-0)*0.15 + 0.05
        # = 0.62 + 0.13 + 0.05 + 0.15 + 0.05 = 1.0
        assert score == pytest.approx(1.0)

    def test_happiness_all_deprived(self) -> None:
        """All needs=0.0, health=0.0, unlust=1.0, employed=False -> happiness close to 0.0."""
        agent = _make_agent(
            food=0.0, water=0.0, safety=0.0, social=0.0, sleep=0.0,
            self_esteem=0.0, financial=0.0, reputation=0.0,
            health=0.0, employed=False, unlust=1.0,
        )
        score = compute_happiness(agent)
        # (1-1)*0.15 = 0, employed bonus = 0, health*0.13 = 0
        # All need contributions are 0 * w = 0
        assert score == pytest.approx(0.0)

    def test_happiness_employed_bonus(self) -> None:
        """Same agent, employed=True vs False -> employed version is +0.05 higher."""
        agent_base = _make_agent(
            food=0.5, water=0.5, safety=0.5, social=0.5, sleep=0.5,
            self_esteem=0.5, financial=0.5, reputation=0.5,
            health=0.5, employed=False, unlust=0.2,
        )
        agent_employed = deepcopy(agent_base)
        agent_employed.resources.employed = True

        base_score = compute_happiness(agent_base)
        employed_score = compute_happiness(agent_employed)

        assert employed_score == pytest.approx(base_score + 0.05)

    def test_happiness_clamped(self) -> None:
        """Even with all max values, happiness <= 1.0."""
        agent = _make_agent(
            food=1.0, water=1.0, safety=1.0, social=1.0, sleep=1.0,
            self_esteem=1.0, financial=1.0, reputation=1.0,
            health=1.0, employed=True, unlust=0.0,
        )
        score = compute_happiness(agent)
        assert score <= 1.0
        assert score >= 0.0

    def test_happiness_deterministic(self) -> None:
        """Same agent state -> same happiness (pure function)."""
        agent = _make_agent(
            food=0.3, water=0.7, safety=0.9, social=0.4, sleep=0.6,
            self_esteem=0.8, financial=0.5, reputation=0.7,
            health=0.8, employed=True, unlust=0.3,
        )
        assert compute_happiness(agent) == compute_happiness(agent)
        assert compute_happiness(agent) == compute_happiness(agent)


# ===========================================================================
# Emotion state machine tests
# ===========================================================================


class TestEmotionStateMachine:
    """5-state emotion machine with hysteresis timers."""

    def test_emotion_normal_default(self) -> None:
        """New agent, happiness=0.5, unlust=0.2 -> NORMAL."""
        agent = _make_agent(happiness_score=0.5, unlust=0.2)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.NORMAL
        assert agent.emotions.emotion_timer == 0

    def test_emotion_happy(self) -> None:
        """happiness=0.8, unlust=0.1 -> HAPPY, timer=0."""
        agent = _make_agent(happiness_score=0.8, unlust=0.1)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.HAPPY
        assert agent.emotions.emotion_timer == 0

    def test_emotion_sad(self) -> None:
        """happiness=0.2, unlust=0.1 -> SAD, timer=2."""
        agent = _make_agent(happiness_score=0.2, unlust=0.1)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.SAD
        expected_timer = max(1, int(2 * (1.0 - 0.5 * 0.5)))  # resilience=0.5
        assert agent.emotions.emotion_timer == expected_timer

    def test_emotion_angry(self) -> None:
        """unlust=0.65, anger_tendency=0.6 -> ANGRY, timer=3."""
        agent = _make_agent(unlust=0.65, anger_tendency=0.6)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.ANGRY
        expected_timer = max(1, int(3 * (1.0 - 0.5 * 0.5)))  # resilience=0.5
        assert agent.emotions.emotion_timer == expected_timer

    def test_emotion_angry_low_anger_tendency(self) -> None:
        """unlust=0.65, anger_tendency=0.3 -> NOT ANGRY (anger_tendency <= 0.4)."""
        agent = _make_agent(happiness_score=0.5, unlust=0.65, anger_tendency=0.3)
        update_emotion(agent, DeterministicRNG(42))
        # Should fall through to happy/normal check — happiness=0.5 is neither happy nor sad
        assert agent.emotions.primary != EmotionType.ANGRY
        assert agent.emotions.primary == EmotionType.NORMAL

    def test_emotion_despair(self) -> None:
        """unlust=0.85 -> DESPAIR, timer=4."""
        agent = _make_agent(unlust=0.85)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.DESPAIR
        expected_timer = max(1, int(4 * (1.0 - 0.5 * 0.5)))  # resilience=0.5
        assert agent.emotions.emotion_timer == expected_timer

    def test_emotion_priority_despair_over_angry(self) -> None:
        """unlust=0.85, anger_tendency=0.9 -> DESPAIR (not ANGRY)."""
        agent = _make_agent(unlust=0.85, anger_tendency=0.9, happiness_score=0.5)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.DESPAIR

    def test_emotion_priority_angry_over_sad(self) -> None:
        """unlust=0.65, anger_tendency=0.6, happiness=0.2 -> ANGRY (not SAD)."""
        agent = _make_agent(unlust=0.65, anger_tendency=0.6, happiness_score=0.2)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.ANGRY

    def test_emotion_timer_lock(self) -> None:
        """Set emotion_timer=2, call update_emotion -> timer decrements to 1, emotion stays same."""
        agent = _make_agent(
            happiness_score=0.5, unlust=0.1,
            primary_emotion=EmotionType.SAD, emotion_timer=2,
        )
        update_emotion(agent, DeterministicRNG(42))
        # Timer decremented, emotion unchanged (locked)
        assert agent.emotions.emotion_timer == 1
        assert agent.emotions.primary == EmotionType.SAD

    def test_emotion_timer_expires(self) -> None:
        """Set emotion_timer=1, call update_emotion -> timer becomes 0, re-evaluates next call."""
        agent = _make_agent(
            happiness_score=0.5, unlust=0.1,
            primary_emotion=EmotionType.SAD, emotion_timer=1,
        )
        # First call: timer decrements to 0, returns early (no re-evaluation yet)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.emotion_timer == 0
        assert agent.emotions.primary == EmotionType.SAD  # still locked until next call

        # Second call: timer is 0, so re-evaluates -> happiness=0.5, unlust=0.1 -> NORMAL
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.NORMAL

    def test_resilience_shortens_timer(self) -> None:
        """resilience=1.0, despair -> timer = 4*(1-0.5) = 2."""
        agent = _make_agent(unlust=0.85, resilience=1.0)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.DESPAIR
        assert agent.emotions.emotion_timer == max(1, int(4 * (1.0 - 1.0 * 0.5)))

    def test_resilience_zero_full_timer(self) -> None:
        """resilience=0.0, despair -> timer = 4."""
        agent = _make_agent(unlust=0.85, resilience=0.0)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.DESPAIR
        assert agent.emotions.emotion_timer == 4

    def test_resilience_half_timer(self) -> None:
        """resilience=0.5, despair -> timer = 4*(1-0.25) = 3."""
        agent = _make_agent(unlust=0.85, resilience=0.5)
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.primary == EmotionType.DESPAIR
        assert agent.emotions.emotion_timer == 3

    def test_happy_no_timer(self) -> None:
        """HAPPY state has timer=0 (exits when score drops)."""
        agent = _make_agent(
            happiness_score=0.8, unlust=0.1,
            primary_emotion=EmotionType.HAPPY, emotion_timer=2,
        )
        # Timer decrements
        update_emotion(agent, DeterministicRNG(42))
        assert agent.emotions.emotion_timer == 1
        assert agent.emotions.primary == EmotionType.HAPPY

    def test_sad_timer_with_resilience(self) -> None:
        """Sad state with resilience > 0 shortens the timer appropriately."""
        # resilience=0.0 -> timer = 2
        agent_low = _make_agent(unlust=0.1, happiness_score=0.2, resilience=0.0)
        update_emotion(agent_low, DeterministicRNG(42))
        assert agent_low.emotions.emotion_timer == 2

        # resilience=1.0 -> timer = max(1, int(2 * (1 - 0.5))) = max(1, 1) = 1
        agent_high = _make_agent(unlust=0.1, happiness_score=0.2, resilience=1.0)
        update_emotion(agent_high, DeterministicRNG(42))
        assert agent_high.emotions.emotion_timer == 1


# ===========================================================================
# Sleep reset tests
# ===========================================================================


class TestSleepReset:
    """Sleep-based emotional reset."""

    def test_sleep_reset_good_sleep(self) -> None:
        """safety=0.9, unlust=0.1, resilience=0.8 -> sleep_quality=0.648 > 0.5 -> resets to NORMAL."""
        agent = _make_agent(
            safety=0.9, unlust=0.1, resilience=0.8,
            primary_emotion=EmotionType.SAD, emotion_timer=3,
        )
        apply_sleep_reset(agent)
        assert agent.emotions.primary == EmotionType.NORMAL
        assert agent.emotions.emotion_timer == 0

    def test_sleep_reset_moderate_sleep(self) -> None:
        """safety=0.6, unlust=0.2, resilience=0.7 -> sleep_quality=0.336, between 0.3 and 0.5 -> halves timer."""
        agent = _make_agent(
            safety=0.6, unlust=0.2, resilience=0.7,
            primary_emotion=EmotionType.SAD, emotion_timer=5,
        )
        apply_sleep_reset(agent)
        # Timer should be halved: 5 // 2 = 2
        assert agent.emotions.emotion_timer == 2
        # Emotion unchanged
        assert agent.emotions.primary == EmotionType.SAD

    def test_sleep_reset_insomnia(self) -> None:
        """safety=0.2, unlust=0.7, resilience=0.3 -> sleep_quality=0.018 < 0.3 -> no reset."""
        agent = _make_agent(
            safety=0.2, unlust=0.7, resilience=0.3,
            primary_emotion=EmotionType.SAD, emotion_timer=3,
        )
        apply_sleep_reset(agent)
        # No change
        assert agent.emotions.primary == EmotionType.SAD
        assert agent.emotions.emotion_timer == 3

    def test_sleep_reset_exact_threshold_good(self) -> None:
        """sleep_quality exactly at 0.5 -> reset (strictly greater)."""
        agent = _make_agent(
            safety=0.8, unlust=0.0, resilience=0.625,
            primary_emotion=EmotionType.ANGRY, emotion_timer=3,
        )
        # sleep_quality = 0.8 * 1.0 * 0.625 = 0.5 -> exactly equal, NOT greater
        apply_sleep_reset(agent)
        # 0.5 is not > 0.5, so should NOT reset
        assert agent.emotions.primary == EmotionType.ANGRY
        # 0.5 > 0.3, so halves the timer
        assert agent.emotions.emotion_timer == 1  # 3 // 2 = 1

    def test_sleep_reset_exact_threshold_moderate(self) -> None:
        """sleep_quality exactly at 0.3 -> halves timer (strictly greater check)."""
        agent = _make_agent(
            safety=0.6, unlust=0.0, resilience=0.5,
            primary_emotion=EmotionType.ANGRY, emotion_timer=4,
        )
        # sleep_quality = 0.6 * 1.0 * 0.5 = 0.3 -> not > 0.3, so no halving
        apply_sleep_reset(agent)
        assert agent.emotions.primary == EmotionType.ANGRY
        assert agent.emotions.emotion_timer == 4  # unchanged


# ===========================================================================
# Modifier tests
# ===========================================================================


class TestModifiers:
    """Emotion-based modifier multipliers."""

    @pytest.mark.parametrize(
        "emotion, expected",
        [
            (EmotionType.HAPPY, 1.20),
            (EmotionType.NORMAL, 1.00),
            (EmotionType.SAD, 0.70),
            (EmotionType.ANGRY, 0.90),
            (EmotionType.DESPAIR, 0.40),
        ],
    )
    def test_productivity_modifiers(self, emotion: EmotionType, expected: float) -> None:
        """Productivity multiplier matches expected values."""
        assert emotion_productivity_mod(emotion) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "emotion, expected",
        [
            (EmotionType.HAPPY, 1.30),
            (EmotionType.NORMAL, 1.00),
            (EmotionType.SAD, 0.80),
            (EmotionType.ANGRY, 0.90),
            (EmotionType.DESPAIR, 0.50),
        ],
    )
    def test_creativity_modifiers(self, emotion: EmotionType, expected: float) -> None:
        """Creativity multiplier matches expected values."""
        assert emotion_creativity_mod(emotion) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "emotion, expected",
        [
            (EmotionType.HAPPY, 1.40),
            (EmotionType.NORMAL, 1.00),
            (EmotionType.SAD, 0.70),
            (EmotionType.ANGRY, 0.50),
            (EmotionType.DESPAIR, 0.20),
        ],
    )
    def test_social_modifiers(self, emotion: EmotionType, expected: float) -> None:
        """Social multiplier matches expected values."""
        assert emotion_social_mod(emotion) == pytest.approx(expected)
