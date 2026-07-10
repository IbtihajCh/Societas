import json
import logging
from typing import Optional

from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.types.aliases import EventId, TickNumber
from models.config import AIConfig
from models.client.prompt_loader import PromptLoader
from models.client.amd_client import AMDClient
from models.client.response_parser import parse_response, ParseError

logger = logging.getLogger("societas.ai.narration")


class NarrativeGenerator:
    def __init__(self, config: AIConfig, client: Optional[AMDClient] = None):
        self.config = config
        self._client = client or AMDClient(config)
        self._loader = PromptLoader()

    def generate_news(self, events: list, state_deltas: dict) -> NewsEvent:
        prompt, frontmatter = self._loader.load("narrative-generation.md")
        temperature = frontmatter.get("temperature", 0.8)
        max_tokens = frontmatter.get("max_tokens", 512)

        result = self._client.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Generate a news dispatch from these events:\n"
                        f"{json.dumps(events, indent=2)}\n\n"
                        f"State deltas:\n{json.dumps(state_deltas, indent=2)}"
                    ),
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = result.get("content", "").strip()
        try:
            parsed = parse_response(content, dict)
            events_list = events or []
            tick_val = int(parsed.get("tick", 0)) or (max([e.get("tick", 0) for e in events_list] + [0]) if events_list else 0)
            return NewsEvent(
                id=EventId(f"news-{tick_val}-{events_list[0].get('type', 'event') if events_list else 'dispatch'}"),
                tick=TickNumber(tick_val),
                headline=parsed.get("headline", "Simulation Dispatch"),
                dateline=parsed.get("dateline", ""),
                body=parsed.get("body", content),
                bylines=parsed.get("bylines", []),
                category=parsed.get("category", "general"),
                importance=min(max(float(parsed.get("importance", 0.5)), 0.0), 1.0),
            )
        except (ParseError, ValueError) as e:
            logger.warning("news parsing failed, using raw content: %s", e)
            events_list = events or []
            tick_val = max([e.get("tick", 0) for e in events_list] + [0]) if events_list else 0
            return NewsEvent(
                id=EventId(f"news-raw-{tick_val}"),
                tick=TickNumber(tick_val),
                headline="Simulation Update",
                body=content,
                category="general",
                importance=0.5,
            )

    def generate_spotlight(self, agent_id: str, events: list) -> SpotlightNarration:
        prompt, frontmatter = self._loader.load("narrative-generation.md")
        temperature = frontmatter.get("temperature", 0.8)
        max_tokens = frontmatter.get("max_tokens", 512)

        result = self._client.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Generate a spotlight narration for agent {agent_id}.\n"
                        f"Events:\n{json.dumps(events, indent=2)}"
                    ),
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = result.get("content", "").strip()
        try:
            parsed = parse_response(content, dict)
            return SpotlightNarration(
                agent_id=agent_id,
                tick=TickNumber(int(parsed.get("tick", 0))),
                title=parsed.get("title", f"Spotlight: {agent_id}"),
                content=parsed.get("content", content),
                mood=parsed.get("mood", "neutral"),
                key_events=parsed.get("key_events", []),
            )
        except (ParseError, ValueError) as e:
            logger.warning("spotlight parsing failed, using raw content: %s", e)
            return SpotlightNarration(
                agent_id=agent_id,
                content=content,
            )
