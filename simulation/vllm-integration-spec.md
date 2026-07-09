# vLLM Integration Specification — For AI Systems Engineer

**Date:** 2026-07-09
**From:** Simulation Engineer
**To:** AI Systems Engineer
**Status:** Spec — awaiting implementation

---

## What We Need

The simulation engine has a `MockAIRouter` that implements `IAIRouter`. We need a `VLLMRouter` that makes real HTTP calls to vLLM servers running Gemma 4 models. The simulation engine calls the router; the router calls vLLM; vLLM returns JSON; the simulation executes the action.

**You implement:** `models/router/vllm_router.py` — a class implementing `IAIRouter` that uses `httpx.AsyncClient` to call vLLM endpoints.

**You DO NOT implement:** Any simulation logic, decision-making, or action execution. The simulation handles all of that.

---

## Three Models, Three Endpoints

```
┌─────────────────────────────────────────────────────────────┐
│  AMD GPU (198GB VRAM)                                       │
│                                                             │
│  vLLM Instance 1 (port 8001)     vLLM Instance 2 (port 8002)│
│  Gemma 4 E2B IT QAT              Gemma 4 26B A4B IT QAT     │
│  ~1GB VRAM, 3 replicas           ~16.5GB VRAM               │
│  Agent brains (27 calls/tick)    Moral reasoning (1-2/tick) │
│  temp=0.0, no thinking            temp=0.2, thinking ON     │
│  max_tokens=64                    max_tokens=256            │
│                                                             │
│               vLLM Instance 3 (port 8003)                  │
│               Gemma 4 31B IT QAT                           │
│               ~20.3GB VRAM                                  │
│               Governance advisor + Policy translation      │
│               temp=0.3, thinking ON                         │
│               max_tokens=512                                │
└─────────────────────────────────────────────────────────────┘
```

Total VRAM: ~40GB of 198GB. Room to scale to 500+ agents.

---

## Interface Contract

The simulation calls these methods on the router:

```python
class IAIRouter(ABC):
    @abstractmethod
    async def agent_decide(self, prompt: str) -> dict:
        """E2B: Parse agent state prompt, return {action, feeling, reason}."""

    @abstractmethod
    async def agent_decide_batch(self, prompts: list[str]) -> list[dict]:
        """E2B: Batch version of agent_decide for staggered calls."""

    @abstractmethod
    async def moral_reasoning(self, prompt: str) -> dict:
        """26B A4B: Resolve moral dilemma, return {action, reasoning}."""

    @abstractmethod
    async def moral_reasoning_batch(self, prompts: list[str]) -> list[dict]:
        """26B A4B: Batch version of moral_reasoning."""

    @abstractmethod
    async def governance_advisory(self, prompt: str) -> dict:
        """31B: Analyze world state, return {assessment, recommendation, watch_items}."""

    @abstractmethod
    async def translate_policy(self, prompt: str) -> dict:
        """31B: Translate policy text to ImpactDeltas + PolicyWeights."""

    @abstractmethod
    async def generate_news(self, prompt: str) -> dict:
        """31B: Generate news article from events."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if vLLM servers are reachable."""
```

---

## Prompt Schemas

### E2B Agent Brain (port 8001)

**Input prompt** (~200 tokens, built by `decision_engine.build_agent_prompt()`):
```
You are agent {id}. Your state:
Needs: food={0.30} water={0.45} sleep={0.62} safety={0.81} social={0.55} ...
Traits: morality={0.52} creativity={0.73} anger_tendency={0.31} ...
Money: £{340}. Employed: yes. Job: mechanic.
Mood: NORMAL. Happiness: {0.68}. Unlust: {0.12}. Health: {0.95}.
Reputation: {0.45}. Trust in govt: {0.50}. Crimes: 0. Good acts: 2.
Nearby: {12} agents, {3} protesting, {2} needy, {1} sad, {4} generous.
World: tax={0.20} welfare={off} food_avail={0.85}.

Choose ONE action. Reply JSON: {"action":"work","feeling":"content","reason":"earning money"}
Actions: work buy_food rest seek_job beg befriend console isolate share steal harm_other protest complain comply idle
```

**Expected output** (JSON, max 64 tokens):
```json
{"action":"buy_food","feeling":"hungry","reason":"food is low at 0.30"}
```

**vLLM call:**
```python
response = await client.post(
    f"http://localhost:8001/v1/completions",
    json={
        "model": "google/gemma-4-e2b-it-qat",
        "prompt": prompt,
        "temperature": 0.0,
        "max_tokens": 64,
        "stop": ["\n"]
    }
)
```

### 26B A4B Moral Reasoning (port 8002)

**Input prompt** (with thinking mode, built by `decision_engine.build_moral_dilemma_prompt()`):
```
<|think|>
You are agent {id} facing a moral dilemma.
Context: {richer_state_description}
Your morality: {0.52}. Unlust: {0.65}. Emotion: ANGRY.
Options and consequences:
- steal: gain £18-60, victim loses money+safety, your reputation -0.06
- beg: gain £0-5, no harm, reputation -0.02
- work: earn £45, no harm, but food may drop further
What should a person with your morality do?

Output JSON: {"action":"...","reasoning":"2-3 sentences explaining your moral reasoning"}
<|channel>thought
```

