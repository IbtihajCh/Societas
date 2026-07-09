import logging
from typing import Optional

from shared.schemas.decision import DecisionRequest, DecisionResponse, DecisionOption
from shared.types.enums import ActionType
from models.router.config import AIConfig
from models.client.prompt_loader import PromptLoader
from models.client.amd_client import AMDClient
from models.client.response_parser import parse_response, ParseError

logger = logging.getLogger("societas.ai.tie_break")


class TieBreaker:
    def __init__(self, config: AIConfig, client: Optional[AMDClient] = None):
        self.config = config
        self._client = client or AMDClient(config)
        self._loader = PromptLoader()

    def resolve(self, request: DecisionRequest) -> DecisionResponse:
        prompt, frontmatter = self._loader.load("tie-break.md")
        temperature = frontmatter.get("temperature", 0.2)
        max_tokens = frontmatter.get("max_tokens", 196)

        options_text = "; ".join(
            f"{o.action.value if hasattr(o.action, 'value') else o.action}: {o.label} (scores={o.utility_scores})"
            for o in request.options
        )

        result = self._client.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Resolve this ambiguous decision for agent {request.agent_id}.\n"
                        f"State: {request.state}\n"
                        f"Unlust: {request.unlust}\n"
                        f"Morality: {request.morality}\n"
                        f"Options:\n{options_text}"
                    ),
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            parsed = parse_response(result["content"], dict)
            action_label = str(parsed.get("action", ""))
            action = next(
                (o.action for o in request.options if (
                    o.label == action_label
                    or str(o.action) == action_label
                    or (hasattr(o.action, "value") and o.action.value == action_label)
                )),
                request.options[0].action if request.options else ActionType.IDLE,
            )
            return DecisionResponse(
                action=action,
                confidence=min(max(float(parsed.get("confidence", 0.5)), 0.0), 1.0),
                reason=parsed.get("reason", ""),
            )
        except (ParseError, ValueError, IndexError) as e:
            logger.error("tie-break parsing failed: %s", e)
            return DecisionResponse(
                action=request.options[0].action if request.options else ActionType.IDLE,
                confidence=0.3,
                reason=f"AI tie-break failed, defaulting to first option. Error: {e}",
            )
