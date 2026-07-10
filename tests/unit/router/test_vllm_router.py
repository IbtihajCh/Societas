"""Tests for VLLMRouter with mocked httpx responses."""

import json
import pytest
from unittest.mock import patch, MagicMock

from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter
from shared.schemas.agent_state import AgentState
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


class TestVLLMRouterAvailable:
    def test_is_available_returns_true_when_server_up(self, router: VLLMRouter) -> None:
        with patch.object(router._client_dense, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert router.is_available() is True
            mock_get.assert_called_once_with(
                "/models", headers={"Authorization": "Bearer key-dense"}
            )

    def test_is_available_returns_false_on_error(self, router: VLLMRouter) -> None:
        with patch.object(router._client_dense, "get") as mock_get:
            mock_get.side_effect = ConnectionError("no route")
            assert router.is_available() is False


class TestVLLMRouterAgentDecide:
    def test_agent_decide_returns_valid_json(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"message": {"content": '{"action":"work","feeling":"productive","reason":"need money"}'}}]
        }

        with patch.object(router._client_e2b, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.agent_decide("some prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert data["action"] == "work"
            assert data["feeling"] == "productive"
            assert "reason" in data

    def test_agent_decide_fallback_on_error(self, router: VLLMRouter) -> None:
        with patch.object(router._client_e2b, "post") as mock_post:
            mock_post.side_effect = ConnectionError("no route")
            result = router.agent_decide("prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert data["action"] == "work"
            assert "fallback" in data["reason"].lower()

    def test_agent_decide_fallback_on_bad_json(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"choices": [{"message": {"content": "not valid json"}}]}

        with patch.object(router._client_e2b, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.agent_decide("prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert "fallback" in data["reason"].lower()

    def test_agent_decide_batch_returns_list(self, router: VLLMRouter) -> None:
        prompts = ["p1", "p2", "p3"]
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"action":"work","feeling":"ok","reason":"a"}'}},
                {"message": {"content": '{"action":"rest","feeling":"tired","reason":"b"}'}},
                {"message": {"content": '{"action":"beg","feeling":"sad","reason":"c"}'}},
            ]
        }

        with patch.object(router._client_e2b, "post") as mock_post:
            mock_post.return_value = fake_response
            results = router.agent_decide_batch(prompts, [MagicMock()] * 3, MagicMock())
            assert len(results) == 3
            for r in results:
                data = json.loads(r)
                assert "action" in data
            # Verify the batched prompts each go through as individual chat messages
            assert mock_post.call_count == 3
            call_kwargs = mock_post.call_args[1]
            assert "messages" in call_kwargs["json"]
            assert len(call_kwargs["json"]["messages"]) == 1
            assert call_kwargs["json"]["messages"][0]["role"] == "user"


class TestVLLMRouterMoralReasoning:
    def test_moral_reasoning_returns_reasoning_field(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"message": {"content": '{"action":"console","feeling":"empathetic","reason":"moral duty to help"}'}}]
        }

        with patch.object(router._client_moe, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.moral_reasoning("prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert "reason" in data
            assert data["action"] == "console"

    def test_moral_reasoning_uses_moe_api_key(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"choices": [{"message": {"content": '{"action":"work","feeling":"ok","reason":"ok"}'}}]}

        with patch.object(router._client_moe, "post") as mock_post:
            mock_post.return_value = fake_response
            router.moral_reasoning("prompt", MagicMock(), MagicMock())
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer key-moe"

    def test_moral_reasoning_batch(self, router: VLLMRouter) -> None:
        prompts = ["p1", "p2"]
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"action":"share","feeling":"generous","reason":"m1"}'}},
                {"message": {"content": '{"action":"comply","feeling":"neutral","reason":"m2"}'}},
            ]
        }

        with patch.object(router._client_moe, "post") as mock_post:
            mock_post.return_value = fake_response
            results = router.moral_reasoning_batch(prompts, [MagicMock()] * 2, MagicMock())
            assert len(results) == 2


class TestVLLMRouterGovernance:
    def _make_world(self) -> SimulationState:
        return SimulationState(
            crime_rate=0.05,
            unemployment_rate=0.10,
            tax_rate=0.15,
            welfare_enabled=False,
            food_availability=0.85,
        )

    def _make_agents(self, count: int = 1) -> list[AgentState]:
        return [AgentState(id=str(i), is_alive=True, unlust=0.3) for i in range(count)]

    def test_governance_advisory_returns_dict(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"message": {"content": '{"assessment":"stable","recommendation":"none","watch_items":[]}'}}]
        }

        with patch.object(router._client_dense, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.governance_advisory(self._make_world(), self._make_agents())
            assert isinstance(result, dict)
            assert "assessment" in result
            assert "recommendation" in result
            assert "watch_items" in result

    def test_governance_advisory_fallback(self, router: VLLMRouter) -> None:
        with patch.object(router._client_dense, "post") as mock_post:
            mock_post.side_effect = ConnectionError("no route")
            result = router.governance_advisory(self._make_world(), self._make_agents())
            assert result["assessment"] == "Unavailable"
            assert result["recommendation"] == "Fallback to deterministic governance"


class TestVLLMRouterCallCount:
    def test_call_count_tracks_calls(self, router: VLLMRouter) -> None:
        fake_ok = MagicMock()
        fake_ok.status_code = 200
        fake_ok.json.return_value = {"choices": [{"message": {"content": '{"action":"work","feeling":"ok","reason":"ok"}'}}]}

        with (
            patch.object(router._client_e2b, "post", return_value=fake_ok),
            patch.object(router._client_moe, "post", return_value=fake_ok),
        ):
            assert router.call_count == 0
            router.agent_decide("p1", MagicMock(), MagicMock())
            assert router.call_count == 1
            router.moral_reasoning("p2", MagicMock(), MagicMock())
            assert router.call_count == 2
