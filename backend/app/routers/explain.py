import logging
import os

from fastapi import APIRouter, Depends

from backend.app.dependencies import get_simulation_service
from backend.app.services.simulation_service import SimulationService

logger = logging.getLogger("societas.api")

router = APIRouter(tags=["explain"])


@router.post("/explain")
async def explain_simulation_state(
    body: dict,
    service: SimulationService = Depends(get_simulation_service),
):
    question = body.get("question", "")
    state = service.get_state()
    if state is None:
        return {"answer": "Simulation not started.", "evidence": {}, "source": "system"}

    answer_parts = []
    evidence = {}

    q = question.lower()

    if "crime" in q:
        cr = getattr(state, "crime_rate", 0)
        answer_parts.append(f"The crime rate is {cr:.3f}.")
        evidence["crime_rate"] = cr
        if cr < 0.04:
            answer_parts.append("This is well below the normal baseline (0.04–0.12).")
        elif cr < 0.12:
            answer_parts.append("This is within the normal baseline range.")
        elif cr < 0.25:
            answer_parts.append("This is elevated above normal (threshold 0.15).")
        else:
            answer_parts.append("This is at crisis level (threshold >0.25).")

    if "econom" in q or "money" in q or "wealth" in q:
        aw = getattr(state, "economic_health", 0.5)
        unemp = getattr(state, "unemployment_rate", 0)
        answer_parts.append(f"Economic health: {aw:.2f}, unemployment: {unemp:.2%}.")
        evidence["economic_health"] = aw
        evidence["unemployment_rate"] = unemp

    if "death" in q or "die" in q or "mortal" in q:
        pop = getattr(state, "population", 0)
        answer_parts.append(f"Current population: {pop}.")
        evidence["population"] = pop

    if "unlust" in q or "unhap" in q or "miser" in q:
        au = getattr(state, "unlust", 0)
        answer_parts.append(f"The unlust (misery) index is {au:.3f}.")
        evidence["unlust"] = au
        if au < 0.15:
            answer_parts.append("This is within the normal range (<0.15).")
        elif au < 0.35:
            answer_parts.append("This is elevated (0.15–0.35).")
        else:
            answer_parts.append("This is critical (>0.35).")

    if "food" in q:
        fa = getattr(state, "food_availability", 0.85)
        answer_parts.append(f"Food availability: {fa:.2f}.")
        evidence["food_availability"] = fa
        if fa > 0.8:
            answer_parts.append("This is within the normal range (0.80–1.0).")
        elif fa > 0.5:
            answer_parts.append("This is below normal but not yet critical.")
        else:
            answer_parts.append("This is at crisis level (<0.5).")

    if "protest" in q or "riot" in q:
        pi = getattr(state, "protest_intensity", 0)
        answer_parts.append(f"Protest intensity: {pi:.3f}.")
        evidence["protest_intensity"] = pi

    if "tax" in q:
        tr = getattr(state, "tax_rate", 0.15)
        wel = getattr(state, "welfare_enabled", False)
        answer_parts.append(f"Tax rate: {tr:.0%}. Welfare is {'enabled' if wel else 'disabled'}.")
        evidence["tax_rate"] = tr
        evidence["welfare_enabled"] = wel

    if not answer_parts:
        ec = getattr(state, "economic_health", 0)
        sc = getattr(state, "social_cohesion", 0)
        pop = getattr(state, "population", 0)
        tick = getattr(state, "tick", 0)
        answer_parts.append(
            f"The simulation is at tick {tick} with {pop} agents. "
            f"Economic health: {ec:.2f}, Social cohesion: {sc:.2f}."
        )
        evidence["economic_health"] = ec
        evidence["social_cohesion"] = sc
        evidence["population"] = pop
        evidence["tick"] = tick

    return {
        "answer": " ".join(answer_parts),
        "evidence": evidence,
        "source": "rule",
    }
