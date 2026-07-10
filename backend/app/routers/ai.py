import logging
from typing import Any

from fastapi import APIRouter

from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter

logger = logging.getLogger("societas.api.ai")

router = APIRouter()
_ai_router: VLLMRouter | None = None


def get_ai_router() -> VLLMRouter:
    global _ai_router
    if _ai_router is None:
        config = VLLMConfig(
            api_key_e2b="",
            api_key_moe_26b="",
            api_key_dense_31b="",
        )
        _ai_router = VLLMRouter(config)
    return _ai_router


@router.get("/status")
async def ai_status() -> dict:
    router_inst = get_ai_router()
    available = router_inst.is_available()
    return {
        "available": available,
        "base_url": "http://165.245.130.202:8000/v1",
    }
