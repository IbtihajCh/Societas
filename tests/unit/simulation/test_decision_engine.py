"""Tests for the decision engine — prompt building, dilemma detection,
LLM parsing, action validation, and deterministic fallback.
"""

from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
)
from shared.schemas.simulation_state import SimulationState
from shared.constants.defaults import (
    BASE_FOOD_COST,
    MORAL_DILEMMA_FOOD_THRESHOLD,
    MORAL_DILEMMA_MORALITY_THRESHOLD,
    MORAL_DILEMMA_UNLUST_THRESHOLD,
    SCARCITY_BASE,
)
from shared.types.aliases import AgentId, NeedValue
from shared.types.enums import ActionType, EmotionType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.decision_engine import (
    build_agent_prompt,
    build_moral_dilemma_prompt,
    deterministic_fallback,
    is_moral_dilemma,
    parse_llm_response,
    should_evaluate_this_tick,
    validate_action,
)


def _make_agent(
    agent_id: str = "0",
    food: float = 0.5,
    water: float = 0.5,
    sleep: float = 0.5,
    safety: float = 0.5,
    social: float = 0.5,
    esteem: float = 0.5,
    reputation: float = 0.5,
    money: float = 100.0,
    employed: bool = False,
    health: float = 1.0,
    morality: float = 0.5,
    anger_tendency: float = 0.5,
    ambition: float = 0.5,
    extraversion: float = 0.5,
    creativity: float = 0.5,
    resilience: float = 0.5,
    dominance_urge: float = 0.5,
    risk_tolerance: float = 0.5,
    emotion: EmotionType = EmotionType.NORMAL,
    happiness: float = 0.5,
    unlust: float = 0.0,
    trust_in_govt: float = 0.5,
    crimes_committed: int = 0,
    good_acts: int = 0,
    social_connections: list[AgentId] | None = None,
) -> AgentState:
    """Build an AgentState with the given parameters for testing."""
    needs = AgentNeeds(
        levels={
            NeedType.FOOD: NeedValue(food),
            NeedType.WATER: NeedValue(water),
            NeedType.SLEEP: NeedValue(sleep),
            NeedType.SAFETY: NeedValue(safety),
            NeedType.SOCIAL_CONNECTION: NeedValue(social),
            NeedType.SELF_ESTEEM: NeedValue(esteem),
            NeedType.REPUTATION: NeedValue(reputation),
        }
    )
    traits = AgentTraits(
        morality=morality,
        anger_tendency=anger_tendency,
        ambition=ambition,
        extraversion=extraversion,
        creativity=creativity,
        resilience=resilience,
        dominance_urge=dominance_urge,
        risk_tolerance=risk_tolerance,
    )
    resources = AgentResources(
        money=money,
        employed=employed,
        health=health,
    )
    emotions = AgentEmotions(
        primary=emotion,
        happiness_score=happiness,
    )
    return AgentState(
        id=AgentId(agent_id),
        needs=needs,
        traits=traits,
        resources=resources,
        emotions=emotions,
        unlust=unlust,
        trust_in_govt=trust_in_govt,
        crimes_committed=crimes_committed,
        good_acts=good_acts,
        social_connections=social_connections or [],
    )


def _make_world(
    tax_rate: float = 0.15,
    welfare_enabled: bool = False,
    food_availability: float = 0.85,
) -> SimulationState:
    """Build a SimulationState with the given parameters for testing."""
    return SimulationState(
        tax_rate=tax_rate,
        welfare_enabled=welfare_enabled,
        food_availability=food_availability,
    )


# =============================================================================
# Staggered scheduling
# =============================================================================


def test_should_evaluate_tick_0_agent_0() -> None:
    """agent_id='0', tick=0 → True (0%3==0)."""
    agent = _make_agent(agent_id="0")
    assert should_evaluate_this_tick(agent, 0) is True


def test_should_evaluate_tick_1_agent_0() -> None:
    """agent_id='0', tick=1 → False."""
    agent = _make_agent(agent_id="0")
    assert should_evaluate_this_tick(agent, 1) is False


def test_should_evaluate_tick_3_agent_0() -> None:
    """agent_id='0', tick=3 → True (3%3==0)."""
    agent = _make_agent(agent_id="0")
    assert should_evaluate_this_tick(agent, 3) is True


def test_should_evaluate_agent_1_offset() -> None:
    """agent_id='1', tick=1 → True, tick=0 → False."""
    agent = _make_agent(agent_id="1")
    assert should_evaluate_this_tick(agent, 1) is True
    assert should_evaluate_this_tick(agent, 0) is False


def test_should_evaluate_agent_2_offset() -> None:
    """agent_id='2', tick=2 → True, tick=0 → False."""
    agent = _make_agent(agent_id="2")
    assert should_evaluate_this_tick(agent, 2) is True
    assert should_evaluate_this_tick(agent, 0) is False


# =============================================================================
# Prompt building
# =============================================================================


def test_build_agent_prompt_contains_needs() -> None:
    """Prompt includes 'hunger=' and 'water='."""
    agent = _make_agent(food=0.3, water=0.7)
    world = _make_world()
    prompt = build_agent_prompt(agent, world, {})
    assert "hunger=" in prompt
    assert "water=" in prompt


