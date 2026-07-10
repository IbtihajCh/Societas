"""Tests for crisis injection and policy preset controls."""

import asyncio
import pytest
from unittest.mock import MagicMock

from shared.dto.policy_dto import CrisisInjectRequestDTO, PresetApplyRequestDTO
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import CrisisType, PolicyPreset

from backend.app.services.policy_service import PolicyService


@pytest.fixture
def engine():
    eng = MagicMock()
    state = SimulationState()
    eng.get_state.return_value = state
    return eng


@pytest.fixture
def service(engine):
    return PolicyService(engine=engine)


class TestCrisisInjection:
    def test_natural_disaster_lowers_food_and_water(self, service, engine):
        state = engine.get_state()
        state.food_availability = 0.9
        state.water_availability = 0.9

        result = asyncio.run(service.inject_crisis(CrisisInjectRequestDTO(crisis_type=CrisisType.NATURAL_DISASTER)))

        assert result.crisis_type == "natural_disaster"
        assert "food_availability" in result.changes
        assert state.food_availability < 0.9
        assert state.water_availability < 0.9

    def test_economic_crash_raises_unemployment(self, service, engine):
        state = engine.get_state()
        state.unemployment_rate = 0.1

        result = asyncio.run(service.inject_crisis(CrisisInjectRequestDTO(crisis_type=CrisisType.ECONOMIC_CRASH)))

        assert result.crisis_type == "economic_crash"
        assert state.unemployment_rate > 0.1
        assert state.economic_health < 0.5

    def test_crime_wave_raises_crime_rate(self, service, engine):
        state = engine.get_state()
        state.crime_rate = 0.05

        result = asyncio.run(service.inject_crisis(CrisisInjectRequestDTO(crisis_type=CrisisType.CRIME_WAVE)))

        assert result.crisis_type == "crime_wave"
        assert state.crime_rate > 0.05
        assert state.public_order < 0.5

    def test_plague_lowers_food_and_economy(self, service, engine):
        state = engine.get_state()
        state.food_availability = 0.85

        result = asyncio.run(service.inject_crisis(CrisisInjectRequestDTO(crisis_type=CrisisType.PLAGUE)))

        assert result.crisis_type == "plague"
        assert state.food_availability < 0.85
        assert state.social_cohesion < 0.5

    def test_runtime_error_if_no_engine(self):
        service = PolicyService(engine=None)
        with pytest.raises(RuntimeError, match="Simulation not started"):
            asyncio.run(service.inject_crisis(CrisisInjectRequestDTO()))


class TestPolicyPresets:
    def test_ubi_enables_welfare(self, service, engine):
        state = engine.get_state()
        state.welfare_enabled = False
        state.welfare_amount = 0.0

        result = asyncio.run(service.apply_policy_preset(PresetApplyRequestDTO(preset_name=PolicyPreset.UNIVERSAL_BASIC_INCOME)))

        assert result.preset_name == "universal_basic_income"
        assert state.welfare_enabled is True
        assert state.welfare_amount == 20.0
        assert "welfare_enabled" in result.changes
        assert len(result.policy_id) > 0

    def test_police_state_reduces_crime(self, service, engine):
        state = engine.get_state()
        state.crime_rate = 0.3

        result = asyncio.run(service.apply_policy_preset(PresetApplyRequestDTO(preset_name=PolicyPreset.POLICE_STATE)))

        assert result.preset_name == "police_state"
        assert state.crime_rate < 0.3
        assert state.public_order > 0.5
        assert state.social_cohesion < 0.5

    def test_deregulation_lowers_tax(self, service, engine):
        state = engine.get_state()
        state.tax_rate = 0.3

        result = asyncio.run(service.apply_policy_preset(PresetApplyRequestDTO(preset_name=PolicyPreset.MARKET_DEREGULATION)))

        assert result.preset_name == "market_deregulation"
        assert state.tax_rate < 0.3
        assert state.economic_health > 0.5
        assert state.unemployment_rate < 0.3

    def test_runtime_error_if_no_engine(self):
        service = PolicyService(engine=None)
        with pytest.raises(RuntimeError, match="Simulation not started"):
            asyncio.run(service.apply_policy_preset(PresetApplyRequestDTO()))

    def test_unknown_preset_raises_error(self, service, engine):
        with pytest.raises(ValueError, match="Unknown preset"):
            asyncio.run(service.apply_policy_preset(PresetApplyRequestDTO(
                preset_name="nonexistent"  # type: ignore
            )))
