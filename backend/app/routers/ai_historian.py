import logging
from typing import Any

from fastapi import APIRouter

from backend.app.services.ai_historian import AIHistorianService, _historian_instance
from backend.app.services.simulation_service import _service_instance

logger = logging.getLogger("societas.api.historian")

router = APIRouter()


def _get_historian() -> AIHistorianService | None:
    if _historian_instance is not None:
        return _historian_instance
    if _service_instance is not None:
        return _service_instance.historian
    return None


@router.get("/history")
async def get_history() -> list[dict[str, Any]]:
    historian = _get_historian()
    if historian is None:
        return []
    return historian.get_history()


@router.get("/policy-advice")
async def get_policy_advice() -> dict[str, Any]:
    historian = _get_historian()
    if historian is None:
        return {"governance": {"assessment": "No simulation running", "recommendation": "Start a simulation first", "watch_items": []}, "ethics": "Not available"}
    if _service_instance is None:
        return {"governance": {"assessment": "No simulation running", "recommendation": "Start a simulation first", "watch_items": []}, "ethics": "Not available"}
    state = _service_instance.get_engine().get_state()
    agents = _service_instance.get_engine().get_agents()
    return historian.get_governance_advice(state, agents)
