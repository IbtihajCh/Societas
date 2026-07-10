import time
import logging
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

from models.config import AIConfig

logger = logging.getLogger("societas.ai.amd")

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


class AMDClient:
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        base_url = self.config.amd_base_url
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Content-Type": "application/json"},
            timeout=self.config.request_timeout,
        )

    def chat_completion(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> dict:
        payload = {
            "model": model or self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        last_exc = None
        for attempt in range(self.config.max_retries):
            try:
                resp = self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("no choices in response")
                content = choices[0].get("message", {}).get("content", "")
                return {
                    "content": content,
                    "finish_reason": choices[0].get("finish_reason", ""),
                    "usage": data.get("usage", {}),
                }
            except httpx.HTTPStatusError as e:
                last_exc = e
                logger.warning("AMD API error (attempt %d/%d): %s", attempt + 1, self.config.max_retries, e)
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_exc = e
                logger.warning("AMD connection error (attempt %d/%d): %s", attempt + 1, self.config.max_retries, e)
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
        raise last_exc or RuntimeError("AMD client failed")

    def close(self):
        self._client.close()