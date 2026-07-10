import logging
from typing import Optional

from models.config import AIConfig
from models.client.prompt_loader import PromptLoader
from models.client.amd_client import AMDClient

logger = logging.getLogger("societas.ai.persona")


class PersonaGenerator:
    def __init__(self, config: AIConfig, client: Optional[AMDClient] = None):
        self.config = config
        self._client = client or AMDClient(config)
        self._loader = PromptLoader()

    def generate(self, traits: dict) -> str:
        prompt, frontmatter = self._loader.load("persona-generation.md")
        temperature = frontmatter.get("temperature", 0.7)
        max_tokens = frontmatter.get("max_tokens", 128)

        traits_text = ", ".join(f"{k}={v}" for k, v in traits.items())

        result = self._client.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Generate a persona from these traits: {traits_text}",
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = result.get("content", "").strip()
        return content if content else "A simple simulation agent."
