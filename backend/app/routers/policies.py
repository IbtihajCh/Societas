from fastapi import APIRouter, Depends, HTTPException

from shared.dto.policy_dto import PolicyCreateRequestDTO, PolicyListResponseDTO, PolicyResponseDTO

from backend.app.dependencies import get_policy_service
from backend.app.services.policy_service import PolicyService

router = APIRouter()


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