**Expected output:**
```
<|channel>thought
I have moderate morality (0.52) and high unlust (0.65). My anger makes me want to act out, but stealing would harm an innocent person. With morality above 0.5, I should resist the urge to steal. Working is the moral choice, even though I'm angry.
<channel|>
{"action":"work","reasoning":"Despite anger and high unlust, my morality (0.52) prevents me from stealing. I choose to work honestly."}
```

**vLLM call:**
```python
response = await client.post(
    f"http://localhost:8002/v1/completions",
    json={
        "model": "google/gemma-4-26b-a4b-it-qat",
        "prompt": prompt,
        "temperature": 0.2,
        "max_tokens": 256,
    }
)
```

### 31B Governance Advisor (port 8003)

**Input prompt:**
```
<|think|>
You are a governance advisor monitoring a society simulation.
World state at tick {150}:
  Population: {78} alive (2 deaths this period)
  Avg happiness: {0.62} (declining)
  Avg unlust: {0.35} (rising)
  Unemployment: {12%}
  Crime rate: {0.08} (rising)
  Protest intensity: {0.15}
  Tax rate: {0.20}, Welfare: enabled £8/tick
  Food availability: {0.85}
  Active policies: [{list}]
  Recent events: {summary}

Assess stability and recommend action.
Output JSON:
{"assessment":"stable|concerning|critical","recommendation":"...","watch_items":["..."]}
<|channel>thought
```

**vLLM call:**
```python
response = await client.post(
    f"http://localhost:8003/v1/completions",
    json={
        "model": "google/gemma-4-31b-it-qat",
        "prompt": prompt,
        "temperature": 0.3,
        "max_tokens": 512,
    }
)
```

### 31B Policy Translation (port 8003)

**Input prompt:**
```
<|think|>
Translate this policy into simulation impact deltas.

Policy: "Increase income tax by 10% and use revenue for food subsidies for poor families"

Current weights: economic_freedom={0.5} social_welfare={0.5} ...

Output JSON:
{
  "weights": {"economic_freedom": -0.2, "social_welfare": +0.3, ...},
  "impact_deltas": {
    "POOR": {"money_delta": -5, "food_delta": +0.10, "safety_delta": 0, "social_delta": 0, "anger_spike": 0.05},
    "MIDDLE": {"money_delta": -15, "food_delta": +0.05, ...},
    "RICH": {"money_delta": -50, "food_delta": 0, ...}
  },
  "world_changes": {"new_tax_rate": 0.30, "food_event": +0.05},
  "reasoning": "..."
}
<|channel>thought
```

---

## Batching Strategy

The simulation uses **staggered re-evaluation**: 1/3 of agents re-evaluate each tick (agent_id % 3). This means:

- 80 agents → 27 calls/tick to E2B
- 150 agents → 50 calls/tick
- 500 agents → 167 calls/tick

**Batch these into a single vLLM call** using the `prompts` array:

```python
# Instead of 27 individual calls:
response = await client.post(
    "http://localhost:8001/v1/completions",
    json={
        "model": "google/gemma-4-e2b-it-qat",
        "prompt": [prompt1, prompt2, prompt3, ...],  # array of prompts
        "temperature": 0.0,
        "max_tokens": 64,
    }
)
# Returns array of completions
```

This is critical for performance — 27 sequential calls would take ~27 seconds, but 1 batched call takes ~1 second.

---

## Fireworks AI Fallback

If vLLM is unavailable (GPU not ready, model loading), fall back to Fireworks AI API:

```python
# Fireworks endpoint
FIREWORKS_MODELS = {
    "e2b": "accounts/fireworks/models/gemma-4-e2b-it",
    "26b": "accounts/fireworks/models/gemma-4-26b-a4b-it",
    "31b": "accounts/fireworks/models/gemma-4-31b-it",
}
# Base URL: https://api.fireworks.ai/inference/v1
# Auth: Bearer $FIREWORKS_API_KEY
```

---

## What We Need From You

1. **`models/router/vllm_router.py`** — implements `IAIRouter` with real HTTP calls
2. **Docker Compose** for 3 vLLM instances (ports 8001/8002/8003)
3. **Config** for model names, endpoints, fallback to Fireworks
4. **Health check** — `is_available()` pings all 3 endpoints
5. **Error handling** — on vLLM failure, return `None` so the simulation falls back to deterministic mode
6. **Batching** — `agent_decide_batch()` and `moral_reasoning_batch()` must use vLLM's batch prompt feature

---

## What We Will Do (Simulation Side)

The simulation engine already:
- Builds prompts via `decision_engine.build_agent_prompt()` and `build_moral_dilemma_prompt()`
- Parses JSON responses via `decision_engine.parse_llm_response()`
- Validates actions via `decision_engine.validate_action()`
- Falls back to `deterministic_fallback()` when the router returns invalid/None
- Tracks `ai_calls`, `ambiguity_count`, `fallback_count` in TickResult

We are improving the deterministic fallback to produce more interesting behavior even without LLM (see separate plan). But the LLM is what makes SOCIETAS special — it's the "entirety of society on a single GPU" pitch.
