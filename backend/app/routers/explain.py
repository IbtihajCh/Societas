"""Explain endpoint: answers 'why did this happen?' using 31B LLM or rule-based fallback."""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.dependencies import get_simulation_service
from backend.app.services.simulation_service import SimulationService
from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter

router = APIRouter()
logger = logging.getLogger("societas.explain")


class ExplainRequest(BaseModel):
    question: str = ""


class ExplainResponse(BaseModel):
    answer: str
    evidence: dict
    source: str = "llm"


def _build_rule_explanation(state, question: str) -> str:
    q = question.lower()
    parts = []
    if any(w in q for w in ["tax", "welfare", "policy", "economy"]):
        parts.append(
            f"Current tax rate is {state.tax_rate:.0%}, "
            f"welfare is {'enabled' if state.welfare_enabled else 'disabled'} "
            f"(amount: ${state.welfare_amount:.0f}). "
            f"Economic health: {state.economic_health:.2f}, "
            f"unemployment: {state.unemployment_rate:.0%}."
        )
    if any(w in q for w in ["crime", "steal", "harm", "protest", "riot"]):
        parts.append(
            f"Crime rate: {state.crime_rate:.2f}, "
            f"protest intensity: {state.protest_intensity:.2f}, "
            f"public order: {state.public_order:.2f}, "
            f"average unlust: {state.unlust:.2f}."
        )
    if any(w in q for w in ["food", "hunger", "famine", "drought"]):
        parts.append(
            f"Food availability: {state.food_availability:.0%}, "
            f"water availability: {state.water_availability:.0%}."
        )
    if any(w in q for w in ["die", "death", "mortality", "population"]):
        parts.append(
            f"Population: {state.population}, "
            f"average unlust: {state.unlust:.2f}, "
            f"morality: {state.morality:.2f}."
        )
    if any(w in q for w in ["unlust", "happiness", "emotion", "angry", "sad"]):
        parts.append(
            f"Average unlust: {state.unlust:.2f}, "
            f"morality: {state.morality:.2f}, "
            f"social cohesion: {state.social_cohesion:.2f}."
        )
    if any(w in q for w in ["env", "environment", "weather", "event"]):
        active = state.active_env_events or []
        if active:
            parts.append(f"Active environmental events: {', '.join(active)}.")
        else:
            parts.append("No active environmental events.")
    if not parts:
        parts.append(
            f"World state — population: {state.population}, "
            f"tick: {state.time_step}, "
            f"economic health: {state.economic_health:.2f}, "
            f"crime rate: {state.crime_rate:.2f}, "
            f"food availability: {state.food_availability:.0%}."
        )
    return " ".join(parts)


@router.post("/explain", response_model=ExplainResponse)
async def explain(
    request: ExplainRequest,
    service: SimulationService = Depends(get_simulation_service),
):
    engine = service.get_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="Simulation not started")
    state = engine.get_state()

    evidence = {
        "tick": state.time_step,
        "population": state.population,
        "economic_health": round(state.economic_health, 3),
        "crime_rate": round(state.crime_rate, 3),
        "protest_intensity": round(state.protest_intensity, 3),
        "unemployment_rate": round(state.unemployment_rate, 3),
        "food_availability": round(state.food_availability, 3),
        "tax_rate": state.tax_rate,
        "welfare_enabled": state.welfare_enabled,
        "unlust": round(state.unlust, 3),
        "morality": round(state.morality, 3),
        "active_env_events": state.active_env_events or [],
    }

    config = VLLMConfig(
        base_url=os.getenv("VLLM_BASE_URL", ""),
        base_url_e2b=os.getenv("VLLM_BASE_URL_E2B", ""),
        base_url_moe_26b=os.getenv("VLLM_BASE_URL_MOE_26B", ""),
        base_url_dense_31b=os.getenv("VLLM_BASE_URL_DENSE_31B", ""),
        api_key_e2b=os.getenv("API_KEY_E2B", ""),
        api_key_moe_26b=os.getenv("API_KEY_MOE_26B", ""),
        api_key_dense_31b=os.getenv("API_KEY_DENSE_31B", ""),
    )
    router = VLLMRouter(config)

    if router.is_available():
        try:
            answer = router.answer_question(request.question, state)
            if answer:
                return ExplainResponse(answer=answer, evidence=evidence, source="llm")
        except Exception as e:
            logger.warning("LLM explain call failed, using rule fallback: %s", e)

    answer = _build_rule_explanation(state, request.question)
    return ExplainResponse(answer=answer, evidence=evidence, source="rule")