def test_build_agent_prompt_contains_traits() -> None:
    """Prompt includes 'morality=' and 'anger='."""
    agent = _make_agent(morality=0.8, anger_tendency=0.3)
    world = _make_world()
    prompt = build_agent_prompt(agent, world, {})
    assert "morality=" in prompt
    assert "anger=" in prompt


def test_build_agent_prompt_contains_actions_list() -> None:
    """Prompt includes the comma-separated action list."""
    agent = _make_agent()
    world = _make_world()
    prompt = build_agent_prompt(agent, world, {})
    assert "work, buy_food, rest" in prompt


def test_build_agent_prompt_contains_json_format() -> None:
    """Prompt includes the JSON response format instruction."""
    agent = _make_agent()
    world = _make_world()
    prompt = build_agent_prompt(agent, world, {})
    assert '"action":"...","feeling":"...","reason":"one sentence"' in prompt


def test_build_moral_dilemma_prompt_has_think_token() -> None:
    """Moral dilemma prompt starts with '<|think|>'."""
    agent = _make_agent()
    world = _make_world()
    prompt = build_moral_dilemma_prompt(agent, world, {})
    assert prompt.startswith("<|think|>")


def test_build_moral_dilemma_prompt_contains_moral_framing() -> None:
    """Moral dilemma prompt includes 'moral dilemma' phrasing."""
    agent = _make_agent()
    world = _make_world()
    prompt = build_moral_dilemma_prompt(agent, world, {})
    assert "moral dilemma" in prompt


# =============================================================================
# Moral dilemma detection
# =============================================================================


def test_dilemma_starving_moral() -> None:
    """food=0.1, morality=0.6, unlust=0.6 → True."""
    agent = _make_agent(food=0.1, morality=0.6, unlust=0.6)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is True


def test_dilemma_starving_amoral() -> None:
    """food=0.1, morality=0.3, unlust=0.6 → False (low morality)."""
    agent = _make_agent(food=0.1, morality=0.3, unlust=0.6)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is False


def test_dilemma_angry_moral() -> None:
    """emotion=ANGRY, morality=0.7, unlust=0.6 → True."""
    agent = _make_agent(emotion=EmotionType.ANGRY, morality=0.7, unlust=0.6)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is True


def test_dilemma_angry_low_morality() -> None:
    """emotion=ANGRY, morality=0.4, unlust=0.6 → False."""
    agent = _make_agent(emotion=EmotionType.ANGRY, morality=0.4, unlust=0.6)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is False


def test_dilemma_despair_with_money() -> None:
    """emotion=DESPAIR, money=200 → True."""
    agent = _make_agent(emotion=EmotionType.DESPAIR, money=200)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is True


def test_dilemma_despair_no_money() -> None:
    """emotion=DESPAIR, money=50 → False."""
    agent = _make_agent(emotion=EmotionType.DESPAIR, money=50)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is False


def test_dilemma_high_unlust_dominance() -> None:
    """unlust=0.7, dominance=0.8 → True."""
    agent = _make_agent(unlust=0.7, dominance_urge=0.8)
    world = _make_world()
    assert is_moral_dilemma(agent, world) is True


def test_dilemma_financial_crisis_with_bonds() -> None:
    """money=30, social=0.6, connections=['1'] → True."""
    agent = _make_agent(money=30, social=0.6, social_connections=[AgentId("1")])
    world = _make_world()
    assert is_moral_dilemma(agent, world) is True


def test_dilemma_no_dilemma_normal() -> None:
    """Normal agent (defaults) → False."""
    agent = _make_agent()
    world = _make_world()
    assert is_moral_dilemma(agent, world) is False


# =============================================================================
# LLM response parsing
# =============================================================================


def test_parse_valid_json() -> None:
    """Valid JSON with action → dict with action='work'."""
    result = parse_llm_response(
        '{"action":"work","feeling":"tired","reason":"need money"}'
    )
    assert result is not None
    assert result["action"] == "work"


def test_parse_json_with_extra_text() -> None:
    """JSON embedded in surrounding text → parsed correctly."""
    result = parse_llm_response('Here is my response: {"action":"rest"} done')
    assert result is not None
    assert result["action"] == "rest"


def test_parse_invalid_json() -> None:
    """Completely invalid input → None."""
    result = parse_llm_response("not json at all")
    assert result is None


def test_parse_missing_action() -> None:
    """Valid JSON but missing 'action' key → None."""
    result = parse_llm_response('{"feeling":"sad"}')
    assert result is None


def test_parse_empty_string() -> None:
    """Empty string → None."""
    result = parse_llm_response("")
    assert result is None


# =============================================================================
# Action validation
# =============================================================================


def test_validate_valid_action() -> None:
    """'work' for employed agent → ActionType.WORK."""
    agent = _make_agent(employed=True)
    world = _make_world()
    assert validate_action(agent, "work", world) == ActionType.WORK


