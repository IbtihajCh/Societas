import pytest
from unittest.mock import MagicMock

from shared.schemas.decision import DecisionRequest, DecisionOption
from shared.types.enums import ActionType
from models.config import AIConfig
from models.tie_break.tie_breaker import TieBreaker
from models.client.amd_client import AMDClient


def make_mock_client(result_content: str) -> MagicMock:
    client = MagicMock(spec=AMDClient)
    client.chat_completion.return_value = {
        "content": result_content,
        "finish_reason": "stop",
        "usage": {},
    }
    return client


class TestTieBreaker:
    def test_resolve_returns_selected_action(self):
        client = make_mock_client('{"action": "WORK", "confidence": 0.85, "reason": "Best option"}')
        breaker = TieBreaker(AIConfig(), client=client)
        request = DecisionRequest(
            agent_id="agent-001",
            state="Normal state",
            options=[
                DecisionOption(action=ActionType.WORK, label="Work", utility_scores={"wealth": 0.8}),
                DecisionOption(action=ActionType.SOCIALIZE, label="Socialize", utility_scores={"social": 0.7}),
            ],
        )
        response = breaker.resolve(request)
        assert response.action == ActionType.WORK
        assert response.confidence == 0.85
        assert response.reason == "Best option"

    def test_resolve_matches_by_label(self):
        client = make_mock_client('{"action": "Socialize", "confidence": 0.9, "reason": "Good choice"}')
        breaker = TieBreaker(AIConfig(), client=client)
        request = DecisionRequest(
            agent_id="agent-001",
            state="Normal",
            options=[
                DecisionOption(action=ActionType.WORK, label="Work", utility_scores={}),
                DecisionOption(action=ActionType.SOCIALIZE, label="Socialize", utility_scores={}),
            ],
        )
        response = breaker.resolve(request)
        assert response.action == ActionType.SOCIALIZE

    def test_fallback_on_parse_failure(self):
        client = make_mock_client("not valid json")
        breaker = TieBreaker(AIConfig(), client=client)
        request = DecisionRequest(
            agent_id="agent-001",
            state="Normal",
            options=[
                DecisionOption(action=ActionType.WORK, label="Work", utility_scores={}),
            ],
        )
        response = breaker.resolve(request)
        assert response.action == ActionType.WORK
        assert response.confidence == 0.3

    def test_fallback_on_empty_options(self):
        client = make_mock_client("not json")
        breaker = TieBreaker(AIConfig(), client=client)
        request = DecisionRequest(agent_id="a1", state="s")
        response = breaker.resolve(request)
        assert response.action == ActionType.IDLE

    def test_confidence_clamped(self):
        client = make_mock_client('{"action": "WORK", "confidence": 1.5}')
        breaker = TieBreaker(AIConfig(), client=client)
        request = DecisionRequest(
            agent_id="a1",
            state="s",
            options=[DecisionOption(action=ActionType.WORK, label="Work", utility_scores={})],
        )
        response = breaker.resolve(request)
        assert response.confidence <= 1.0
