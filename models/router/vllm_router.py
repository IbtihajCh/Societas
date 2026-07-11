import json
import logging
from typing import Any

import httpx

from models.router.vllm_config import VLLMConfig
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState

logger = logging.getLogger("societas.ai.vllm_router")


_AVAILABILITY_TIMEOUT = 5


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
        self._cached_available: bool | None = None

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
        if not api_key:
            logger.warning("No API key configured for model %s", model)
            return [""] * (len(prompt) if isinstance(prompt, list) else 1)
        headers = {"Authorization": f"Bearer {api_key}"}
        if isinstance(prompt, list):
            messages_list = [[{"role": "user", "content": p}] for p in prompt]
            payload_list: list[dict[str, Any]] = [
                {"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
                for msgs in messages_list
            ]
        else:
            payload_list = [{"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}]

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
                    if extract_json:
                        texts.append(self._extract_json(raw))
                    else:
                        texts.append(raw)
                    break
                except Exception as e:
                    if attempt < self._config.max_retries:
                        logger.warning("vLLM call failed (attempt %d): %s", attempt + 1, e)
                    else:
                        logger.error("vLLM call failed after %d retries: %s", self._config.max_retries + 1, e)
                        texts.append("")

        if not texts:
            count = len(prompt) if isinstance(prompt, list) else 1
            return [""] * count
        return texts

    def _extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return ""
        candidate = text[start:end]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return ""

    def agent_decide(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        self._call_count += 1
        if not self.is_available():
            return ""
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
        if not self.is_available():
            return [""] * len(prompts)
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
        if not self.is_available():
            return ""
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
        if not self.is_available():
            return [""] * len(prompts)
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
        if not self.is_available():
            return {"assessment": "LLM unavailable", "recommendation": "Deterministic governance active", "watch_items": []}
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
        if not raw:
            return {"assessment": "No LLM response", "recommendation": "Deterministic governance active", "watch_items": []}
        try:
            data = json.loads(raw)
            if "assessment" in data and "recommendation" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return {"assessment": "Parse failed", "recommendation": "Deterministic governance active", "watch_items": []}

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
        if self._cached_available is not None:
            return self._cached_available
        api_key = self._config.api_key_dense_31b or self._config.api_key_e2b
        if not api_key:
            self._cached_available = False
            return False
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = self._client_dense.get("/models", headers=headers, timeout=_AVAILABILITY_TIMEOUT)
            self._cached_available = resp.status_code == 200
            return self._cached_available
        except Exception as e:
            logger.info("vLLM server unreachable: %s", e)
            self._cached_available = False
            return False

    def answer_question(self, question: str, state: SimulationState) -> str:
        if not self.is_available():
            return ""
        prompt = (
            f"You are an expert simulation analyst. A society simulation is running.\n"
            f"Current state: population={state.population}, economic_health={state.economic_health:.2f}, "
            f"crime_rate={state.crime_rate:.2f}, protest_intensity={state.protest_intensity:.2f}, "
            f"unemployment_rate={state.unemployment_rate:.2f}, food_availability={state.food_availability:.2f}, "
            f"tax_rate={state.tax_rate:.2f}, welfare_enabled={state.welfare_enabled}, "
            f"avg_unlust={state.unlust:.2f}, morality={state.morality:.2f}.\n\n"
            f"Question: {question}\n\n"
            f"Provide a concise natural-language explanation (2-4 sentences) based on the data above."
        )
        results = self._call_vllm(
            self._client_dense,
            prompt,
            api_key=self._config.api_key_dense_31b,
            temperature=0.4,
            max_tokens=256,
            model=self._config.model_dense_31b,
            extract_json=False,
        )
        return results[0]

    def generate_narrative(self, context: str) -> str:
        if not self.is_available():
            return ""
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
        if not self.is_available():
            return ""
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
        if not self.is_available():
            return ""
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
        if not self.is_available():
            return ""
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
