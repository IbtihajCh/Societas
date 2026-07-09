import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from pathlib import Path

from models.router.ai_router import AIRouter
from models.router.config import AIConfig
from shared.schemas.decision import DecisionRequest, DecisionOption
from shared.types.enums import ActionType

logger = logging.getLogger("societas.ai.evaluation")


@dataclass
class EvaluationResult:
    scenario: str = ""
    passed: bool = False
    duration_ms: float = 0.0
    expected: dict | None = None
    actual: dict | None = None
    error: str | None = None


ScenarioFunc = Callable[[AIRouter], EvaluationResult]


def evaluate_scenario(router: AIRouter, name: str, fn: ScenarioFunc) -> EvaluationResult:
    logger.info("Evaluating scenario: %s", name)
    start = time.perf_counter()
    try:
        result = fn(router)
        result.duration_ms = (time.perf_counter() - start) * 1000
        result.scenario = name
    except Exception as e:
        result = EvaluationResult(
            scenario=name,
            passed=False,
            duration_ms=(time.perf_counter() - start) * 1000,
            error=str(e),
        )
    status = "PASS" if result.passed else "FAIL"
    logger.info("Scenario %s: %s (%.1fms)", name, status, result.duration_ms)
    return result


def run_evaluation_suite(router: AIRouter) -> list[EvaluationResult]:
    results = []
    results.append(evaluate_scenario(router, "tie_break_basic", _eval_tie_break_basic))
    results.append(evaluate_scenario(router, "policy_translation_basic", _eval_policy_translation_basic))
    results.append(evaluate_scenario(router, "persona_generation_basic", _eval_persona_generation_basic))
    results.append(evaluate_scenario(router, "narrative_generation_basic", _eval_narrative_generation_basic))
    return results


def _eval_tie_break_basic(router: AIRouter) -> EvaluationResult:
    request = DecisionRequest(
        agent_id="eval-agent",
        state="Normal conditions, needs partially satisfied.",
        unlust=0.3,
        morality=0.7,
        options=[
            DecisionOption(action=ActionType.WORK, label="Work", utility_scores={"wealth": 0.8, "stress": 0.3}),
            DecisionOption(action=ActionType.SOCIALIZE, label="Socialize", utility_scores={"social": 0.7, "fun": 0.6}),
        ],
    )
    response = router.tie_break(request)
    return EvaluationResult(
        passed=response.confidence > 0.0,
        expected={"action_type": "WORK or SOCIALIZE"},
        actual={"action": str(response.action), "confidence": response.confidence, "reason": response.reason},
    )


def _eval_policy_translation_basic(router: AIRouter) -> EvaluationResult:
    weights = router.translate_policy(
        persona="A conservative trader focused on economic growth.",
        goal="Reduce business taxes to stimulate the economy.",
        context={"world_state_summary": "Economy stagnant", "time_step": 50, "active_policies": []},
    )
    return EvaluationResult(
        passed=True,
        expected={"weights": "any 6-dim vector"},
        actual={
            "economic_freedom": weights.economic_freedom,
            "social_welfare": weights.social_welfare,
            "innovation": weights.innovation,
        },
    )


def _eval_persona_generation_basic(router: AIRouter) -> EvaluationResult:
    persona = router.generate_persona({
        "ambition": 0.9, "risk_tolerance": 0.8, "materialism": 0.7,
    })
    return EvaluationResult(
        passed=len(persona) > 10,
        expected={"persona_length": "> 10 chars"},
        actual={"persona": persona[:100]},
    )


def _eval_narrative_generation_basic(router: AIRouter) -> EvaluationResult:
    news = router.generate_news(
        events=[{"type": "policy_passed", "tick": 100, "description": "New tax law enacted"}],
        state_deltas={"economic_health": 0.1, "social_cohesion": -0.05},
    )
    return EvaluationResult(
        passed=len(news.body) > 5,
        expected={"body_length": "> 5 chars"},
        actual={"headline": news.headline, "body_preview": news.body[:100]},
    )
