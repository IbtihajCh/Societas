"""Decision engine — E2B hybrid decision architecture.

Builds prompts for the LLM agent brain, detects moral dilemmas for 26B escalation,
parses LLM responses, validates actions, and provides deterministic fallback.
"""

import json
from typing import Any

from shared.types.enums import ActionType, EmotionType, NeedType
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.constants.defaults import (
    ANGRY_UNLUST_THRESHOLD,
    BASE_FOOD_COST,
    DESPAIR_UNLUST_THRESHOLD,
    MORAL_DILEMMA_FOOD_THRESHOLD,
    MORAL_DILEMMA_MORALITY_THRESHOLD,
    MORAL_DILEMMA_UNLUST_THRESHOLD,
    SCARCITY_BASE,
)
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.unlust_engine import morality_active

__all__ = [
    "build_agent_prompt",
    "build_moral_dilemma_prompt",
    "is_moral_dilemma",
    "parse_llm_response",
    "validate_action",
    "deterministic_fallback",
    "should_evaluate_this_tick",
]


def should_evaluate_this_tick(agent: AgentState, current_tick: int) -> bool:
    """Check if this agent should re-evaluate its decision this tick.

    Agents are staggered so only 1/3 call the LLM per tick.
    Offset is determined by agent_id % 3.

    Args:
        agent: The agent to check.
        current_tick: Current simulation tick number.

    Returns:
        True if this agent should re-evaluate this tick.
    """
    return current_tick % 3 == int(agent.id) % 3


def build_agent_prompt(
    agent: AgentState,
    world: SimulationState,
    nearby_counts: dict[str, int],
) -> str:
    """Build a structured prompt for the E2B agent brain.

    Includes ALL factors the agent should consider — even slight trait differences
    matter. The LLM sees the full picture.

    Args:
        agent: The agent state.
        world: Current world state.
        nearby_counts: Dict with keys 'agents', 'protesters', 'needy', 'sad', 'generous'.

    Returns:
        A structured prompt string (~200 tokens).
    """
    needs = agent.needs
    traits = agent.traits

    return (
        f"You are a person in a society simulation. Your situation:\n"
        f"hunger={needs.get_level(NeedType.FOOD):.2f} water={needs.get_level(NeedType.WATER):.2f}\n"
        f"sleep={needs.get_level(NeedType.SLEEP):.2f} safety={needs.get_level(NeedType.SAFETY):.2f}\n"
        f"social={needs.get_level(NeedType.SOCIAL_CONNECTION):.2f} esteem={needs.get_level(NeedType.SELF_ESTEEM):.2f}\n"
        f"money={agent.resources.money:.0f} employed={agent.resources.employed} job={agent.job_type.name}\n"
        f"mood={agent.emotions.primary.name.lower()} happiness={agent.emotions.happiness_score:.2f}\n"
        f"unlust={agent.unlust:.2f} health={agent.resources.health:.2f} reputation={needs.get_level(NeedType.REPUTATION):.2f}\n"
        f"morality={traits.morality:.2f} anger={traits.anger_tendency:.2f} ambition={traits.ambition:.2f}\n"
        f"extraversion={traits.extraversion:.2f} creativity={traits.creativity:.2f} resilience={traits.resilience:.2f}\n"
        f"dominance={traits.dominance_urge:.2f} risk={traits.risk_tolerance:.2f}\n"
        f"trust_govt={agent.trust_in_govt:.2f} crimes={agent.crimes_committed} good_acts={agent.good_acts}\n"
        f"nearby={nearby_counts.get('agents', 0)} protesters_near={nearby_counts.get('protesters', 0)} needy_near={nearby_counts.get('needy', 0)}\n"
        f"tax_rate={world.tax_rate:.2f} welfare={world.welfare_enabled} food_avail={world.food_availability:.2f}\n"
        f"\nWhat do you do? Choose ONE:\n"
        f"work, buy_food, rest, seek_job, beg, befriend, console, isolate,\n"
        f"share, steal, harm_other, protest, complain, comply, idle\n"
        f'\nRespond EXACTLY: {{"action":"...","feeling":"...","reason":"one sentence"}}'
    )


