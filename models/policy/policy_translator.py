import logging
from typing import Optional

from shared.schemas.policy import PolicyWeights
from models.config import AIConfig
from models.client.prompt_loader import PromptLoader
from models.client.amd_client import AMDClient
from models.client.response_parser import parse_response, ParseError

logger = logging.getLogger("societas.ai.policy")


class PolicyTranslator:
    def __init__(self, config: AIConfig, client: Optional[AMDClient] = None):
        self.config = config
        self._client = client or AMDClient(config)
        self._loader = PromptLoader()

    def translate(self, persona: str, goal: str, context: dict) -> PolicyWeights:
        prompt, frontmatter = self._loader.load("policy-translation.md")
        temperature = frontmatter.get("temperature", 0.3)
        max_tokens = frontmatter.get("max_tokens", 256)

        context_text = (
            f"world_state_summary: {context.get('world_state_summary', 'N/A')}\n"
            f"time_step: {context.get('time_step', 'N/A')}\n"
            f"active_policies: {context.get('active_policies', [])}"
        )

        result = self._client.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Translate this agent's policy goal into utility weights.\n"
                        f"Persona: {persona}\n"
                        f"Goal: {goal}\n"
                        f"Context:\n{context_text}"
                    ),
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            parsed = parse_response(result["content"], dict)
            weights_data = parsed.get("weights", {})
            return PolicyWeights(
                economic_freedom=float(weights_data.get("economic_freedom", 0.0)),
                social_welfare=float(weights_data.get("social_welfare", 0.0)),
                environmental_protection=float(weights_data.get("environmental_protection", 0.0)),
                public_order=float(weights_data.get("public_order", 0.0)),
                innovation=float(weights_data.get("innovation", 0.0)),
                cultural_preservation=float(weights_data.get("cultural_preservation", 0.0)),
            )
        except (ParseError, ValueError) as e:
            logger.error("policy translation parsing failed: %s", e)
            return PolicyWeights()