def test_validate_unknown_action() -> None:
    """'fly' (unknown action) → None."""
    agent = _make_agent()
    world = _make_world()
    assert validate_action(agent, "fly", world) is None


def test_validate_buy_food_no_money() -> None:
    """money=0, action='buy_food' → None (insufficient funds)."""
    agent = _make_agent(money=0)
    world = _make_world(food_availability=0.85)
    assert validate_action(agent, "buy_food", world) is None


def test_validate_buy_food_with_money() -> None:
    """money=100, action='buy_food' → ActionType.BUY_FOOD."""
    agent = _make_agent(money=100)
    world = _make_world(food_availability=0.85)
    assert validate_action(agent, "buy_food", world) == ActionType.BUY_FOOD


def test_validate_work_unemployed() -> None:
    """employed=False, action='work' → None."""
    agent = _make_agent(employed=False)
    world = _make_world()
    assert validate_action(agent, "work", world) is None


def test_validate_seek_job_employed() -> None:
    """employed=True, action='seek_job' → None."""
    agent = _make_agent(employed=True)
    world = _make_world()
    assert validate_action(agent, "seek_job", world) is None


def test_validate_steal_moral() -> None:
    """unlust=0.2, morality=0.8, action='steal' → None (morality blocks)."""
    agent = _make_agent(unlust=0.2, morality=0.8)
    world = _make_world()
    assert validate_action(agent, "steal", world) is None


def test_validate_steal_amoral() -> None:
    """unlust=0.85, morality=0.3, action='steal' → ActionType.STEAL."""
    agent = _make_agent(unlust=0.85, morality=0.3)
    world = _make_world()
    assert validate_action(agent, "steal", world) == ActionType.STEAL


def test_validate_case_insensitive() -> None:
    """'WORK' (uppercase) → ActionType.WORK."""
    agent = _make_agent(employed=True)
    world = _make_world()
    assert validate_action(agent, "WORK", world) == ActionType.WORK


def test_validate_with_whitespace() -> None:
    """'  work  ' (with surrounding whitespace) → ActionType.WORK."""
    agent = _make_agent(employed=True)
    world = _make_world()
    assert validate_action(agent, "  work  ", world) == ActionType.WORK


# =============================================================================
# Deterministic fallback
# =============================================================================


def test_fallback_critical_food_buy() -> None:
    """food=0.05, money=100 → BUY_FOOD (can afford it)."""
    agent = _make_agent(food=0.05, money=100, employed=True)
    world = _make_world(food_availability=0.85)
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.BUY_FOOD


def test_fallback_critical_food_steal() -> None:
    """food=0.05, money=0, unlust=0.85, morality=0.3 → STEAL (morality bypassed)."""
    agent = _make_agent(food=0.05, money=0, unlust=0.85, morality=0.3)
    world = _make_world(food_availability=0.85)
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.STEAL


def test_fallback_critical_food_beg() -> None:
    """food=0.05, money=0, unlust=0.2, morality=0.8 → BEG (morality blocks steal)."""
    agent = _make_agent(food=0.05, money=0, unlust=0.2, morality=0.8)
    world = _make_world(food_availability=0.85)
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.BEG


def test_fallback_unemployed() -> None:
    """employed=False → SEEK_JOB (Level 2)."""
    agent = _make_agent(employed=False)
    world = _make_world()
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.SEEK_JOB


def test_fallback_low_money_employed() -> None:
    """money=50, employed=True → WORK (Level 2, money < 120)."""
    agent = _make_agent(money=50, employed=True)
    world = _make_world()
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.WORK


def test_fallback_despair() -> None:
    """emotion=DESPAIR, money=500, employed=True → ISOLATE (Level 3)."""
    agent = _make_agent(emotion=EmotionType.DESPAIR, money=500, employed=True)
    world = _make_world()
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.ISOLATE


def test_fallback_angry_amoral() -> None:
    """emotion=ANGRY, unlust=0.7, morality=0.3, money=500, employed=True → PROTEST."""
    agent = _make_agent(
        emotion=EmotionType.ANGRY, unlust=0.7, morality=0.3, money=500, employed=True
    )
    world = _make_world()
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.PROTEST


def test_fallback_default_work() -> None:
    """Normal agent, employed=True → WORK (Level 3 final fallback)."""
    agent = _make_agent(money=200, employed=True)
    world = _make_world()
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.WORK


def test_fallback_default_rest() -> None:
    """Normal agent, employed=False → SEEK_JOB (Level 2 catches it)."""
    agent = _make_agent(employed=False)
    world = _make_world()
    rng = DeterministicRNG(seed=42)
    assert deterministic_fallback(agent, world, rng) == ActionType.SEEK_JOB


def test_fallback_deterministic() -> None:
    """Same agent + same world + same seed → same action."""
    agent = _make_agent(food=0.1, money=50, employed=True)
    world = _make_world(food_availability=0.85)
    rng1 = DeterministicRNG(seed=42)
    rng2 = DeterministicRNG(seed=42)
    result1 = deterministic_fallback(agent, world, rng1)
    result2 = deterministic_fallback(agent, world, rng2)
    assert result1 == result2
