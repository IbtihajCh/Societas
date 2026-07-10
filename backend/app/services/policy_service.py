import uuid
from dataclasses import asdict
from typing import Optional

from shared.dto.policy_dto import (
    CrisisInjectRequestDTO,
    CrisisResultDTO,
    PolicyCreateRequestDTO,
    PolicyListResponseDTO,
    PolicyResponseDTO,
    PresetApplyRequestDTO,
    PresetResultDTO,
)
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.schemas.policy import Policy, PolicyWeights
from shared.types.aliases import PolicyId
from shared.types.enums import CrisisType, PolicyCategory, PolicyPreset, WealthClass

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

    async def inject_crisis(self, request: CrisisInjectRequestDTO) -> CrisisResultDTO:
        if self._engine is None:
            raise RuntimeError("Simulation not started")
        state = self._engine.get_state()
        crisis_type = request.crisis_type

        if crisis_type == CrisisType.NATURAL_DISASTER:
            changes = {
                "food_availability": max(0.0, state.food_availability - 0.6),
                "water_availability": max(0.0, state.water_availability - 0.5),
                "economic_health": max(0.0, state.economic_health - 0.2),
            }
            desc = "A major natural disaster has struck, destroying crops and disrupting water supplies."
        elif crisis_type == CrisisType.ECONOMIC_CRASH:
            changes = {
                "unemployment_rate": min(1.0, state.unemployment_rate + 0.4),
                "economic_health": max(0.0, state.economic_health - 0.4),
                "tax_rate": max(0.0, state.tax_rate + 0.1),
            }
            desc = "The economy has crashed — widespread layoffs and falling markets."
        elif crisis_type == CrisisType.CRIME_WAVE:
            changes = {
                "crime_rate": min(1.0, state.crime_rate + 0.35),
                "public_order": max(0.0, state.public_order - 0.3),
                "social_cohesion": max(0.0, state.social_cohesion - 0.15),
            }
            desc = "A wave of organized crime has swept through the society."
        elif crisis_type == CrisisType.PLAGUE:
            changes = {
                "food_availability": max(0.0, state.food_availability - 0.3),
                "economic_health": max(0.0, state.economic_health - 0.15),
                "social_cohesion": max(0.0, state.social_cohesion - 0.2),
            }
            desc = "A deadly plague is spreading through the population."
        else:
            changes = {}
            desc = "Unknown crisis."

        for key, value in changes.items():
            setattr(state, key, value)

        return CrisisResultDTO(
            crisis_type=crisis_type.value,
            description=desc,
            changes=changes,
        )

    async def apply_policy_preset(self, request: PresetApplyRequestDTO) -> PresetResultDTO:
        if self._engine is None:
            raise RuntimeError("Simulation not started")
        state = self._engine.get_state()

        preset = request.preset_name

        if preset == PolicyPreset.UNIVERSAL_BASIC_INCOME:
            name = "Universal Basic Income"
            desc = "Provides a regular cash payment to all citizens regardless of employment."
            state.welfare_enabled = True
            state.welfare_amount = 20.0
            state.tax_rate = min(1.0, state.tax_rate + 0.15)
            weights = PolicyWeights(social_welfare=0.6, economic_freedom=-0.2)
            changes = {"welfare_enabled": True, "welfare_amount": 20.0, "tax_rate": round(state.tax_rate, 2)}
        elif preset == PolicyPreset.POLICE_STATE:
            name = "Police State"
            desc = "Heavy surveillance and policing to maintain order at any cost."
            state.crime_rate = max(0.0, state.crime_rate - 0.15)
            state.public_order = min(1.0, state.public_order + 0.2)
            state.social_cohesion = max(0.0, state.social_cohesion - 0.1)
            weights = PolicyWeights(public_order=0.8, cultural_preservation=-0.3)
            changes = {"crime_rate": round(state.crime_rate, 2), "public_order": round(state.public_order, 2), "social_cohesion": round(state.social_cohesion, 2)}
        elif preset == PolicyPreset.MARKET_DEREGULATION:
            name = "Market Deregulation"
            desc = "Removes government regulations to stimulate economic growth."
            state.tax_rate = max(0.0, state.tax_rate - 0.1)
            state.economic_health = min(1.0, state.economic_health + 0.15)
            state.unemployment_rate = max(0.0, state.unemployment_rate - 0.05)
            weights = PolicyWeights(economic_freedom=0.7, social_welfare=-0.3, environmental_protection=-0.2)
            changes = {"tax_rate": round(state.tax_rate, 2), "economic_health": round(state.economic_health, 2), "unemployment_rate": round(state.unemployment_rate, 2)}
        else:
            raise ValueError(f"Unknown preset: {preset}")

        policy = Policy(
            id=PolicyId(uuid.uuid4().hex[:12]),
            name=name,
            description=desc,
            weights=weights,
            is_active=True,
        )
        await self._repository.save(policy)
        self._engine.apply_policy(policy)

        return PresetResultDTO(
            preset_name=preset.value,
            description=desc,
            policy_id=policy.id,
            changes=changes,
        )

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
