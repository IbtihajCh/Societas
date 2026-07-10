import json
import logging
from typing import Any

import httpx

from models.router.vllm_config import VLLMConfig
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState

logger = logging.getLogger("societas.ai.vllm_router")

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
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )
        self._call_count = 0

    def _call_vllm(
        self,
        prompt: str | list[str],
        api_key: str,
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> list[str]:
        headers = {"Authorization": f"Bearer {api_key}"}
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if isinstance(prompt, list):
            payload["prompt"] = prompt

        last_error: Exception | None = None
        for attempt in range(self._config.max_retries + 1):
            try:
                resp = self._client.post("/v1/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                texts = []
                for c in choices:
                    raw = c.get("text", "")
                    extracted = self._extract_json(raw)
                    texts.append(extracted)
                return texts
            except Exception as e:
                last_error = e
                if attempt < self._config.max_retries:
                    logger.warning("vLLM call failed (attempt %d): %s", attempt + 1, e)
                else:
                    logger.error("vLLM call failed after %d retries: %s", self._config.max_retries + 1, e)

        count = len(prompt) if isinstance(prompt, list) else 1
        return [FALLBACK_RESPONSE] * count

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
            prompts,
            api_key=self._config.api_key_e2b,
            temperature=self._config.temperature_e2b,
            max_tokens=self._config.max_tokens_e2b,
            model=self._config.model_e2b,
        )

    def moral_reasoning(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        self._call_count += 1
        results = self._call_vllm(
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
            prompts,
            api_key=self._config.api_key_moe_26b,
            temperature=self._config.temperature_moe,
            max_tokens=self._config.max_tokens_moe,
            model=self._config.model_moe_26b,
        )

    def governance_advisory(self, world: SimulationState, agents: list[AgentState]) -> dict[str, Any]:
        prompt = self._build_governance_prompt(world, agents)
        results = self._call_vllm(
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
        try:
            headers = {"Authorization": f"Bearer {self._config.api_key_dense_31b}"}
            resp = self._client.get("/v1/models", headers=headers)
            return resp.status_code == 200
        except Exception:
            return False

    @property
    def call_count(self) -> int:
        return self._call_count
