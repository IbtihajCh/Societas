"""Mock AI router — trait-aware decisions for testing without GPU.

Returns JSON responses in the same format as real Gemma models:
{"action":"...","feeling":"...","reason":"..."}

Uses agent personality, needs, and emotional state to select actions,
injecting variety that mimics LLM behavior while remaining deterministic.
"""

import json
from typing import Any

from shared.types.enums import ActionType, EmotionType, JobType, NeedType, WealthClass
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.constants.defaults import BASE_FOOD_COST, SCARCITY_BASE
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.unlust_engine import morality_active

__all__ = ["MockAIRouter"]


class MockAIRouter:
    """Mock AI router that returns trait-aware deterministic responses.

    Implements the same interface as the future VLLMRouter but returns
    personality-driven decisions based on agent traits, needs, and
    emotional state instead of pure fallback logic.
    """

    def __init__(self, rng: DeterministicRNG | None = None) -> None:
        """Initialize the mock router.

        Args:
            rng: Optional RNG for deterministic action selection.
        """
        self._rng = rng or DeterministicRNG(seed=42)
        self._call_count = 0

    def is_available(self) -> bool:
        """Check if the router is available.

        Returns:
            Always True for mock router.
        """
        return True

    def agent_decide(
        self, prompt: str, agent: AgentState, world: SimulationState
    ) -> str:
        """Mock agent decision — trait-aware action selection.

        Args:
            prompt: The agent prompt (ignored, uses agent state directly).
            agent: The agent state.
            world: Current world state.

        Returns:
            JSON string: {"action":"...","feeling":"...","reason":"..."}
        """
        self._call_count += 1
        result = self._trait_aware_decision(agent, world)
        return json.dumps(result)

    def agent_decide_batch(
        self, prompts: list[str], agents: list[AgentState], world: SimulationState
    ) -> list[str]:
        """Mock batch agent decision.

        Args:
            prompts: List of prompts (ignored).
            agents: List of agent states.
            world: Current world state.

        Returns:
            List of JSON strings.
        """
        return [self.agent_decide(p, a, world) for p, a in zip(prompts, agents)]

    def moral_reasoning(
        self, prompt: str, agent: AgentState, world: SimulationState
    ) -> str:
        """Mock moral reasoning — trait-aware with moral dilemma bias.

        Args:
            prompt: The moral dilemma prompt (ignored).
            agent: The agent state.
            world: Current world state.

        Returns:
            JSON string with moral reasoning.
        """
        self._call_count += 1
        result = self._trait_aware_decision(agent, world, moral_bias=True)
        result["reason"] = (
            f"Moral reasoning: {result['action']} — "
            f"morality={agent.traits.morality:.2f}, "
            f"dilemma evaluated"
        )
        return json.dumps(result)

    def moral_reasoning_batch(
        self, prompts: list[str], agents: list[AgentState], world: SimulationState
    ) -> list[str]:
        """Mock batch moral reasoning.

        Args:
            prompts: List of prompts.
            agents: List of agent states.
            world: Current world state.

        Returns:
            List of JSON strings.
        """
        return [self.moral_reasoning(p, a, world) for p, a in zip(prompts, agents)]

    def _trait_aware_decision(
        self,
        agent: AgentState,
        world: SimulationState,
        moral_bias: bool = False,
    ) -> dict[str, Any]:
        """Select action based on agent personality, needs, and emotional state.

        Considers extraversion, morality, anger tendency, ambition, and creativity
        to produce varied decisions across different agents.

        Args:
            agent: The agent making the decision.
            world: Current world state.
            moral_bias: If True, bias toward prosocial/moral actions.

        Returns:
            Dict with action, feeling, reason keys.
        """
        food = agent.needs.get_level(NeedType.FOOD)
        water = agent.needs.get_level(NeedType.WATER)
        social = agent.needs.get_level(NeedType.SOCIAL_CONNECTION)
        money = agent.resources.money
        is_moral = morality_active(agent.unlust, agent.traits.morality)

        # Level 1 — Critical survival (same as fallback)
        if food < 0.08 or water < 0.08:
            food_cost = BASE_FOOD_COST * (SCARCITY_BASE - world.food_availability)
            if money >= food_cost:
                return {"action": "buy_food", "feeling": "relief", "reason": "need food urgently"}
            elif not is_moral:
                return {"action": "steal", "feeling": "desperate", "reason": "no money, no morality"}
            else:
                return {"action": "beg", "feeling": "ashamed", "reason": "no money but moral"}

        # Level 2 — Employment (same as fallback)
        if not agent.resources.employed:
            return {"action": "seek_job", "feeling": "hopeful", "reason": "need employment"}

        # Level 3 — Personality-driven weighted selection
        weights: dict[str, float] = {}

        # Ambition drives work harder
        weights["work"] = 30.0 + agent.traits.ambition * 20.0

        # Low sleep → rest
        sleep_level = agent.needs.get_level(NeedType.SLEEP)
        if sleep_level < 0.3:
            weights["rest"] = 25.0
        else:
            weights["rest"] = 8.0

        # Extraversion drives social
        social_weight = 5.0 + agent.traits.extraversion * 20.0
        if social < 0.5:
            social_weight *= 2.0
        weights["befriend"] = social_weight

        # Morality drives prosocial
        if agent.traits.morality > 0.6 and money > 200:
            weights["share"] = agent.traits.morality * 15.0

        # Sad nearby → console (empathy)
        if agent.traits.morality > 0.5:
            weights["console"] = 5.0

        # Anger tendency → protest/complain
        if agent.traits.anger_tendency > 0.4:
            weights["protest"] = agent.traits.anger_tendency * 10.0
            weights["complain"] = agent.traits.anger_tendency * 8.0

        # Low trust in government → complain
        if agent.trust_in_govt < 0.4:
            weights["complain"] = weights.get("complain", 0.0) + 10.0

        # Criminal path (only if not moral)
        if not is_moral and agent.unlust > 0.4:
            weights["steal"] = 15.0
            if agent.traits.anger_tendency > 0.6:
                weights["harm_other"] = 5.0

        # Anger emotion amplifies
        if agent.emotions.primary == EmotionType.ANGRY:
            weights["protest"] = weights.get("protest", 0.0) + 25.0
            if not is_moral:
                weights["steal"] = weights.get("steal", 0.0) + 15.0
                weights["harm_other"] = weights.get("harm_other", 0.0) + 8.0

        # Despair
        if agent.emotions.primary == EmotionType.DESPAIR:
            weights["isolate"] = 30.0
            weights["beg"] = 10.0

        # Low money
        if money < 100:
            weights["beg"] = weights.get("beg", 0.0) + 10.0

        # -- New action weights --

        # FRAUD — immoral rich
        if not is_moral and money > 200:
            weights["fraud"] = agent.traits.ambition * 8.0

        # TREAT — doctor profession
        if agent.job_type == JobType.DOCTOR:
            weights["treat"] = 15.0 + agent.traits.morality * 10.0

        # COUNSEL — therapist profession
        if agent.job_type == JobType.THERAPIST:
            weights["counsel"] = 15.0 + agent.traits.morality * 10.0

        # CAMPAIGN — political ambition
        if agent.traits.ambition > 0.5 and agent.notoriety > 0.4 and money > 100:
            weights["campaign"] = agent.traits.ambition * 15.0

        # COMPLY — compliant personality
        if agent.trust_in_govt > 0.5 and agent.traits.anger_tendency < 0.3:
            weights["comply"] = agent.trust_in_govt * 8.0

        # SPREAD_RUMOR — dominance-driven gossip
        if agent.traits.dominance_urge > 0.6:
            weights["spread_rumor"] = agent.traits.dominance_urge * 10.0

        # SUPPORT_FAMILY — family financial support
        if money > 20:
            family_bond = agent.needs.get_level(NeedType.FAMILY_BOND)
            if family_bond < 0.5:
                weights["support_family"] = (0.5 - family_bond) * 10.0

        # INVEST — financial investment
        if money > 200 and agent.traits.ambition > 0.4:
            weights["invest"] = agent.traits.ambition * 8.0

        # BUY_PROPERTY — real estate
        if money > 500 and agent.wealth_class != WealthClass.POOR:
            weights["buy_property"] = 5.0

        # HOBBY — stress relief
        if agent.emotions.happiness_score < 0.4 or agent.unlust > 0.5:
            weights["hobby"] = 8.0

        # IDLE — conscious choice, very low weight
        weights["idle"] = 1.0

        # Moral bias for dilemma context
        if moral_bias:
            if is_moral:
                weights["share"] = weights.get("share", 0.0) + 20.0
                weights["console"] = weights.get("console", 0.0) + 10.0
            else:
                weights["steal"] = weights.get("steal", 0.0) + 5.0

        # Ensure at least some weight exists (fallback to work)
        if not weights:
            weights["work"] = 50.0

        # Pick weighted random
        actions = list(weights.keys())
        values = list(weights.values())
        chosen = self._rng.weighted_choice(actions, values)

        feelings = {
            "work": "productive", "rest": "tired", "befriend": "social",
            "share": "generous", "console": "empathetic", "protest": "angry",
            "complain": "frustrated", "steal": "desperate", "harm_other": "enraged",
            "isolate": "withdrawn", "beg": "ashamed", "buy_food": "satisfied",
            "seek_job": "hopeful",
        }

        return {
            "action": chosen,
            "feeling": feelings.get(chosen, "neutral"),
            "reason": (
                f"trait-driven choice (morality={agent.traits.morality:.2f}, "
                f"extraversion={agent.traits.extraversion:.2f}, "
                f"anger={agent.traits.anger_tendency:.2f})"
            ),
        }

    def governance_advisory(
        self, world: SimulationState, agents: list[AgentState]
    ) -> dict[str, Any]:
        """Mock governance advisory — returns threshold-based alerts.

        Args:
            world: Current world state.
            agents: All agents.

        Returns:
            Dict with assessment, recommendation, watch_items.
        """
        living = [a for a in agents if a.is_alive]
        if not living:
            return {"assessment": "No living agents", "recommendation": "N/A", "watch_items": []}

        avg_unlust = sum(a.unlust for a in living) / len(living)
        crime_rate = world.crime_rate
        unemployment = world.unemployment_rate

        watch_items: list[str] = []
        if avg_unlust > 0.6:
            watch_items.append("High average unlust — population distressed")
        if crime_rate > 0.15:
            watch_items.append("Crime rate above threshold")
        if unemployment > 0.15:
            watch_items.append("Unemployment above natural rate")

        if avg_unlust > 0.7:
            recommendation = "Consider welfare programs or tax reduction"
        elif crime_rate > 0.15:
            recommendation = "Consider public order policies"
        elif unemployment > 0.15:
            recommendation = "Consider economic stimulus"
        else:
            recommendation = "Society is stable"

        return {
            "assessment": (
                f"Unlust: {avg_unlust:.2f}, "
                f"Crime: {crime_rate:.2f}, "
                f"Unemployment: {unemployment:.2f}"
            ),
            "recommendation": recommendation,
            "watch_items": watch_items,
        }

    @property
    def call_count(self) -> int:
        """Number of LLM calls made."""
        return self._call_count
