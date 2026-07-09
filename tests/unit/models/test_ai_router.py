import pytest
from unittest.mock import MagicMock

from shared.schemas.decision import DecisionRequest, DecisionResponse, DecisionOption
from shared.schemas.policy import PolicyWeights
from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.types.aliases import EventId
from shared.types.enums import ActionType
from models.router.ai_router import AIRouter
from models.router.config import AIConfig
from models.policy.policy_translator import PolicyTranslator
from models.narration.narrative_generator import NarrativeGenerator
from models.personas.persona_generator import PersonaGenerator
from models.tie_break.tie_breaker import TieBreaker


class TestAIRouter:
    def test_router_initialization(self):
        router = AIRouter()
        assert router.config is not None
        assert router.config.amd_base_url == ""

    def test_router_initialization_with_config(self):
        config = AIConfig(request_timeout=60.0)
        router = AIRouter(config=config)
        assert router.config.request_timeout == 60.0

    def test_translate_policy_delegates(self):
        mock_pt = MagicMock(spec=PolicyTranslator)
        expected = PolicyWeights(economic_freedom=0.5)
        mock_pt.translate.return_value = expected
        router = AIRouter(policy_translator=mock_pt)
        result = router.translate_policy("persona", "goal", {})
        assert result == expected
        mock_pt.translate.assert_called_once_with("persona", "goal", {})

    def test_tie_break_delegates(self):
        mock_tb = MagicMock(spec=TieBreaker)
        expected = DecisionResponse(action=ActionType.WORK, confidence=0.8)
        mock_tb.resolve.return_value = expected
        router = AIRouter(tie_breaker=mock_tb)
        request = DecisionRequest(agent_id="a1", state="s")
        result = router.tie_break(request)
        assert result == expected
        mock_tb.resolve.assert_called_once_with(request)

    def test_generate_news_delegates(self):
        mock_ng = MagicMock(spec=NarrativeGenerator)
        expected = NewsEvent(id=EventId("news-1"), headline="Test")
        mock_ng.generate_news.return_value = expected
        router = AIRouter(narrative_generator=mock_ng)
        result = router.generate_news([], {})
        assert result == expected

    def test_generate_persona_delegates(self):
        mock_pg = MagicMock(spec=PersonaGenerator)
        mock_pg.generate.return_value = "A test persona"
        router = AIRouter(persona_generator=mock_pg)
        result = router.generate_persona({"trait": 0.5})
        assert result == "A test persona"

    def test_generate_narration_delegates(self):
        mock_ng = MagicMock(spec=NarrativeGenerator)
        expected = SpotlightNarration(agent_id="a1", content="test")
        mock_ng.generate_spotlight.return_value = expected
        router = AIRouter(narrative_generator=mock_ng)
        result = router.generate_narration("a1", [])
        assert result == expected

    def test_is_available(self):
        router = AIRouter()
        assert router.is_available() is True


