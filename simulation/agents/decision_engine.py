"""Decision engine — E2B hybrid decision architecture.

Builds prompts for the LLM agent brain, detects moral dilemmas for 26B escalation,
parses LLM responses, validates actions, and provides deterministic fallback.
"""

import json
import math
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
from simulation.agents.memory_system import compute_memory_prompt
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

    prompt = (
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

    # Inject episodic memories into the prompt for context-aware decisions
    agent_memories = compute_memory_prompt(agent)
    if agent_memories:
        prompt += f"\n\n{agent_memories}"

    return prompt


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


def softmax_choice(
    action_scores: dict[str, float],
    rng: DeterministicRNG,
    temperature: float = 0.5,
) -> str:
    """
    Select an action using softmax probability distribution.

    P(action_i) = exp(score_i / temperature) / sum(exp(score_j / temperature))

    Higher temperature = more random exploration
    Lower temperature = more deterministic (greedy)
    """
    actions = list(action_scores.keys())
    scores = list(action_scores.values())

    # Apply temperature scaling
    scaled = [s / temperature for s in scores]

    # Numerical stability: subtract max
    max_s = max(scaled)
    exp_s = [math.exp(s - max_s) for s in scaled]
    total = sum(exp_s)
    probs = [e / total for e in exp_s]

    # Cumulative distribution for weighted selection
    r = rng.random()
    cumulative = 0.0
    for i, prob in enumerate(probs):
        cumulative += prob
        if r < cumulative:
            return actions[i]
    return actions[-1]


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

    # Level 3 — Softmax over weighted action utilities
    base_scores = {
        "WORK": 5.0,
        "REST": 3.0,
        "BEFRIEND": 3.0,
        "CONSOLE": 2.0,
        "SHARE": 2.0,
        "COMPLAIN": 1.0,
        "ISOLATE": 1.0,
        "STEAL": 1.0,
        "BEG": 1.0,
        "HARM_OTHER": 0.5,
        "PROTEST": 1.0,
    }

    # Modulate scores by agent state
    # Extraversion → higher BEFRIEND/CONSOLE
    if agent.traits.extraversion > 0.6:
        base_scores["BEFRIEND"] += (agent.traits.extraversion - 0.6) * 10
        base_scores["CONSOLE"] += (agent.traits.extraversion - 0.6) * 5
    elif agent.traits.extraversion < 0.3:
        base_scores["ISOLATE"] += (0.3 - agent.traits.extraversion) * 10

    # Anger tendency → higher STEAL/PROTEST/HARM_OTHER
    if agent.traits.anger_tendency > 0.5:
        anger_bonus = (agent.traits.anger_tendency - 0.5) * 10
        base_scores["STEAL"] += anger_bonus * 0.5
        base_scores["PROTEST"] += anger_bonus * 0.4
        base_scores["HARM_OTHER"] += anger_bonus * 0.3

    # Morality → lower criminal actions
    if agent.traits.morality > 0.6:
        morality_penalty = (agent.traits.morality - 0.6) * 10
        base_scores["STEAL"] = max(0.1, base_scores["STEAL"] - morality_penalty * 0.5)
        base_scores["HARM_OTHER"] = max(0.1, base_scores["HARM_OTHER"] - morality_penalty * 0.4)
        base_scores["PROTEST"] = max(0.1, base_scores["PROTEST"] - morality_penalty * 0.3)

    # Unlust → higher PROTEST/ISOLATE/BEG
    if unlust > 0.4:
        unlust_bonus = (unlust - 0.4) * 15
        base_scores["ISOLATE"] += unlust_bonus * 0.3
        base_scores["BEG"] += unlust_bonus * 0.2
    if unlust > 0.5:
        base_scores["PROTEST"] += (unlust - 0.5) * 20

    # Employment status
    if not agent.resources.employed:
        base_scores["WORK"] = max(0.1, base_scores["WORK"] - 2.0)
        base_scores["BEG"] += 2.0

    # Emotional state
    if agent.emotions.primary == EmotionType.DESPAIR:
        base_scores["ISOLATE"] += 5.0
        base_scores["BEG"] += 3.0
    elif agent.emotions.primary == EmotionType.ANGRY:
        base_scores["PROTEST"] += 4.0
        base_scores["STEAL"] += 2.0
        base_scores["HARM_OTHER"] += 1.0
    elif agent.emotions.primary == EmotionType.SADNESS:
        base_scores["CONSOLE"] += 3.0
        base_scores["REST"] += 2.0

    # Filter out invalid actions
    valid_actions = {}
    for action_name, score in base_scores.items():
        if score <= 0:
            continue
        # Validate action
        if action_name == "WORK" and not agent.resources.employed:
            continue
        if action_name == "STEAL" and agent.traits.morality > 0.4:
            continue
        if action_name == "HARM_OTHER" and agent.traits.morality > 0.3:
            continue
        if action_name == "BEG" and agent.resources.money > 50:
            continue
        if action_name == "SHARE" and agent.resources.money < 100:
            continue
        valid_actions[action_name] = score

    # If no valid actions, default to IDLE
    if not valid_actions:
        return ActionType.IDLE

    # Temperature varies by emotional stability
    temperature = 0.5
    if abs(unlust - 0.5) > 0.3:
        temperature = 0.8  # More random when unstable

    action_name = softmax_choice(valid_actions, rng, temperature)
    action_map = {
        "WORK": ActionType.WORK,
        "REST": ActionType.REST,
        "BEFRIEND": ActionType.BEFRIEND,
        "CONSOLE": ActionType.CONSOLE,
        "SHARE": ActionType.SHARE,
        "COMPLAIN": ActionType.COMPLAIN,
        "ISOLATE": ActionType.ISOLATE,
        "STEAL": ActionType.STEAL,
        "BEG": ActionType.BEG,
        "HARM_OTHER": ActionType.HARM_OTHER,
        "PROTEST": ActionType.PROTEST,
    }
    return action_map.get(action_name, ActionType.IDLE)
