"""Mock AI router — deterministic LLM responses for testing without GPU.

Returns JSON responses in the same format as real Gemma models:
{"action":"...","feeling":"...","reason":"..."}

Uses deterministic_fallback to select actions, ensuring full reproducibility.
"""

import json
from typing import Any

from shared.types.enums import ActionType
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.decision_engine import (
    deterministic_fallback,
    is_moral_dilemma,
    parse_llm_response,
)
from simulation.agents.action_executor import compute_nearby_counts

__all__ = ["MockAIRouter"]


class MockAIRouter:
    """Mock AI router that returns deterministic responses.

    Implements the same interface as the future VLLMRouter but returns
    deterministic fallback actions wrapped in LLM-style JSON.
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
        """Mock agent decision — returns deterministic fallback as JSON.

        Args:
            prompt: The agent prompt (ignored, uses deterministic fallback).
            agent: The agent state.
            world: Current world state.

        Returns:
            JSON string: {"action":"...","feeling":"...","reason":"..."}
        """
        self._call_count += 1
        action = deterministic_fallback(agent, world, self._rng)
        feeling = agent.emotions.primary.value
        reason = f"Deterministic fallback: {action.value}"
        return json.dumps({"action": action.value, "feeling": feeling, "reason": reason})

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
        """Mock moral reasoning — returns deterministic fallback as JSON.

        Args:
            prompt: The moral dilemma prompt (ignored).
            agent: The agent state.
            world: Current world state.

        Returns:
            JSON string with moral reasoning.
        """
        self._call_count += 1
        action = deterministic_fallback(agent, world, self._rng)
        feeling = agent.emotions.primary.value
        reason = (
            f"Moral reasoning fallback: {action.value} — "
            f"agent faces dilemma but deterministic logic applies"
        )
        return json.dumps({"action": action.value, "feeling": feeling, "reason": reason})

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
