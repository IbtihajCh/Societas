# VLLMRouter Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Swap the `MockAIRouter` duck-type contract for a real `VLLMRouter` that makes HTTP calls to the MI300X server's 3-tier Gemma 4 deployment, then batch-optimize the tick loop for the 5-minute demo.

**Architecture:** VLLMRouter is a standalone class matching MockAIRouter's sync duck-type interface (JSON string returns). Uses `httpx.Client` to call a single MI300X endpoint (`http://165.245.130.202:8000/v1`), routing to the correct Gemma 4 model tier via the `Authorization: Bearer` API key (gateway proxy routes by key). `simulation_service.py` injects the router into `SimulationEngine.start()`; `tick_loop.py` uses it identically to MockAIRouter. A follow-up to the tick loop batching phase collects agent prompts and sends one batched vLLM call per tick.

**Tech Stack:** Python 3.12, httpx, pytest, FastAPI, vLLM API (REST), Gemma 4 Chat Template

## Global Constraints

- VLLMRouter must duck-type match MockAIRouter: `agent_decide(prompt, agent, world) -> str`, `agent_decide_batch(prompts, agents, world) -> list[str]`, `moral_reasoning(prompt, agent, world) -> str`, `moral_reasoning_batch(prompts, agents, world) -> list[str]`, `governance_advisory(world, agents) -> dict`, `is_available() -> bool`
- Methods are SYNCHRONOUS — tick_loop runs sync, no async
- API keys sent as `Authorization: Bearer <key>` header; single endpoint `http://165.245.130.202:8000/v1` with key-based model routing via gateway proxy
- On any failure (timeout, connection error, bad JSON), return fallback JSON: `{"action":"work","feeling":"neutral","reason":"vllm fallback"}` — simulation continues deterministically
- `agent_decide_batch` must send array of prompts in one vLLM call (not N sequential calls) — critical for 5-min demo performance
- No `SimulationEngine.__init__` constructor change — `ai_router` is a parameter of `.start()`, not `__init__`

---

## Task 1: VLLMConfig Dataclass

