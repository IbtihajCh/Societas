import pytest
from unittest.mock import MagicMock

from models.router.config import AIConfig
from models.personas.persona_generator import PersonaGenerator
from models.client.amd_client import AMDClient


def make_mock_client(result_content: str) -> MagicMock:
    client = MagicMock(spec=AMDClient)
    client.chat_completion.return_value = {
        "content": result_content,
        "finish_reason": "stop",
        "usage": {},
    }
    return client


class TestPersonaGenerator:
    def test_generate_returns_persona_string(self):
        client = make_mock_client("Marcus is a mercantile magnate.")
        generator = PersonaGenerator(AIConfig(), client=client)
        result = generator.generate({"ambition": 0.9, "materialism": 0.7})
        assert result == "Marcus is a mercantile magnate."

    def test_generate_empty_content_returns_fallback(self):
        client = make_mock_client("   ")
        generator = PersonaGenerator(AIConfig(), client=client)
        result = generator.generate({})
        assert result == "A simple simulation agent."

    def test_generate_strips_whitespace(self):
        client = make_mock_client("  Elara is wise.  ")
        generator = PersonaGenerator(AIConfig(), client=client)
        result = generator.generate({"wisdom": 0.8})
        assert result == "Elara is wise."

    def test_generate_calls_with_correct_params(self):
        mock_client = MagicMock(spec=AMDClient)
        mock_client.chat_completion.return_value = {
            "content": "A persona",
            "finish_reason": "stop",
            "usage": {},
        }
        generator = PersonaGenerator(AIConfig(), client=mock_client)
        generator.generate({"openness": 0.7, "ambition": 0.9})
        _, kwargs = mock_client.chat_completion.call_args
        messages = kwargs["messages"]
        user_msg = messages[1]["content"]
        assert "openness=0.7" in user_msg
        assert kwargs.get("max_tokens") == 128
