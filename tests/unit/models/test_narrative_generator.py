import pytest
from unittest.mock import MagicMock

from shared.schemas.news_event import NewsEvent, SpotlightNarration
from models.router.config import AIConfig
from models.narration.narrative_generator import NarrativeGenerator
from models.client.amd_client import AMDClient


def make_mock_client(result_content: str) -> MagicMock:
    client = MagicMock(spec=AMDClient)
    client.chat_completion.return_value = {
        "content": result_content,
        "finish_reason": "stop",
        "usage": {},
    }
    return client


class TestNarrativeGeneratorNews:
    def test_generate_news_returns_news_event(self):
        client = make_mock_client('{"headline": "Market Crash", "body": "Markets fell sharply.", "category": "ECONOMIC", "importance": 0.8}')
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_news(
            events=[{"type": "resource_shift", "tick": 100}],
            state_deltas={"economic_health": -0.2},
        )
        assert isinstance(result, NewsEvent)
        assert "Market Crash" in result.headline
        assert "Markets fell sharply." in result.body
        assert result.importance == 0.8

    def test_generate_news_fallback_on_parse_failure(self):
        client = make_mock_client("Plain text response without json")
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_news(
            events=[{"type": "conflict", "tick": 50}],
            state_deltas={},
        )
        assert isinstance(result, NewsEvent)
        assert result.headline == "Simulation Update"
        assert "Plain text" in result.body

    def test_generate_news_empty_events(self):
        client = make_mock_client("Some content")
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_news(events=[], state_deltas={})
        assert isinstance(result, NewsEvent)

    def test_generate_news_clamps_importance(self):
        client = make_mock_client('{"headline": "H", "importance": 1.5}')
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_news(events=[{"type": "event", "tick": 1}], state_deltas={})
        assert result.importance <= 1.0


class TestNarrativeGeneratorSpotlight:
    def test_generate_spotlight_returns_spotlight(self):
        client = make_mock_client('{"title": "Rise of Marcus", "content": "Marcus made key decisions.", "mood": "confident"}')
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_spotlight("agent-001", [{"type": "decision", "tick": 100}])
        assert isinstance(result, SpotlightNarration)
        assert result.agent_id == "agent-001"
        assert result.title == "Rise of Marcus"
        assert result.mood == "confident"

    def test_generate_spotlight_fallback(self):
        client = make_mock_client("Raw text")
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_spotlight("agent-001", [])
        assert isinstance(result, SpotlightNarration)
        assert result.agent_id == "agent-001"
        assert "Raw text" in result.content

    def test_generate_spotlight_empty_events(self):
        client = make_mock_client('{"title": "T", "content": "C"}')
        generator = NarrativeGenerator(AIConfig(), client=client)
        result = generator.generate_spotlight("agent-001", [])
        assert result.agent_id == "agent-001"