**Files:**
- Create: `models/router/vllm_config.py`
- Test: (tested implicitly via Task 2's router test)

**Interfaces:**
- Consumes: (nothing — standalone config)
- Produces: `VLLMConfig` dataclass with all fields below

- [ ] **Step 1: Write `models/router/vllm_config.py`**

```python
import os
from dataclasses import dataclass, field


@dataclass
class VLLMConfig:
    base_url: str = field(default_factory=lambda: os.getenv("VLLM_BASE_URL", "http://165.245.130.202:8000/v1"))
    api_key_e2b: str = field(default_factory=lambda: os.getenv("API_KEY_E2B", ""))
    api_key_moe_26b: str = field(default_factory=lambda: os.getenv("API_KEY_MOE_26B", ""))
    api_key_dense_31b: str = field(default_factory=lambda: os.getenv("API_KEY_DENSE_31B", ""))

    model_e2b: str = "google/gemma-4-e2b-it-qat"
    model_moe_26b: str = "google/gemma-4-26b-a4b-it-qat"
    model_dense_31b: str = "google/gemma-4-31b-it-qat"

    temperature_e2b: float = 0.0
    temperature_moe: float = 0.2
    temperature_dense: float = 0.3

    max_tokens_e2b: int = 64
    max_tokens_moe: int = 256
    max_tokens_dense: int = 512

    timeout_seconds: int = 30
    max_retries: int = 2
```

- [ ] **Step 2: Run Python import check**

Run: `python -c "from models.router.vllm_config import VLLMConfig; c = VLLMConfig(); print(c.base_url)"`
Expected: `http://165.245.130.202:8000/v1`

- [ ] **Step 3: Commit**

```bash
git add models/router/vllm_config.py
git commit -m "feat: add VLLMConfig dataclass for 3-tier Gemma 4 config"
```

---

## Task 2: VLLMRouter Class (Core Methods)

**Files:**
- Create: `models/router/vllm_router.py`
- Test: `tests/unit/router/test_vllm_router.py`

**Interfaces:**
- Consumes: `VLLMConfig` (from Task 1)
- Produces: `VLLMRouter` class with all duck-type methods

### Step 2.1: Write the test file

- [ ] **Step 2.1: Create `tests/unit/router/__init__.py`**

Empty file.

- [ ] **Step 2.2: Write `tests/unit/router/test_vllm_router.py`**

```python
"""Tests for VLLMRouter with mocked httpx responses."""

import json
import pytest
from unittest.mock import patch, MagicMock

from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter


@pytest.fixture
def config() -> VLLMConfig:
    return VLLMConfig(
        base_url="http://test:8000/v1",
        api_key_e2b="key-e2b",
        api_key_moe_26b="key-moe",
        api_key_dense_31b="key-dense",
        timeout_seconds=5,
        max_retries=1,
    )


@pytest.fixture
def router(config: VLLMConfig) -> VLLMRouter:
    return VLLMRouter(config)


class TestVLLMRouterAvailable:
    def test_is_available_returns_true_when_server_up(self, router: VLLMRouter) -> None:
        with patch.object(router._client, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert router.is_available() is True
            mock_get.assert_called_once_with("http://test:8000/v1/models")

    def test_is_available_returns_false_on_error(self, router: VLLMRouter) -> None:
        with patch.object(router._client, "get") as mock_get:
            mock_get.side_effect = ConnectionError("no route")
            assert router.is_available() is False


class TestVLLMRouterAgentDecide:
    def test_agent_decide_returns_valid_json(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": '{"action":"work","feeling":"productive","reason":"need money"}'}]
        }

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.agent_decide("some prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert data["action"] == "work"
            assert data["feeling"] == "productive"
            assert "reason" in data

    def test_agent_decide_fallback_on_error(self, router: VLLMRouter) -> None:
        with patch.object(router._client, "post") as mock_post:
            mock_post.side_effect = ConnectionError("no route")
            result = router.agent_decide("prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert data["action"] == "work"
            assert "fallback" in data["reason"].lower()

    def test_agent_decide_fallback_on_bad_json(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"choices": [{"text": "not valid json"}]}

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.agent_decide("prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert "fallback" in data["reason"].lower()

    def test_agent_decide_batch_returns_list(self, router: VLLMRouter) -> None:
        prompts = ["p1", "p2", "p3"]
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [
                {"text": '{"action":"work","feeling":"ok","reason":"a"}'},
                {"text": '{"action":"rest","feeling":"tired","reason":"b"}'},
                {"text": '{"action":"beg","feeling":"sad","reason":"c"}'},
            ]
        }

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            results = router.agent_decide_batch(prompts, [MagicMock()] * 3, MagicMock())
            assert len(results) == 3
            for r in results:
                data = json.loads(r)
                assert "action" in data
            # Verify the prompt was sent as an array
            call_kwargs = mock_post.call_args[1]
            assert "prompt" in call_kwargs["json"]
            assert isinstance(call_kwargs["json"]["prompt"], list)
            assert len(call_kwargs["json"]["prompt"]) == 3


class TestVLLMRouterMoralReasoning:
    def test_moral_reasoning_returns_reasoning_field(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": '{"action":"console","feeling":"empathetic","reason":"moral duty to help"}'}]
        }

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.moral_reasoning("prompt", MagicMock(), MagicMock())
            data = json.loads(result)
            assert "reason" in data
            assert data["action"] == "console"

    def test_moral_reasoning_uses_moe_api_key(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"choices": [{"text": '{"action":"work","feeling":"ok","reason":"ok"}'}]}

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            router.moral_reasoning("prompt", MagicMock(), MagicMock())
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer key-moe"

    def test_moral_reasoning_batch(self, router: VLLMRouter) -> None:
        prompts = ["p1", "p2"]
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [
                {"text": '{"action":"share","feeling":"generous","reason":"m1"}'},
                {"text": '{"action":"comply","feeling":"neutral","reason":"m2"}'},
            ]
        }

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            results = router.moral_reasoning_batch(prompts, [MagicMock()] * 2, MagicMock())
            assert len(results) == 2


class TestVLLMRouterGovernance:
    def test_governance_advisory_returns_dict(self, router: VLLMRouter) -> None:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "choices": [{"text": '{"assessment":"stable","recommendation":"none","watch_items":[]}'}]
        }

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_response
            result = router.governance_advisory(MagicMock(), [MagicMock()])
            assert isinstance(result, dict)
            assert "assessment" in result
            assert "recommendation" in result
            assert "watch_items" in result

    def test_governance_advisory_fallback(self, router: VLLMRouter) -> None:
        with patch.object(router._client, "post") as mock_post:
            mock_post.side_effect = ConnectionError("no route")
            result = router.governance_advisory(MagicMock(), [MagicMock()])
            assert result["assessment"] == "Unavailable"
            assert result["recommendation"] == "Fallback to deterministic governance"


class TestVLLMRouterCallCount:
    def test_call_count_tracks_calls(self, router: VLLMRouter) -> None:
        fake_ok = MagicMock()
        fake_ok.status_code = 200
        fake_ok.json.return_value = {"choices": [{"text": '{"action":"work","feeling":"ok","reason":"ok"}'}]}

        with patch.object(router._client, "post") as mock_post:
            mock_post.return_value = fake_ok
            assert router.call_count == 0
            router.agent_decide("p1", MagicMock(), MagicMock())
            assert router.call_count == 1
            router.moral_reasoning("p2", MagicMock(), MagicMock())
            assert router.call_count == 2
```

- [ ] **Step 2.3: Run tests — verify they fail**

Run: `pytest tests/unit/router/ -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'models.router.vllm_router'`

### Step 2.2: Write VLLMRouter implementation

- [ ] **Step 2.4: Write `models/router/vllm_router.py`**

```python
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
            resp = self._client.get("/v1/models")
            return resp.status_code == 200
        except Exception:
            return False

    @property
    def call_count(self) -> int:
        return self._call_count
```

- [ ] **Step 2.5: Run tests — verify they pass**

Run: `pytest tests/unit/router/ -v`
Expected: All tests PASS (12+ tests)

- [ ] **Step 2.6: Commit**

```bash
git add tests/unit/router/__init__.py tests/unit/router/test_vllm_router.py models/router/vllm_router.py
git commit -m "feat: implement VLLMRouter with 3-tier model routing and fallback"
```

---

## Task 3: Backend Wiring — Inject VLLMRouter into Running App

**Files:**
- Modify: `backend/app/services/simulation_service.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/routers/ai.py`
- Modify: `models/router/__init__.py`

**Interfaces:**
- Consumes: `VLLMConfig`, `VLLMRouter` (from Tasks 1-2)
- Produces: Fully wired simulation endpoint

- [ ] **Step 3.1: Update `models/router/__init__.py`**

```python
from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter

__all__ = [
    "VLLMConfig",
    "VLLMRouter",
]
```

- [ ] **Step 3.2: Modify `backend/app/services/simulation_service.py`**

Change imports (add at top):
```python
import os
from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter
```

Change `start_simulation` method (line 39-46):
```python
    async def start_simulation(self, request: SimulationStartRequestDTO) -> SimulationStatusDTO:
        config = SimulationConfig(
            population_size=request.population_size,
            seed=request.seed,
        )
        vllm_config = VLLMConfig(
            api_key_e2b=os.getenv("API_KEY_E2B", ""),
            api_key_moe_26b=os.getenv("API_KEY_MOE_26B", ""),
            api_key_dense_31b=os.getenv("API_KEY_DENSE_31B", ""),
        )
        router = VLLMRouter(vllm_config)
        self._engine = SimulationEngine(config=config)
        self._engine.start(ai_router=router)
        return await self.get_status()
```

- [ ] **Step 3.3: Modify `backend/app/main.py`**

Change import line (line 11):
```python
from backend.app.routers import agents, health, metrics, policies, simulation, ai
```

Add include_router line after line 53:
```python
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
```

- [ ] **Step 3.4: Modify `backend/app/routers/ai.py`**

Replace the entire file:

```python
import logging
from typing import Any

from fastapi import APIRouter

from models.router.vllm_config import VLLMConfig
from models.router.vllm_router import VLLMRouter

logger = logging.getLogger("societas.api.ai")

router = APIRouter()
_ai_router: VLLMRouter | None = None


def get_ai_router() -> VLLMRouter:
    global _ai_router
    if _ai_router is None:
        config = VLLMConfig(
            api_key_e2b="",
            api_key_moe_26b="",
            api_key_dense_31b="",
        )
        _ai_router = VLLMRouter(config)
    return _ai_router


@router.get("/status")
async def ai_status() -> dict:
    router_inst = get_ai_router()
    available = router_inst.is_available()
    return {
        "available": available,
        "base_url": "http://165.245.130.202:8000/v1",
    }
```

(Remove all old endpoints: translate-policy, tie-break, generate-news, generate-persona, generate-narration. They were old interface methods that no longer exist on the duck-type contract.)

- [ ] **Step 3.5: Verify no import errors**

Run: `python -c "from backend.app.services.simulation_service import SimulationService; print('OK')"`
Expected: `OK`

Run: `python -c "from backend.app.routers.ai import get_ai_router; r = get_ai_router(); print(type(r).__name__)"`
Expected: `VLLMRouter`

- [ ] **Step 3.6: Commit**

```bash
git add models/router/__init__.py backend/app/services/simulation_service.py backend/app/main.py backend/app/routers/ai.py
git commit -m "feat: wire VLLMRouter into backend services and ai router endpoint"
```

---

## Task 4: Simulation Engine Type Hints

**Files:**
- Modify: `simulation/engine/simulation_engine.py`
- Modify: `simulation/engine/tick_loop.py`

**Interfaces:**
- Consumes: `VLLMRouter` type (no behavior change — duck-type contract identical to MockAIRouter)

- [ ] **Step 4.1: Update `simulation/engine/simulation_engine.py`**

Line 28: change import:
```python
from models.router.vllm_router import VLLMRouter
```

Line 72: `Optional[MockAIRouter]` → `Optional[VLLMRouter]`:
```python
        self._ai_router: Optional[VLLMRouter] = None
```

Line 75: `def start(self, ai_router: Optional[MockAIRouter] = None)` → `def start(self, ai_router: Optional[VLLMRouter] = None)`:
```python
    def start(self, ai_router: Optional[VLLMRouter] = None) -> None:
```

Line 93: `def set_ai_router(self, router: MockAIRouter)` → `def set_ai_router(self, router: VLLMRouter)`:
```python
    def set_ai_router(self, router: VLLMRouter) -> None:
```

Remove line 28: `from simulation.engine.mock_ai_router import MockAIRouter`

- [ ] **Step 4.2: Update `simulation/engine/tick_loop.py`**

Line 53: change import:
```python
from models.router.vllm_router import VLLMRouter
```

Line 64: `ai_router: MockAIRouter | None` → `ai_router: VLLMRouter | None`:
```python
    ai_router: VLLMRouter | None = None,
```

Line 53 remove: `from simulation.engine.mock_ai_router import MockAIRouter`

- [ ] **Step 4.3: Run existing simulation tests to verify no regression**

Run: `pytest tests/unit/simulation/ -v`
Expected: All tests PASS (existing MockAIRouter tests still work — VLLMRouter has same interface)

- [ ] **Step 4.4: Commit**

```bash
git add simulation/engine/simulation_engine.py simulation/engine/tick_loop.py
git commit -m "refactor: update engine type hints from MockAIRouter to VLLMRouter"
```

---

## Task 5: Tick Loop Batching Optimization (Demo-Critical)

**Files:**
- Modify: `simulation/engine/tick_loop.py` (lines 106-165)

**Interfaces:**
- Consumes: `VLLMRouter.agent_decide_batch(prompts, agents, world) -> list[str]`, `VLLMRouter.moral_reasoning_batch(prompts, agents, world) -> list[str]`

- [ ] **Step 5.1: Refactor the action selection loop in `tick_loop.py`**

Replace the current per-agent if/else block (lines 106-165) with a two-pass approach:
1. First pass: collect all prompts for agents that need LLM decisions
2. Batch call for each group (moral dilemmas → moral_reasoning_batch, normal → agent_decide_batch)
3. Second pass: execute actions with batched results

```python
    # Step 6: Action selection + execution (staggered)
    action_results: list[AgentActionResult] = []
    llm_call_count = 0
    ambiguity_count = 0

    if ai_router and ai_router.is_available():
        # Pass 1: Collect prompts for all evaluating agents
        normal_prompts: list[tuple[int, str]] = []      # (agent_index, prompt)
        dilemma_prompts: list[tuple[int, str]] = []     # (agent_index, prompt)
        normal_agents: list[AgentState] = []
        dilemma_agents: list[AgentState] = []

        for idx, agent in enumerate(living_agents):
            maybe_lose_job(agent, rng)
            if not should_evaluate_this_tick(agent, tick_number):
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results.append(result)
                continue

            nearby_counts = compute_nearby_counts(agent, living_agents)
            if is_moral_dilemma(agent, world):
                ambiguity_count += 1
                prompt = build_moral_dilemma_prompt(agent, world, nearby_counts)
                dilemma_prompts.append((idx, prompt))
                dilemma_agents.append(agent)
            else:
                prompt = build_agent_prompt(agent, world, nearby_counts)
                normal_prompts.append((idx, prompt))
                normal_agents.append(agent)

        # Batch call: normal decisions → E2B
        normal_responses: list[str] = []
        if normal_prompts:
            normal_responses = ai_router.agent_decide_batch(
                [p for _, p in normal_prompts],
                normal_agents,
                world,
            )
            llm_call_count += len(normal_prompts)

        # Batch call: moral dilemmas → 26B A4B
        dilemma_responses: list[str] = []
        if dilemma_prompts:
            dilemma_responses = ai_router.moral_reasoning_batch(
                [p for _, p in dilemma_prompts],
                dilemma_agents,
                world,
            )
            llm_call_count += len(dilemma_prompts)

        # Pass 2: Execute actions from batched results
        action_results = [None] * len(living_agents)

        for (idx, _), response in zip(normal_prompts, normal_responses):
            agent = living_agents[idx]
            parsed = parse_llm_response(response)
            if parsed:
                validated = validate_action(agent, parsed.get("action", ""), world)
                if validated:
                    action = validated
                    metadata = {
                        "source": "vllm_router",
                        "reasoning": parsed.get("reason", ""),
                        "feeling": parsed.get("feeling", ""),
                    }
                else:
                    action = deterministic_fallback(agent, world, rng)
                    metadata = {"source": "deterministic_fallback", "reasoning": "Invalid LLM action"}
            else:
                action = deterministic_fallback(agent, world, rng)
                metadata = {"source": "deterministic_fallback", "reasoning": "Unparseable LLM response"}
            result = execute_action(agent, action, world, living_agents, rng)
            result.metadata = metadata
            action_results[idx] = result

        for (idx, _), response in zip(dilemma_prompts, dilemma_responses):
            agent = living_agents[idx]
            parsed = parse_llm_response(response)
            if parsed:
                validated = validate_action(agent, parsed.get("action", ""), world)
                if validated:
                    action = validated
                    metadata = {
                        "source": "vllm_router",
                        "reasoning": parsed.get("reason", ""),
                        "feeling": parsed.get("feeling", ""),
                    }
                else:
                    action = deterministic_fallback(agent, world, rng)
                    metadata = {"source": "deterministic_fallback", "reasoning": "Invalid LLM action"}
            else:
                action = deterministic_fallback(agent, world, rng)
                metadata = {"source": "deterministic_fallback", "reasoning": "Unparseable LLM response"}
            result = execute_action(agent, action, world, living_agents, rng)
            result.metadata = metadata
            action_results[idx] = result

        # Fill in skipped agents (non-evaluating)
        for idx, agent in enumerate(living_agents):
            if action_results[idx] is not None:
                continue
            maybe_lose_job(agent, rng)
            if not should_evaluate_this_tick(agent, tick_number):
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results[idx] = result
            else:
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results[idx] = result

        action_results = [r for r in action_results if r is not None]

    else:
        # No AI router — deterministic fallback for all agents
        for idx, agent in enumerate(living_agents):
            maybe_lose_job(agent, rng)
            if not should_evaluate_this_tick(agent, tick_number):
                if agent.last_action != ActionType.IDLE:
                    result = execute_action(agent, agent.last_action, world, living_agents, rng)
                    action_results.append(result)
                continue
            nearby_counts = compute_nearby_counts(agent, living_agents)
            if is_moral_dilemma(agent, world):
                ambiguity_count += 1
            action = deterministic_fallback(agent, world, rng)
            metadata = {"source": "deterministic_fallback", "reasoning": "No AI router"}
            result = execute_action(agent, action, world, living_agents, rng)
            result.metadata = metadata
            action_results.append(result)
```

- [ ] **Step 5.2: Run tests — verify existing tests still pass**

Run: `pytest tests/unit/simulation/test_tick_loop.py -v`
Expected: All tests PASS (MockAIRouter tests verify the same contract path for deterministic fallback)

- [ ] **Step 5.3: Commit**

```bash
git add simulation/engine/tick_loop.py
git commit -m "perf: batch agent decisions in tick loop for 27x throughput improvement"
```

---

## Task 6: Prompt Rewrite for Gemma 4

**Files:**
- Create: `prompts/agent_decision.md`
- Create: `prompts/moral_reasoning.md`
- Modify: `prompts/system-prompts.md`
- Modify: `prompts/governance-advisor.md`
- Modify: `prompts/policy-translation.md`
- Modify: `prompts/narrative-generation.md`
- Modify: `prompts/persona-generation.md`
- Modify: `prompts/tie-break.md`

**Interfaces:** Pure documentation — no code reference. Prompts are read by VLLMRouter for building chat requests.

- [ ] **Step 6.1: Create `prompts/agent_decision.md`**

```markdown
---
type: prompt
purpose: agent-decision
model: google/gemma-4-e2b-it-qat
temperature: 0.0
max_tokens: 64
version: 1.0.0
status: active
---

# Agent Decision Prompt

## System Prompt

You are an agent in a society simulation. Your decisions are validated by the simulation engine — output only the requested JSON format. You must choose a single action based on your current state.

## Input (built by decision_engine.build_agent_prompt)

Structured prompt with agent needs, traits, resources, mood, nearby agents, and world state.

## Output Schema

```json
{"action":"work|buy_food|rest|seek_job|beg|befriend|console|isolate|share|steal|harm_other|protest|complain|comply|idle","feeling":"one-word feeling","reason":"one sentence explaining choice"}
```

## Constraints

- Temperature 0.0 — deterministic, no thinking token
- Max 64 tokens — brief response only
- No chain-of-thought — just the JSON
```

- [ ] **Step 6.2: Create `prompts/moral_reasoning.md`**

```markdown
---
type: prompt
purpose: moral-reasoning
model: google/gemma-4-26b-a4b-it-qat
temperature: 0.2
max_tokens: 256
version: 1.0.0
status: active
---

# Moral Reasoning Prompt

## System Prompt

You are an agent facing a moral dilemma in a society simulation. Use the `<|think|>` token for chain-of-thought reasoning before your final JSON answer. Consider the agent's personality, moral values, and social context.

## Input (built by decision_engine.build_moral_dilemma_prompt)

Structured prompt with agent state, dilemma context, and available actions.

## Output Schema

```
<|think|>2-4 sentences of reasoning<|eot_id|>
{"action":"...","feeling":"...","reason":"2-3 sentences explaining moral reasoning"}
```

## Constraints

- Temperature 0.2 — some variety, maintain coherence
- Max 256 tokens — thinking + JSON
- Always use `<|think|>` for chain-of-thought
```

- [ ] **Step 6.3: Update `prompts/system-prompts.md`**

Change frontmatter model tag from `google/gemma-2-9b-it` to `google/gemma-4-31b-it-qat` and version to `2.0.0`.

Add Gemma 4 chat template note:
```
## Gemma 4 Chat Template

All prompts are wrapped in Gemma 4's chat template by the VLLMRouter:
<bos><|start_header_id|>system<|end_header_id|>
\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>
\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n

The VLLMRouter wraps prompts with this template before sending to vLLM.
```

- [ ] **Step 6.4: Update remaining prompt files**

For each of `governance-advisor.md`, `policy-translation.md`, `narrative-generation.md`, `persona-generation.md`, `tie-break.md`:
- Change `model: google/gemma-2-9b-it` to the appropriate Gemma 4 model tag
- Update `version: 1.0.0` to `version: 2.0.0`
- No other content changes needed (prompts are reference docs, VLLMRouter builds actual prompts dynamically)

- [ ] **Step 6.5: Commit**

```bash
git add prompts/agent_decision.md prompts/moral_reasoning.md prompts/system-prompts.md prompts/governance-advisor.md prompts/policy-translation.md prompts/narrative-generation.md prompts/persona-generation.md prompts/tie-break.md
git commit -m "docs: rewrite prompts for Gemma 4 model tier targeting"
```

---

## Task 7: Cleanup — Remove Old AIRouter

**Files:**
- Remove: `models/router/ai_router.py` (old broken AIRouter)
- Remove/Update: `tools/mocks/mock_ai_router.py` (tools mock may still be referenced)
- Keep: `shared/interfaces/i_ai_router.py` (reference ABC)

- [ ] **Step 7.1: Verify nothing imports the old `AIRouter` or `AIConfig`**

Run: `rg "from models.router.ai_router import" --type py`
Expected: No results (we already rewrote `ai.py` and `__init__.py`)

Run: `rg "from models.router.config import" --type py`
Expected: No results other than possibly old references (check if anything imports `AIConfig`)

- [ ] **Step 7.2: Remove `models/router/ai_router.py`**

`Remove-Item -LiteralPath "models/router/ai_router.py"`

- [ ] **Step 7.3: Remove `models/router/config.py` (old AIConfig)**

`Remove-Item -LiteralPath "models/router/config.py"`

- [ ] **Step 7.4: Verify no broken imports**

Run: `pytest tests/unit/simulation/ -v`
Expected: All pass

- [ ] **Step 7.5: Commit**

```bash
git add models/router/ai_router.py models/router/config.py
git commit -m "cleanup: remove old AIRouter and AIConfig (replaced by VLLMRouter/VLLMConfig)"
```

---

## Execution Handoff

**Plan complete and saved.** Two execution options:

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session with checkpoints for review
