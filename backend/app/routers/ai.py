import logging
import os
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
        _ai_router = VLLMRouter(VLLMConfig(
            base_url=os.getenv("VLLM_BASE_URL", ""),
            base_url_e2b=os.getenv("VLLM_BASE_URL_E2B", ""),
            base_url_moe_26b=os.getenv("VLLM_BASE_URL_MOE_26B", ""),
            base_url_dense_31b=os.getenv("VLLM_BASE_URL_DENSE_31B", ""),
            api_key_e2b=os.getenv("API_KEY_E2B", ""),
            api_key_moe_26b=os.getenv("API_KEY_MOE_26B", ""),
            api_key_dense_31b=os.getenv("API_KEY_DENSE_31B", ""),
        ))
    return _ai_router


@router.get("/status")
async def ai_status() -> dict:
    router_inst = get_ai_router()
    available = router_inst.is_available()
    return {
        "available": available,
        "base_url_dense_31b": os.getenv("VLLM_BASE_URL_DENSE_31B") or os.getenv("VLLM_BASE_URL", "http://165.245.130.202:8000/v1"),
    }