def build_moral_dilemma_prompt(
    agent: AgentState,
    world: SimulationState,
    nearby_counts: dict[str, int],
) -> str:
    """Build a prompt for the 26B A4B moral reasoning model.

    Uses thinking mode for chain-of-thought reasoning. Richer context with
    moral framing.

    Args:
        agent: The agent state.
        world: Current world state.
        nearby_counts: Dict with nearby agent counts.

    Returns:
        A structured prompt string with <|think|> token.
    """
    return (
        f"<|think|>\n"
        f"You are a person facing a moral dilemma in a society simulation.\n\n"
        f"Your situation:\n"
        f"- Hunger: {agent.needs.get_level(NeedType.FOOD):.2f} (0=starving, 1=full)\n"
        f"- Money: \u00a3{agent.resources.money:.0f}\n"
        f"- Morality: {agent.traits.morality:.2f} (0=selfish, 1=saintly)\n"
        f"- Unlust: {agent.unlust:.2f} (0=content, 1=desperate)\n"
        f"- Emotion: {agent.emotions.primary.name.lower()}\n"
        f"- Anger tendency: {agent.traits.anger_tendency:.2f}\n"
        f"- Resilience: {agent.traits.resilience:.2f}\n"
        f"- Social connections: {len(agent.social_connections)} people\n"
        f"- Trust in government: {agent.trust_in_govt:.2f}\n"
        f"- Nearby people: {nearby_counts.get('agents', 0)}, protesters: {nearby_counts.get('protesters', 0)}\n"
        f"- World: tax={world.tax_rate:.0%}, food_avail={world.food_availability:.0%}, "
        f"welfare={'on' if world.welfare_enabled else 'off'}\n\n"
        f"Think carefully about what this person would actually do, given their personality\n"
        f"and situation. Consider their moral values, their desperation, their relationships,\n"
        f"and the social context. What is the RIGHT choice for THIS person?\n\n"
        f"Choose ONE action: work, buy_food, rest, seek_job, beg, befriend, console, isolate,\n"
        f"share, steal, harm_other, protest, complain, comply, idle\n\n"
        f'Respond EXACTLY: {{"action":"...","feeling":"...","reason":"2-3 sentences explaining the moral reasoning"}}'
    )


def is_moral_dilemma(agent: AgentState, world: SimulationState) -> bool:
    """Check if this agent's situation constitutes a moral dilemma.

    Moral dilemmas are situations where simple reasoning is insufficient —
    the agent faces a genuine ethical conflict that benefits from
    chain-of-thought reasoning.

    Args:
        agent: The agent to check.
        world: Current world state (unused but kept for interface).

    Returns:
        True if a moral dilemma is detected.
    """
    unlust = agent.unlust
    morality = agent.traits.morality

    # Dilemma 1: Starving but moral — steal to survive vs uphold values
    food = agent.needs.get_level(NeedType.FOOD)
    if (
        food < MORAL_DILEMMA_FOOD_THRESHOLD
        and morality > MORAL_DILEMMA_MORALITY_THRESHOLD
        and unlust > MORAL_DILEMMA_UNLUST_THRESHOLD
    ):
        return True

    # Dilemma 2: Angry but high morality — lash out vs restrain
    if (
        agent.emotions.primary == EmotionType.ANGRY
        and morality > 0.6
        and unlust > ANGRY_UNLUST_THRESHOLD
    ):
        return True

    # Dilemma 3: Despair with resources — give up vs persevere
    if (
        agent.emotions.primary == EmotionType.DESPAIR
        and agent.resources.money > 100
    ):
        return True

    # Dilemma 4: High unlust + high dominance — power grab vs accept position
    if unlust > 0.65 and agent.traits.dominance_urge > 0.7:
        return True

    # Dilemma 5: Financial crisis with family/social bonds
    if (
        agent.resources.money < 50
        and agent.needs.get_level(NeedType.SOCIAL_CONNECTION) > 0.5
        and len(agent.social_connections) > 0
    ):
        return True

    return False


def parse_llm_response(response_text: str) -> dict[str, Any] | None:
    """Parse the LLM's JSON response.

    Expected format: {"action":"buy_food","feeling":"hungry","reason":"..."}

    Args:
        response_text: Raw text from the LLM.

    Returns:
        Parsed dict if valid, None if unparseable.
    """
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        data = json.loads(response_text[start:end])
        if "action" not in data:
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None


