import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from models.router.ai_router import AIRouter
from models.router.config import AIConfig
from shared.schemas.decision import DecisionRequest, DecisionResponse, DecisionOption
from shared.schemas.policy import PolicyWeights
from shared.schemas.news_event import NewsEvent, SpotlightNarration

logger = logging.getLogger("societas.api.ai")

router = APIRouter()
_ai_router: AIRouter | None = None


def get_ai_router() -> AIRouter:
    global _ai_router
    if _ai_router is None:
        _ai_router = AIRouter(AIConfig())
    return _ai_router


@router.post("/translate-policy", response_model=dict)
async def translate_policy(body: dict[str, Any]) -> dict:
    router_inst = get_ai_router()
    weights = router_inst.translate_policy(
        persona=body.get("persona", ""),
        goal=body.get("goal", ""),
        context=body.get("context", {}),
    )
    return {
        "economic_freedom": weights.economic_freedom,
        "social_welfare": weights.social_welfare,
        "environmental_protection": weights.environmental_protection,
        "public_order": weights.public_order,
        "innovation": weights.innovation,
        "cultural_preservation": weights.cultural_preservation,
    }


@router.post("/tie-break", response_model=dict)
async def tie_break(body: dict[str, Any]) -> dict:
    router_inst = get_ai_router()
    request = DecisionRequest(
        agent_id=body.get("agent_id", ""),
        state=body.get("state", ""),
        unlust=body.get("unlust", 0.0),
        morality=body.get("morality", 0.5),
        options=[
            DecisionOption(**opt) if isinstance(opt, dict) else opt
            for opt in body.get("options", [])
        ],
        context=body.get("context", {}),
    )
    response = router_inst.tie_break(request)
    return {
        "action": response.action.value if hasattr(response.action, "value") else str(response.action),
        "confidence": response.confidence,
        "reason": response.reason,
    }


@router.post("/generate-news", response_model=dict)
async def generate_news(body: dict[str, Any]) -> dict:
    router_inst = get_ai_router()
    news = router_inst.generate_news(
        events=body.get("events", []),
        state_deltas=body.get("state_deltas", {}),
    )
    return {
        "id": news.id,
        "tick": news.tick,
        "headline": news.headline,
        "dateline": news.dateline,
        "body": news.body,
        "bylines": news.bylines,
        "category": news.category,
        "importance": news.importance,
    }


@router.post("/generate-persona", response_model=dict)
async def generate_persona(body: dict[str, Any]) -> dict:
    router_inst = get_ai_router()
    persona = router_inst.generate_persona(
        traits=body.get("traits", {})
    )
    return {"persona": persona}


@router.post("/generate-narration", response_model=dict)
async def generate_narration(body: dict[str, Any]) -> dict:
    router_inst = get_ai_router()
    narration = router_inst.generate_narration(
        agent_id=body.get("agent_id", ""),
        events=body.get("events", []),
    )
    return {
        "agent_id": narration.agent_id,
        "tick": narration.tick,
        "title": narration.title,
        "content": narration.content,
        "mood": narration.mood,
    }


@router.get("/status")
async def ai_status() -> dict:
    router_inst = get_ai_router()
    available = router_inst.is_available()
    return {
        "available": available,
        "amd_endpoint": router_inst.config.amd_base_url,
        "model": router_inst.config.model_name,
    }
