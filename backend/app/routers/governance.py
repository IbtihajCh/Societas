from fastapi import APIRouter, Depends, HTTPException

from backend.app.dependencies import get_governance_service, get_policy_service, get_simulation_service
from backend.app.services.governance_service import GovernanceService
from backend.app.services.policy_service import PolicyService
from backend.app.services.simulation_service import SimulationService
from shared.dto.policy_dto import PolicyCreateRequestDTO
from pydantic import BaseModel


router = APIRouter()


class ApplySuggestionRequest(BaseModel):
    action: str = ""
    description: str = ""


@router.get("/suggestions")
async def get_suggestions(
    governance: GovernanceService = Depends(get_governance_service),
):
    return {"suggestions": governance.get_suggestions()}


class GovernanceChangeRequest(BaseModel):
    tax_rate: float | None = None
    welfare_enabled: bool | None = None
    welfare_amount: float | None = None
    food_availability: float | None = None

@router.post("/apply", status_code=200)
async def apply_governance(request: GovernanceChangeRequest, service: SimulationService = Depends(get_simulation_service)):
    engine = service.get_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="Simulation not started")
    import dataclasses
    state = engine.get_state()
    if request.tax_rate is not None:
        state.tax_rate = request.tax_rate
    if request.welfare_enabled is not None:
        state.welfare_enabled = request.welfare_enabled
    if request.welfare_amount is not None:
        state.welfare_amount = request.welfare_amount
    if request.food_availability is not None:
        state.food_availability = request.food_availability
    state_dto = await service.get_state()
    return {"status": "applied", "changes": request.model_dump(exclude_none=True), "state": state_dto}

@router.post("/apply-suggestion", status_code=201)
async def apply_suggestion(
    request: ApplySuggestionRequest,
    policy_service: PolicyService = Depends(get_policy_service),
):
    policy_request = PolicyCreateRequestDTO(
        name=request.action,
        description=request.description,
    )
    return await policy_service.create_policy(policy_request)
