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


_MONITORED_FIELDS = [
    "population", "economic_health", "social_cohesion", "public_order",
    "crime_rate", "unemployment_rate", "protest_intensity",
    "unlust", "morality", "food_availability", "water_availability",
    "tax_rate",
]

_FIELD_LABELS = {
    "population": "Population",
    "economic_health": "Economic output",
    "social_cohesion": "Social trust",
    "public_order": "Public order",
    "crime_rate": "Crime rate",
    "unemployment_rate": "Jobless rate",
    "protest_intensity": "Civil unrest",
    "unlust": "Public discontent",
    "morality": "Moral standards",
    "food_availability": "Food supply",
    "water_availability": "Water supply",
    "tax_rate": "Tax burden",
}


class AIHistorianService:
    def __init__(self, router: VLLMRouter) -> None:
        global _historian_instance
        _historian_instance = self
        self._router = router
        self._entries: list[dict[str, Any]] = []
        self._snapshots: list[dict[str, Any]] = []
        self._last_summary_tick: int = 0

    def accumulate(self, world: SimulationState, tick: int) -> None:
        snapshot = {"tick": tick}
        for field in _MONITORED_FIELDS:
            snapshot[field] = getattr(world, field, None)
        self._snapshots.append(snapshot)

    def generate_summary(self, tick: int) -> dict[str, Any] | None:
        if not self._snapshots:
            return None
        prompt = self._build_batch_prompt(tick)
        raw = self._router.generate_narrative_moe(prompt)
        entry = {
            "tick": tick,
            "narrative": raw or FALLBACK_NARRATIVE,
            "period_start": self._last_summary_tick,
        }
        self._entries.append(entry)
        self._last_summary_tick = tick
        return entry

    def has_snapshots(self) -> bool:
        return len(self._snapshots) > 0

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

    def _build_batch_prompt(self, tick: int) -> str:
        start = self._last_summary_tick
        first = self._snapshots[0]
        last = self._snapshots[-1]

        changes = []
        for field in _MONITORED_FIELDS:
            old = first.get(field)
            new = last.get(field)
            label = _FIELD_LABELS.get(field, field)
            if old is not None and new is not None:
                if isinstance(old, (int, float)) and isinstance(new, (int, float)):
                    if abs(new - old) > 0.001:
                        direction = "rose" if new > old else "fell"
                        changes.append(f"{label} {direction} from {old:.0%} to {new:.0%}" if isinstance(old, float) and old <= 1.0 else f"{label} {direction} from {old:.2f} to {new:.2f}")
                    else:
                        changes.append(f"{label} held steady at {old:.0%}" if isinstance(old, float) and old <= 1.0 else f"{label} held steady at {old:.2f}")

        lines: list[str] = []
        lines.append(f"Write a historian's chronicle entry for the period from tick {start} to tick {tick}.")
        lines.append("Write 2-3 paragraphs describing what happened, why it matters, and what it means for the society's trajectory.")
        lines.append("Use the tone of a real historian recording events of a civilization. Be vivid but grounded.")
        lines.append("")
        lines.append("Metrics over this period:")
        for c in changes:
            lines.append(f"  {c}")
        lines.append("")
        lines.append("Chronicle:")
        return "\n".join(lines)

    def _build_governance_prompt(self, world: SimulationState, agents: list[AgentState]) -> str:
        living = [a for a in agents if a.is_alive]
        avg_unlust = sum(a.unlust for a in living) / len(living) if living else 0.0
        n_dead = sum(1 for a in agents if not a.is_alive)
        econ = world.economy
        return (
            f"You are a strategic advisor. Assess this society and recommend policy.\n\n"
            f"State:\n"
            f"- {len(living)} alive, {n_dead} dead\n"
            f"- Discontent {avg_unlust:.0%}, crime {world.crime_rate:.0%}\n"
            f"- Unemployment {world.unemployment_rate:.0%}, inflation {econ.inflation_rate:.0%}\n"
            f"- Tax {world.tax_rate:.0%}, welfare {'on' if world.welfare_enabled else 'off'}\n"
            f"- Food {world.food_availability:.0%}, national debt {world.national_debt:.2f}\n"
            f"- Remittance income {world.remittance_income:.0%}, energy price {world.energy_price:.2f}\n\n"
            f"Output JSON: assessment (2-3 sentence situation analysis), "
            f"recommendation (specific policy with reasoning), "
            f"watch_items (list of 3 things to monitor)."
        )

    def _build_ethics_prompt(self, world: SimulationState) -> str:
        return (
            f"One paragraph ethical assessment of this society.\n\n"
            f"Tax {world.tax_rate:.0%}, welfare {'on' if world.welfare_enabled else 'off'}\n"
            f"Crime {world.crime_rate:.0%}, jobless {world.unemployment_rate:.0%}\n"
            f"Unrest {world.protest_intensity:.0%}, food {world.food_availability:.0%}\n\n"
            f"Ethical assessment:"
        )

    def _parse_governance(self, raw: str) -> dict[str, Any]:
        if not raw:
            return {"assessment": "Unavailable", "recommendation": "No data", "watch_items": []}
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            candidate = raw[start:end]
            try:
                data = json.loads(candidate)
                if "assessment" in data and "recommendation" in data:
                    return data
            except (json.JSONDecodeError, TypeError):
                pass
        return {"assessment": "Unavailable", "recommendation": "Unable to parse", "watch_items": []}
