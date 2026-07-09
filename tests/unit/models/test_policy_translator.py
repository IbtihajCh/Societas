import pytest
from unittest.mock import MagicMock

from shared.schemas.policy import PolicyWeights
from models.router.config import AIConfig
from models.policy.policy_translator import PolicyTranslator
from models.client.amd_client import AMDClient


def make_mock_client(result_content: str) -> MagicMock:
    client = MagicMock(spec=AMDClient)
    client.chat_completion.return_value = {
        "content": result_content,
        "finish_reason": "stop",
        "usage": {},
    }
    return client


class TestPolicyTranslator:
    def test_translate_returns_weights(self):
        client = make_mock_client(
            '{"weights": {"economic_freedom": 0.5, "social_welfare": -0.3}, "confidence": 0.8, "reasoning": "test"}'
        )
        translator = PolicyTranslator(AIConfig(), client=client)
        result = translator.translate(
            persona="A capitalist",
            goal="Reduce taxes",
            context={"world_state_summary": "stable", "time_step": 50, "active_policies": []},
        )
        assert isinstance(result, PolicyWeights)
        assert result.economic_freedom == 0.5
        assert result.social_welfare == -0.3

    def test_translate_missing_weights_defaults_zero(self):
        client = make_mock_client('{"weights": {}}')
        translator = PolicyTranslator(AIConfig(), client=client)
        result = translator.translate("p", "g", {})
        assert result.economic_freedom == 0.0
        assert result.social_welfare == 0.0
        assert result.public_order == 0.0

    def test_translate_parse_failure_returns_empty_weights(self):
        client = make_mock_client("bad json")
        translator = PolicyTranslator(AIConfig(), client=client)
        result = translator.translate("p", "g", {})
        assert isinstance(result, PolicyWeights)
        assert result.economic_freedom == 0.0

    def test_translate_calls_chat_completion(self):
        mock_client = MagicMock(spec=AMDClient)
        mock_client.chat_completion.return_value = {
            "content": '{"weights": {"economic_freedom": 0.2}}',
            "finish_reason": "stop",
            "usage": {},
        }
        translator = PolicyTranslator(AIConfig(), client=mock_client)
        translator.translate("Persona X", "Goal Y", {"world_state_summary": "s", "time_step": 1})
        mock_client.chat_completion.assert_called_once()
        _, kwargs = mock_client.chat_completion.call_args
        messages = kwargs["messages"]
        user_msg = messages[1]["content"]
        assert "Persona X" in user_msg
        assert "Goal Y" in user_msg
