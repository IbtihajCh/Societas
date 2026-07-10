from fastapi import APIRouter, Depends, HTTPException

from shared.dto.policy_dto import (
    CrisisInjectRequestDTO,
    CrisisResultDTO,
    PolicyCreateRequestDTO,
    PolicyListResponseDTO,
    PolicyResponseDTO,
    PresetApplyRequestDTO,
    PresetResultDTO,
)

from backend.app.dependencies import get_policy_service
from backend.app.services.policy_service import PolicyService

router = APIRouter()


@router.post("/crisis", response_model=CrisisResultDTO, status_code=201)
async def inject_crisis(
    request: CrisisInjectRequestDTO,
    service: PolicyService = Depends(get_policy_service),
):
    try:
        return await service.inject_crisis(request)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/presets", response_model=PresetResultDTO, status_code=201)
async def apply_preset(
    request: PresetApplyRequestDTO,
    service: PolicyService = Depends(get_policy_service),
):
    try:
        return await service.apply_policy_preset(request)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PolicyListResponseDTO)
async def list_policies(
    service: PolicyService = Depends(get_policy_service),
):
    return await service.list_policies()


@router.post("/", response_model=PolicyResponseDTO, status_code=201)
async def create_policy(
    request: PolicyCreateRequestDTO,
    service: PolicyService = Depends(get_policy_service),
):
    return await service.create_policy(request)


@router.get("/{policy_id}", response_model=PolicyResponseDTO)
async def get_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    policy = await service.get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.delete("/{policy_id}")
async def revoke_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    deleted = await service.revoke_policy(policy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"status": "revoked", "policy_id": policy_id}
