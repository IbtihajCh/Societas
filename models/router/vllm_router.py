import json
import logging
import time
from typing import Any

import httpx

from models.router.vllm_config import VLLMConfig
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState

logger = logging.getLogger("societas.ai.vllm_router")

_vllm_healthy: bool = True

FALLBACK_RESPONSE = json.dumps({
    "action": "work",
    "feeling": "neutral",
    "reason": "vllm fallback",
})

FALLBACK_GOVERNANCE = {
    "assessment": "Unavailable",
    "recommendation": "Fallback to deterministic governance",
    "watch_items": [],
}


class VLLMRouter:
    def __init__(self, config: VLLMConfig) -> None:
        self._config = config
        url_e2b = config.base_url_e2b or config.base_url
        url_moe = config.base_url_moe_26b or config.base_url
        url_dense = config.base_url_dense_31b or config.base_url
        self._client_e2b = httpx.Client(
            base_url=url_e2b,
            timeout=config.timeout_seconds,
        )
        self._client_moe = httpx.Client(
            base_url=url_moe,
            timeout=config.timeout_seconds,
        )
        self._client_dense = httpx.Client(
            base_url=url_dense,
            timeout=config.timeout_seconds,
        )
        self._call_count = 0

    def _call_vllm(
        self,
        client: httpx.Client,
        prompt: str | list[str],
        api_key: str,
        temperature: float,
        max_tokens: int,
        model: str,
        extract_json: bool = True,
    ) -> list[str]:
        global _vllm_healthy
        headers = {"Authorization": f"Bearer {api_key}"}
        if isinstance(prompt, list):
            messages_list = [[{"role": "user", "content": p}] for p in prompt]
            payload_list: list[dict[str, Any]] = [
                {"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
                for msgs in messages_list
            ]
        else:
            payload_list = [{"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}]

        last_error: Exception | None = None
        text_fallback = "Narrative currently unavailable" if not extract_json else FALLBACK_RESPONSE
        texts: list[str] = []
        for payload in payload_list:
            for attempt in range(self._config.max_retries + 1):
                try:
                    resp = client.post("/chat/completions", headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raw = ""
                    else:
                        raw = choices[0].get("message", {}).get("content", "")
                    _vllm_healthy = True
                    if extract_json:
                        texts.append(self._extract_json(raw))
                    else:
                        texts.append(raw)
                    break
                except Exception as e:
                    last_error = e
                    if attempt < self._config.max_retries:
                        logger.warning("vLLM call failed (attempt %d): %s", attempt + 1, e)
                        time.sleep(2 ** attempt)
                    else:
                        _vllm_healthy = False
                        logger.error("vLLM call failed after %d retries: %s", self._config.max_retries + 1, e)
                        texts.append(text_fallback)

        if not texts:
            count = len(prompt) if isinstance(prompt, list) else 1
            return [text_fallback] * count
        return texts

    def _extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return FALLBACK_RESPONSE
        candidate = text[start:end]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return FALLBACK_RESPONSE

    def agent_decide(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        self._call_count += 1
        results = self._call_vllm(
            self._client_e2b,
            prompt,
            api_key=self._config.api_key_e2b,
            temperature=self._config.temperature_e2b,
            max_tokens=self._config.max_tokens_e2b,
            model=self._config.model_e2b,
        )
        return results[0]

    def agent_decide_batch(
        self, prompts: list[str], agents: list[AgentState], world: SimulationState
    ) -> list[str]:
        self._call_count += len(prompts)
        return self._call_vllm(
            self._client_e2b,
            prompts,
            api_key=self._config.api_key_e2b,
            temperature=self._config.temperature_e2b,
            max_tokens=self._config.max_tokens_e2b,
            model=self._config.model_e2b,
        )

    def moral_reasoning(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        self._call_count += 1
        results = self._call_vllm(
            self._client_moe,
            prompt,
            api_key=self._config.api_key_moe_26b,
            temperature=self._config.temperature_moe,
            max_tokens=self._config.max_tokens_moe,
            model=self._config.model_moe_26b,
        )
        return results[0]

    def moral_reasoning_batch(
        self, prompts: list[str], agents: list[AgentState], world: SimulationState
    ) -> list[str]:
        self._call_count += len(prompts)
        return self._call_vllm(
            self._client_moe,
            prompts,
            api_key=self._config.api_key_moe_26b,
            temperature=self._config.temperature_moe,
            max_tokens=self._config.max_tokens_moe,
            model=self._config.model_moe_26b,
        )

    def governance_advisory(self, world: SimulationState, agents: list[AgentState]) -> dict[str, Any]:
        prompt = self._build_governance_prompt(world, agents)
        results = self._call_vllm(
            self._client_dense,
            prompt,
            api_key=self._config.api_key_dense_31b,
            temperature=self._config.temperature_dense,
            max_tokens=self._config.max_tokens_dense,
            model=self._config.model_dense_31b,
        )
        raw = results[0]
        try:
            data = json.loads(raw)
            if "assessment" in data and "recommendation" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return FALLBACK_GOVERNANCE

    def _build_governance_prompt(self, world: SimulationState, agents: list[AgentState]) -> str:
        living = [a for a in agents if a.is_alive]
        avg_unlust = sum(a.unlust for a in living) / len(living) if living else 0.0
        return (
            f"<|think|>\n"
            f"Assess this society simulation state:\n"
            f"Population: {len(living)}\n"
            f"Avg Unlust: {avg_unlust:.2f}\n"
            f"Crime: {world.crime_rate:.2f}\n"
            f"Unemployment: {world.unemployment_rate:.2f}\n"
            f"Tax: {world.tax_rate:.2f}\n"
            f"Welfare: {'on' if world.welfare_enabled else 'off'}\n"
            f"Food: {world.food_availability:.2f}\n\n"
            f'Output JSON: {{"assessment":"...","recommendation":"...","watch_items":["..."]}}'
        )

    def is_available(self) -> bool:
        """Return whether vLLM calls have been succeeding (updated on each call)."""
        return _vllm_healthy

    def generate_narrative(self, context: str) -> str:
        results = self._call_vllm(
            self._client_dense,
            context,
            api_key=self._config.api_key_dense_31b,
            temperature=0.7,
            max_tokens=256,
            model=self._config.model_dense_31b,
            extract_json=False,
        )
        return results[0]

    def moral_assessment(self, question: str) -> str:
        results = self._call_vllm(
            self._client_moe,
            question,
            api_key=self._config.api_key_moe_26b,
            temperature=0.3,
            max_tokens=256,
            model=self._config.model_moe_26b,
            extract_json=False,
        )
        return results[0]

    def generate_narrative_moe(self, context: str) -> str:
        results = self._call_vllm(
            self._client_moe,
            context,
            api_key=self._config.api_key_moe_26b,
            temperature=0.7,
            max_tokens=512,
            model=self._config.model_moe_26b,
            extract_json=False,
        )
        return results[0]

    def deep_ethics_assessment(self, context: str) -> str:
        results = self._call_vllm(
            self._client_dense,
            context,
            api_key=self._config.api_key_dense_31b,
            temperature=0.4,
            max_tokens=512,
            model=self._config.model_dense_31b,
            extract_json=False,
        )
        return results[0]

    @property
    def call_count(self) -> int:
        return self._call_count