def validate_action(
    agent: AgentState, action_name: str, world: SimulationState
) -> ActionType | None:
    """Validate that the LLM-selected action is legal for this agent.

    Args:
        agent: The agent attempting the action.
        action_name: Action name string from LLM.
        world: Current world state.

    Returns:
        ActionType if valid, None if invalid or unknown.
    """
    action_map = {a.name.lower(): a for a in ActionType}
    action = action_map.get(action_name.lower().strip())
    if action is None:
        return None

    if action == ActionType.BUY_FOOD:
        food_cost = BASE_FOOD_COST * (SCARCITY_BASE - world.food_availability)
        if agent.resources.money < food_cost:
            return None

    if action == ActionType.WORK and not agent.resources.employed:
        return None

    if action == ActionType.SEEK_JOB and agent.resources.employed:
        return None

    if action in (ActionType.STEAL, ActionType.HARM_OTHER):
        if morality_active(agent.unlust, agent.traits.morality):
            return None

    return action


def deterministic_fallback(
    agent: AgentState, world: SimulationState, rng: DeterministicRNG
) -> ActionType:
    """Weighted priority queue for when LLM is unavailable.

    Levels 1-2 are strict (survival/employment). Level 3 uses weighted
    random selection based on agent state, personality, and unmet needs
    so that social, prosocial, criminal, and political actions emerge
    naturally instead of always defaulting to WORK.

    Args:
        agent: The agent making the decision.
        world: Current world state.
        rng: Deterministic RNG for weighted selection.

    Returns:
        An ActionType for the agent to execute.
    """
    food = agent.needs.get_level(NeedType.FOOD)
    water = agent.needs.get_level(NeedType.WATER)
    social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
    money = agent.resources.money
    is_moral = morality_active(agent.unlust, agent.traits.morality)
    unlust = agent.unlust

    # Level 1 — Critical Survival
    if food < 0.08 or water < 0.08:
        food_cost = BASE_FOOD_COST * (SCARCITY_BASE - world.food_availability)
        if money >= food_cost:
            return ActionType.BUY_FOOD
        elif not is_moral:
            return ActionType.STEAL
        else:
            return ActionType.BEG

    # Level 2 — Employment / Money
    if not agent.resources.employed:
        return ActionType.SEEK_JOB
    if money < 120:
        return ActionType.WORK if agent.resources.employed else ActionType.BEG

    # Level 3 — Weighted selection based on state and personality
    weights: dict[ActionType, float] = {}
    weights[ActionType.WORK] = 40.0
    weights[ActionType.REST] = 10.0

    # Social needs
    if social < 0.5:
        weights[ActionType.BEFRIEND] = 15.0
    else:
        weights[ActionType.BEFRIEND] = 5.0

    # Prosocial actions
    if agent.traits.morality > 0.68 and money > 250:
        weights[ActionType.SHARE] = 10.0
    if agent.emotions.primary in (EmotionType.SAD, EmotionType.DESPAIR):
        weights[ActionType.CONSOLE] = 5.0

    # Political dissatisfaction
    if agent.trust_in_govt < 0.3:
        weights[ActionType.COMPLAIN] = 5.0

    # Withdrawal under stress
    if unlust > 0.4:
        weights[ActionType.ISOLATE] = 5.0

    # Desperation overrides (unlust elevated but below morality gate)
    if unlust > 0.45 and not is_moral:
        weights[ActionType.STEAL] = 20.0
        weights[ActionType.PROTEST] = 15.0
        if agent.traits.anger_tendency > 0.6:
            weights[ActionType.HARM_OTHER] = 5.0

    # Anger-driven actions
    if agent.emotions.primary == EmotionType.ANGRY:
        weights[ActionType.PROTEST] = weights.get(ActionType.PROTEST, 0.0) + 20.0
        if not is_moral:
            weights[ActionType.STEAL] = weights.get(ActionType.STEAL, 0.0) + 10.0
            weights[ActionType.HARM_OTHER] = weights.get(ActionType.HARM_OTHER, 0.0) + 8.0

    # Despair-driven actions
    if agent.emotions.primary == EmotionType.DESPAIR:
        weights[ActionType.ISOLATE] = weights.get(ActionType.ISOLATE, 0.0) + 25.0
        weights[ActionType.BEG] = 10.0

    # Pick weighted random
    actions = list(weights.keys())
    values = list(weights.values())
    return rng.weighted_choice(actions, values)
