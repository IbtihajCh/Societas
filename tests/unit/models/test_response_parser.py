import pytest

from models.client.response_parser import parse_response, ParseError
from dataclasses import dataclass


@dataclass
class SimpleResult:
    action: str = ""
    confidence: float = 0.0


class TestParseResponse:
    def test_parse_valid_json(self):
        text = '{"action": "WORK", "confidence": 0.85}'
        result = parse_response(text, dict)
        assert result["action"] == "WORK"
        assert result["confidence"] == 0.85

    def test_parse_json_in_fence(self):
        text = "```json\n{\"action\": \"WORK\", \"confidence\": 0.85}\n```"
        result = parse_response(text, dict)
        assert result["action"] == "WORK"

    def test_parse_json_in_fence_no_lang(self):
        text = "```\n{\"action\": \"WORK\"}\n```"
        result = parse_response(text, dict)
        assert result["action"] == "WORK"

    def test_invalid_json_raises_error(self):
        text = "not json at all"
        with pytest.raises(ParseError):
            parse_response(text, dict)

    def test_parse_to_dataclass(self):
        text = '{"action": "WORK", "confidence": 0.75}'
        result = parse_response(text, SimpleResult)
        assert result.action == "WORK"
        assert result.confidence == 0.75

    def test_extra_fields_ignored(self):
        text = '{"action": "WORK", "confidence": 0.5, "extra": "ignored"}'
        result = parse_response(text, SimpleResult)
        assert result.action == "WORK"

    def test_retry_then_fail(self):
        text = "not json"
        with pytest.raises(ParseError, match="failed after 2 attempts"):
            parse_response(text, dict, max_retries=2)
