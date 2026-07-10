"""AI Historian service — generates narrative chronicles and governance advice from simulation state."""

import json
import logging
from typing import Any

from models.router.vllm_router import VLLMRouter
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState

logger = logging.getLogger("societas.ai.historian")

_historian_instance: "AIHistorianService | None" = None

FALLBACK_NARRATIVE = "The society continued its development without notable incident."
FALLBACK_ETHICS = "Further ethical analysis is unavailable."


class AIHistorianService:
    def __init__(self, router: VLLMRouter) -> None:
        global _historian_instance
        _historian_instance = self
        self._router = router
        self._entries: list[dict[str, Any]] = []

    def generate_entry(self, world: SimulationState, tick: int) -> dict[str, Any]:
        prompt = self._build_narrative_prompt(world, tick)
        raw = self._router.generate_narrative(prompt)
        entry = {
            "tick": tick,
            "narrative": raw or FALLBACK_NARRATIVE,
        }
        self._entries.append(entry)
        return entry

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def get_governance_advice(
        self, world: SimulationState, agents: list[AgentState]
    ) -> dict[str, Any]:
        governance_prompt = self._build_governance_prompt(world, agents)
        raw_gov = self._router.generate_narrative(governance_prompt)
        governance = self._parse_governance(raw_gov)

        ethics_prompt = self._build_ethics_prompt(world)
        ethics = self._router.moral_assessment(ethics_prompt) or FALLBACK_ETHICS

        return {
            "governance": governance,
            "ethics": ethics,
        }

    def _build_narrative_prompt(self, world: SimulationState, tick: int) -> str:
        return (
            f"<|think|>\n"
            f"You are the AI Historian of a simulated society. Write a 2-3 sentence narrative entry "
            f"about what happened at tick {tick}.\n\n"
            f"Society state at tick {tick}:\n"
            f"Population: {world.population}\n"
            f"Economic Health: {world.economic_health:.2f}\n"
            f"Social Cohesion: {world.social_cohesion:.2f}\n"
            f"Crime Rate: {world.crime_rate:.2f}\n"
            f"Unemployment: {world.unemployment_rate:.2f}\n"
            f"Protest Intensity: {world.protest_intensity:.2f}\n"
            f"Unlust (unhappiness): {world.unlust:.2f}\n"
            f"Food Availability: {world.food_availability:.2f}\n\n"
            f"Output a short narrative paragraph describing this moment in the society's history."
        )

    def _build_governance_prompt(self, world: SimulationState, agents: list[AgentState]) -> str:
        living = [a for a in agents if a.is_alive]
        avg_unlust = sum(a.unlust for a in living) / len(living) if living else 0.0
        return (
            f"<|think|>\n"
            f"Assess this society simulation state and recommend a policy:\n"
            f"Population: {len(living)}\n"
            f"Avg Unlust: {avg_unlust:.2f}\n"
            f"Crime: {world.crime_rate:.2f}\n"
            f"Unemployment: {world.unemployment_rate:.2f}\n"
            f"Tax: {world.tax_rate:.2f}\n"
            f"Welfare: {'on' if world.welfare_enabled else 'off'}\n"
            f"Food: {world.food_availability:.2f}\n\n"
            f'Output JSON: {{"assessment":"...","recommendation":"...","watch_items":["..."]}}'
        )

    def _build_ethics_prompt(self, world: SimulationState) -> str:
        return (
            f"<|think|>\n"
            f"Consider the ethical implications of this society's current state:\n"
            f"Tax rate: {world.tax_rate:.0%}\n"
            f"Welfare: {'enabled' if world.welfare_enabled else 'disabled'}\n"
            f"Crime rate: {world.crime_rate:.2f}\n"
            f"Unemployment: {world.unemployment_rate:.2f}\n"
            f"Protest intensity: {world.protest_intensity:.2f}\n"
            f"Food availability: {world.food_availability:.2f}\n\n"
            f"Provide a brief ethical assessment of the current policies and conditions. "
            f"Is the society just? Are there moral concerns?"
        )

    def _parse_governance(self, raw: str) -> dict[str, Any]:
        if not raw:
            return {"assessment": "Unavailable", "recommendation": "No data", "watch_items": []}
        try:
            data = json.loads(raw)
            if "assessment" in data and "recommendation" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return {"assessment": "Unavailable", "recommendation": "Unable to parse", "watch_items": []}
