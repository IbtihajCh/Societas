import logging
from typing import Optional

from shared.schemas.decision import DecisionRequest, DecisionResponse
from shared.schemas.policy import PolicyWeights
from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.interfaces.i_ai_router import IAIRouter

from models.router.config import AIConfig
from models.policy.policy_translator import PolicyTranslator
from models.narration.narrative_generator import NarrativeGenerator
from models.personas.persona_generator import PersonaGenerator
from models.tie_break.tie_breaker import TieBreaker

logger = logging.getLogger("societas.ai.router")


class AIRouter(IAIRouter):
    def __init__(
        self,
        config: Optional[AIConfig] = None,
        policy_translator: Optional[PolicyTranslator] = None,
        narrative_generator: Optional[NarrativeGenerator] = None,
        persona_generator: Optional[PersonaGenerator] = None,
        tie_breaker: Optional[TieBreaker] = None,
    ):
        self.config = config or AIConfig()
        self._policy_translator = policy_translator or PolicyTranslator(self.config)
        self._narrative_generator = narrative_generator or NarrativeGenerator(self.config)
        self._persona_generator = persona_generator or PersonaGenerator(self.config)
        self._tie_breaker = tie_breaker or TieBreaker(self.config)

    def translate_policy(self, persona: str, goal: str, context: dict) -> PolicyWeights:
        return self._policy_translator.translate(persona, goal, context)

    def tie_break(self, request: DecisionRequest) -> DecisionResponse:
        return self._tie_breaker.resolve(request)

    def generate_news(self, events: list, state_deltas: dict) -> NewsEvent:
        return self._narrative_generator.generate_news(events, state_deltas)

    def generate_persona(self, traits: dict) -> str:
        return self._persona_generator.generate(traits)

    def generate_narration(self, agent_id: str, events: list) -> SpotlightNarration:
        return self._narrative_generator.generate_spotlight(agent_id, events)

    def is_available(self) -> bool:
        return True
