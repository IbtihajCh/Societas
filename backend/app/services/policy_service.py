import uuid
from dataclasses import asdict
from typing import Optional

from shared.dto.policy_dto import (
    PolicyCreateRequestDTO,
    PolicyListResponseDTO,
    PolicyResponseDTO,
)
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.schemas.policy import Policy, PolicyWeights
from shared.types.aliases import PolicyId
from shared.types.enums import PolicyCategory

from backend.app.repositories.policy_repository import PolicyRepository


class PolicyService:
    def __init__(
        self,
        engine: Optional[ISimulationEngine] = None,
        repository: Optional[PolicyRepository] = None,
    ):
        self._engine = engine
        self._repository = repository or PolicyRepository()

    async def create_policy(self, request: PolicyCreateRequestDTO) -> PolicyResponseDTO:
        policy = Policy(
            id=PolicyId(uuid.uuid4().hex[:12]),
            name=request.name,
            description=request.description,
            category=request.category,
            weights=PolicyWeights(**{k: float(v) for k, v in request.weights.items()}) if request.weights else PolicyWeights(),
            is_active=True,
        )
        await self._repository.save(policy)
        if self._engine is not None:
            self._engine.apply_policy(policy)
        return self._policy_to_dto(policy)

    async def list_policies(self) -> PolicyListResponseDTO:
        policies = await self._repository.load_all()
        return PolicyListResponseDTO(
            policies=[self._policy_to_dto(p) for p in policies],
            total=len(policies),
        )

    async def get_policy(self, policy_id: str) -> Optional[PolicyResponseDTO]:
        policy = await self._repository.load(policy_id)
        if policy is None:
            return None
        return self._policy_to_dto(policy)

    async def revoke_policy(self, policy_id: str) -> bool:
        if self._engine is not None:
            self._engine.revoke_policy(policy_id)
        return await self._repository.delete(policy_id)

    def _policy_to_dto(self, policy: Policy) -> PolicyResponseDTO:
        return PolicyResponseDTO(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            category=policy.category,
            weights={k: float(v) for k, v in asdict(policy.weights).items()},
            is_active=policy.is_active,
            enactment_tick=policy.enactment_tick,
        )
