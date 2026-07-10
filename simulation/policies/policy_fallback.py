"""Policy fallback — deterministic keyword matching for policy translation.

When the LLM (Gemma 31B) is unavailable, this module provides deterministic
policy translation by matching keywords in the policy text to predefined
ImpactDeltas and PolicyWeights.
"""

from shared.types.enums import PolicyCategory, WealthClass
from shared.schemas.policy import (
    GovernmentPolicy,
    ImpactDelta,
    Policy,
    PolicyWeights,
)
from shared.types.aliases import PolicyId

__all__ = ["translate_policy_fallback", "FALLBACK_KEYWORD_POLICIES"]


FALLBACK_KEYWORD_POLICIES: dict[str, dict[str, object]] = {
    "tax increase": {
        "weights": PolicyWeights(economic_freedom=-0.3, public_order=0.1),
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=-2.0, anger_spike=0.05),
            WealthClass.MIDDLE: ImpactDelta(money_delta=-10.0, anger_spike=0.02),
            WealthClass.RICH: ImpactDelta(money_delta=-50.0, anger_spike=0.01),
        },
    },
    "tax cut": {
        "weights": PolicyWeights(economic_freedom=0.3),
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=2.0),
            WealthClass.MIDDLE: ImpactDelta(money_delta=10.0),
            WealthClass.RICH: ImpactDelta(money_delta=50.0),
        },
    },
    "welfare": {
        "weights": PolicyWeights(social_welfare=0.4),
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=8.0, safety_delta=0.05),
            WealthClass.MIDDLE: ImpactDelta(money_delta=0.0),
            WealthClass.RICH: ImpactDelta(money_delta=-5.0, anger_spike=0.02),
        },
    },
    "food subsidy": {
        "weights": PolicyWeights(social_welfare=0.2),
        "deltas": {
            WealthClass.POOR: ImpactDelta(food_delta=0.10, money_delta=-1.0),
            WealthClass.MIDDLE: ImpactDelta(food_delta=0.05, money_delta=-2.0),
            WealthClass.RICH: ImpactDelta(food_delta=0.02, money_delta=-10.0),
        },
    },
    "police": {
        "weights": PolicyWeights(public_order=0.4),
        "deltas": {
            WealthClass.POOR: ImpactDelta(safety_delta=0.10),
            WealthClass.MIDDLE: ImpactDelta(safety_delta=0.08),
            WealthClass.RICH: ImpactDelta(safety_delta=0.05),
        },
    },
    "education": {
        "weights": PolicyWeights(economic_freedom=0.1, social_welfare=0.2),
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=5.0, safety_delta=0.03),
            WealthClass.MIDDLE: ImpactDelta(money_delta=2.0),
            WealthClass.RICH: ImpactDelta(money_delta=-20.0),
        },
    },
    "housing": {
        "weights": PolicyWeights(social_welfare=0.3),
        "deltas": {
            WealthClass.POOR: ImpactDelta(safety_delta=0.08, money_delta=3.0),
            WealthClass.MIDDLE: ImpactDelta(safety_delta=0.05),
            WealthClass.RICH: ImpactDelta(money_delta=-15.0),
        },
    },
    "minimum wage": {
        "weights": PolicyWeights(economic_freedom=-0.1, social_welfare=0.2),
        "deltas": {
            WealthClass.POOR: ImpactDelta(money_delta=5.0),
            WealthClass.MIDDLE: ImpactDelta(money_delta=3.0),
            WealthClass.RICH: ImpactDelta(money_delta=-10.0),
        },
    },
}


def translate_policy_fallback(
    policy_text: str, policy_id: PolicyId
) -> GovernmentPolicy:
    """Translate a natural language policy using keyword matching.

    Matches keywords in the policy text to predefined ImpactDeltas and
    PolicyWeights. If no keywords match, returns a neutral policy with
    no effects.

    Args:
        policy_text: Natural language policy description.
        policy_id: Unique policy identifier.

    Returns:
        GovernmentPolicy with matched weights and deltas.
    """
    text_lower = policy_text.lower()

    best_match: dict[str, object] | None = None
    best_match_length = 0

    for keyword, config in FALLBACK_KEYWORD_POLICIES.items():
        if keyword in text_lower and len(keyword) > best_match_length:
            best_match = config
            best_match_length = len(keyword)

    if best_match is None:
        return GovernmentPolicy(
            policy=Policy(
                id=policy_id,
                name=policy_text[:50],
                description=policy_text,
                category=PolicyCategory.ECONOMIC,
                weights=PolicyWeights(),
            ),
            impact_deltas={},
            policy_weights=PolicyWeights(),
        )

    weights = best_match["weights"]  # type: ignore[assignment]
    deltas = best_match["deltas"]  # type: ignore[assignment]

    category = PolicyCategory.ECONOMIC
    if "welfare" in text_lower or "housing" in text_lower:
        category = PolicyCategory.SOCIAL
    elif "police" in text_lower:
        category = PolicyCategory.PUBLIC_ORDER
    elif "education" in text_lower:
        category = PolicyCategory.EDUCATION

    return GovernmentPolicy(
        policy=Policy(
            id=policy_id,
            name=policy_text[:50],
            description=policy_text,
            category=category,
            weights=weights if isinstance(weights, PolicyWeights) else PolicyWeights(),
        ),
        impact_deltas=deltas if isinstance(deltas, dict) else {},
        policy_weights=weights if isinstance(weights, PolicyWeights) else PolicyWeights(),
    )
