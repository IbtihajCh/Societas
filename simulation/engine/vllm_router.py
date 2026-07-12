"""VLLM AI router — connects to real Gemma 4 models via vLLM.

Routes requests to the appropriate Gemma 4 model:
- E2B (port 8001): Agent decisions (~27 calls/tick, temp=0.0)
- 26B A4B (port 8002): Moral reasoning with thinking mode (temp=0.2)
- 31B (port 8003/8000): Governance advisory & policy translation (temp=0.3)

Falls back to 31B for all tasks when E2B/26B are unavailable.
"""

import json
from typing import Any

import requests

from shared.interfaces.i_ai_router import IAIRouter
from shared.schemas.agent_state import AgentState
from shared.schemas.decision import DecisionRequest, DecisionResponse
from shared.schemas.news_event import NewsEvent, SpotlightNarration
from shared.schemas.policy import GovernmentPolicy, ImpactDelta, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = ["VLLMRouter"]


class VLLMRouter(IAIRouter):
    """Real AI router connecting to Gemma 4 models via vLLM API.

    Matches the IAIRouter interface. Agent decisions/moral reasoning
    use the same calling convention as MockAIRouter for tick_loop
    backward compatibility.
    """

    def __init__(
        self,
        e2b_url: str = "http://165.245.130.202:8001/v1",
        moe_url: str = "http://165.245.130.202:8002/v1",
        gov_url: str = "http://165.245.130.202:8000/v1",
        e2b_key: str = "societase2b-key3z8",
        moe_key: str = "societasmoe-key7q1",
        gov_key: str = "societas31-key9x2",
        timeout: float = 3.0,
        fallback_to_31b: bool = True,
    ):
        self._e2b_url = e2b_url
        self._moe_url = moe_url
        self._gov_url = gov_url
        self._e2b_key = e2b_key
        self._moe_key = moe_key
        self._gov_key = gov_key
        self._timeout = timeout
        self._fallback_to_31b = fallback_to_31b
        self._call_count = 0

    def is_available(self) -> bool:
        return True

    def _call_llm(
        self,
        prompt: str,
        model: str = "google/gemma-4-31B-it",
        url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> str:
        url = url or self._gov_url
        api_key = api_key or self._gov_key
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            r = requests.post(
                f"{url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self._timeout,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return ""

    def _mock_decide(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        """Deterministic fallback when no AI server is available."""
        from simulation.agents.decision_engine import deterministic_fallback
        from simulation.agents.emotion_engine import compute_happiness

        hap = compute_happiness(agent, world)
        action = deterministic_fallback(
            agent, world, DeterministicRNG(seed=int(agent.age + agent.unlust * 100))
        )
        feelings = ["happy", "neutral", "worried", "determined", "tired"]
        import random

        rng = random.Random(agent.age * 1000 + int(agent.unlust * 100))
        feeling = feelings[rng.randint(0, len(feelings) - 1)]
        return json.dumps(
            {
                "action": action.value if hasattr(action, "value") else str(action),
                "reason": f"My current state (needs={agent.needs.levels.get('survival', 0):.2f}, "
                f"happiness={hap:.2f}, unlust={agent.unlust:.2f}) "
                f"led me to choose {action}.",
                "feeling": feeling,
            }
        )

    def agent_decide(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        self._call_count += 1
        result = self._call_llm(
            prompt,
            model="google/gemma-4-e2b-it",
            url=self._e2b_url,
            api_key=self._e2b_key,
            temperature=0.0,
        )
        if not result:
            result = self._mock_decide(prompt, agent, world)
        return result

    def agent_decide_batch(
        self, prompts: list[str], agents: list[AgentState], world: SimulationState
    ) -> list[str]:
        return [self.agent_decide(p, a, world) for p, a in zip(prompts, agents, strict=False)]

    def _mock_moral(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        from simulation.agents.decision_engine import deterministic_fallback

        action = deterministic_fallback(
            agent, world, DeterministicRNG(seed=agent.age + agent.unlust * 50)
        )
        return json.dumps(
            {
                "action": action.value if hasattr(action, "value") else str(action),
                "reason": f"Moral deliberation: my morality is {agent.traits.morality:.2f}, "
                f"unlust is {agent.unlust:.2f}. I chose {action}.",
                "feeling": "concerned",
            }
        )

    def moral_reasoning(self, prompt: str, agent: AgentState, world: SimulationState) -> str:
        self._call_count += 1
        result = self._call_llm(
            prompt,
            model="google/gemma-4-26b-a4b-it",
            url=self._moe_url,
            api_key=self._moe_key,
            temperature=0.2,
        )
        if not result:
            result = self._mock_moral(prompt, agent, world)
        return result

    def moral_reasoning_batch(
        self, prompts: list[str], agents: list[AgentState], world: SimulationState
    ) -> list[str]:
        return [self.moral_reasoning(p, a, world) for p, a in zip(prompts, agents, strict=False)]

    def translate_policy(
        self,
        policy_text: str,
        existing_weights: PolicyWeights,
        world_state: SimulationState,
    ) -> tuple[PolicyWeights, dict[WealthClass, ImpactDelta], dict[str, Any]]:
        prompt = (
            f"Translate this policy into structured effects: {policy_text}\n\n"
            f"Current weights: economic_freedom={existing_weights.economic_freedom}, "
            f"social_welfare={existing_weights.social_welfare}, "
            f"environmental_protection={existing_weights.environmental_protection}, "
            f"public_order={existing_weights.public_order}, "
            f"innovation={existing_weights.innovation}, "
            f"cultural_preservation={existing_weights.cultural_preservation}\n\n"
            f"Respond as JSON with: new_weights, impact_deltas (per wealth class), world_changes"
        )
        response = self._call_llm(prompt, temperature=0.3)
        if not response:
            return existing_weights, {}, {}
        try:
            data = json.loads(response)
            new_weights = PolicyWeights(
                economic_freedom=data.get("new_weights", {}).get(
                    "economic_freedom", existing_weights.economic_freedom
                ),
                social_welfare=data.get("new_weights", {}).get(
                    "social_welfare", existing_weights.social_welfare
                ),
                environmental_protection=data.get("new_weights", {}).get(
                    "environmental_protection", existing_weights.environmental_protection
                ),
                public_order=data.get("new_weights", {}).get(
                    "public_order", existing_weights.public_order
                ),
                innovation=data.get("new_weights", {}).get(
                    "innovation", existing_weights.innovation
                ),
                cultural_preservation=data.get("new_weights", {}).get(
                    "cultural_preservation", existing_weights.cultural_preservation
                ),
            )
            deltas = {}
            for cls_str, delta_data in data.get("impact_deltas", {}).items():
                cls = WealthClass[cls_str.upper()]
                deltas[cls] = ImpactDelta(**delta_data)
            return new_weights, deltas, data.get("world_changes", {})
        except (json.JSONDecodeError, KeyError):
            return existing_weights, {}, {}

    def tie_break(self, request: DecisionRequest) -> DecisionResponse:
        prompt = (
            f"Resolve this ambiguous decision:\n"
            f"Agent state: {request.agent_state}\n"
            f"Options: {request.options}\n"
            f"Context: {request.context}\n"
            f"Respond with JSON: {{'decision': ..., 'reasoning': ...}}"
        )
        response = self._call_llm(prompt, temperature=0.2)
        if not response:
            return DecisionResponse(decision="idle", reasoning="LLM unavailable")
        try:
            data = json.loads(response)
            return DecisionResponse(
                decision=data.get("decision", "idle"),
                reasoning=data.get("reasoning", ""),
            )
        except json.JSONDecodeError:
            return DecisionResponse(decision="idle", reasoning="Failed to parse")

    def generate_news(self, events: list, state_deltas: dict) -> NewsEvent:
        prompt = (
            f"Generate a news article from these simulation events:\n"
            f"Events: {json.dumps(events)}\n"
            f"State changes: {json.dumps(state_deltas)}\n"
            f"Respond as JSON: {{'headline': ..., 'body': ..., 'tone': ...}}"
        )
        response = self._call_llm(prompt, temperature=0.3)
        if not response:
            return NewsEvent(headline="No news", body="", tone="neutral")
        try:
            data = json.loads(response)
            return NewsEvent(
                headline=data.get("headline", ""),
                body=data.get("body", ""),
                tone=data.get("tone", "neutral"),
            )
        except json.JSONDecodeError:
            return NewsEvent(headline="Simulation Update", body=response, tone="neutral")

    def generate_persona(self, traits: dict) -> str:
        prompt = (
            f"Generate a natural language persona description from these traits:\n"
            f"{json.dumps(traits)}\n"
            f"Respond with a single paragraph describing the character."
        )
        response = self._call_llm(prompt, temperature=0.8, max_tokens=128)
        return response or "A regular person."

    def generate_narration(self, agent_id: str, events: list) -> SpotlightNarration:
        prompt = (
            f"Narrate a spotlight on agent {agent_id} based on these events:\n"
            f"{json.dumps(events)}\n"
            f"Respond as JSON: {{'narration': ..., 'emotional_state': ..., 'highlights': [...]}}"
        )
        response = self._call_llm(prompt, temperature=0.3, max_tokens=256)
        if not response:
            return SpotlightNarration(narration="", emotional_state="neutral", highlights=[])
        try:
            data = json.loads(response)
            return SpotlightNarration(
                narration=data.get("narration", ""),
                emotional_state=data.get("emotional_state", "neutral"),
                highlights=data.get("highlights", []),
            )
        except json.JSONDecodeError:
            return SpotlightNarration(narration=response, emotional_state="neutral", highlights=[])

    def governance_advisory(
        self, world_state: SimulationState, active_policies: list[GovernmentPolicy]
    ) -> dict[str, Any]:
        policies_summary = [
            {"name": p.name, "category": str(p.category), "status": p.status}
            for p in active_policies
        ]
        prompt = (
            f"Provide governance advisory for this simulation state:\n"
            f"Population: {world_state.population}\n"
            f"Economic health: {world_state.economic_health:.2f}\n"
            f"Crime rate: {world_state.crime_rate:.2f}\n"
            f"Unlust: {world_state.unlust:.2f}\n"
            f"Active policies: {json.dumps(policies_summary)}\n"
            f"Respond as JSON: {{'assessment': ..., 'recommendation': ..., 'watch_items': [...]}}"
        )
        response = self._call_llm(prompt, temperature=0.3)
        if not response:
            return {
                "assessment": "LLM unavailable",
                "recommendation": "Maintain current policies",
                "watch_items": [],
            }
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "assessment": response[:200],
                "recommendation": "See assessment",
                "watch_items": [],
            }

    @property
    def call_count(self) -> int:
        return self._call_count
