"""Tests for AI Historian service and router methods."""

import pytest
from unittest.mock import patch, MagicMock

from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter
from shared.schemas.simulation_state import SimulationState


@pytest.fixture
def config() -> VLLMConfig:
    return VLLMConfig(
        base_url="http://test:8000/v1",
        api_key_e2b="key-e2b",
        api_key_moe_26b="key-moe",
        api_key_dense_31b="key-dense",
        timeout_seconds=5,
        max_retries=1,
    )


@pytest.fixture
def router(config: VLLMConfig) -> VLLMRouter:
    return VLLMRouter(config)


@pytest.fixture
def world() -> SimulationState:
    return SimulationState(
        time_step=100,
        population=80,
        economic_health=0.6,
        social_cohesion=0.55,
        crime_rate=0.05,
        unemployment_rate=0.10,
        tax_rate=0.20,
        welfare_enabled=True,
        food_availability=0.85,
        water_availability=0.90,
        protest_intensity=0.02,
        unlust=0.30,
        morality=0.65,
    )


class TestGenerateNarrative:
    def test_generate_narrative_returns_string(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": "The society entered a period of stability and growth."}]
        }
        with patch.object(router._client_dense, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.generate_narrative("Tell me about the society")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_generate_narrative_uses_dense_model(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": "A narrative entry."}]
        }
        with patch.object(router._client_dense, "post") as mock_post:
            mock_post.return_value = fake_response
            router.generate_narrative("Test context")
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer key-dense"


class TestMoralAssessment:
    def test_moral_assessment_returns_string(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": "The moral implications are significant."}]
        }
        with patch.object(router._client_moe, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.moral_assessment("Is this just?")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_moral_assessment_uses_moe_api_key(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": "Moral assessment text."}]
        }
        with patch.object(router._client_moe, "post") as mock_post:
            mock_post.return_value = fake_response
            router.moral_assessment("Test question")
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer key-moe"


class TestAIHistorianService:
    def test_generate_entry_returns_structured_dict(self, router: VLLMRouter, world: SimulationState) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": "At tick 100, the society flourished with high cohesion."}]
        }
        with patch.object(router._client_dense, "post") as mock_post:
            mock_post.return_value = fake_response
            from backend.app.services.ai_historian import AIHistorianService
            historian = AIHistorianService(router)
            entry = historian.generate_entry(world, 100)
            assert isinstance(entry, dict)
            assert "tick" in entry
            assert "narrative" in entry
            assert entry["tick"] == 100
            assert len(entry["narrative"]) > 0

    def test_get_history_returns_all_entries(self, router: VLLMRouter, world: SimulationState) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": "Entry text."}]
        }
        with patch.object(router._client_dense, "post") as mock_post:
            mock_post.return_value = fake_response
            from backend.app.services.ai_historian import AIHistorianService
            historian = AIHistorianService(router)
            historian.generate_entry(world, 50)
            historian.generate_entry(world, 100)
            history = historian.get_history()
            assert len(history) == 2
            assert history[0]["tick"] == 50
            assert history[1]["tick"] == 100

    def test_get_governance_advice_returns_combined(self, router: VLLMRouter, world: SimulationState) -> None:
        fake_dense = MagicMock()
        fake_dense.status_code = 200
        fake_dense.json.return_value = {
            "choices": [{"text": '{"assessment":"stable","recommendation":"lower taxes","watch_items":["crime"]}'}]
        }
        fake_moe = MagicMock()
        fake_moe.status_code = 200
        fake_moe.json.return_value = {
            "choices": [{"text": "The ethical concerns around taxation are balanced."}]
        }
        with (
            patch.object(router._client_dense, "post", return_value=fake_dense),
            patch.object(router._client_moe, "post", return_value=fake_moe),
        ):
            from backend.app.services.ai_historian import AIHistorianService
            historian = AIHistorianService(router)
            advice = historian.get_governance_advice(world, [])
            assert "governance" in advice
            assert "ethics" in advice
            assert advice["governance"]["assessment"] == "stable"
