"""Policy translation bridge — wires VLLMRouter.translate_policy into the simulation.

Provides a single entry point for translating natural-language policy descriptions
into structured PolicyWeights and ImpactDeltas. Falls back to deterministic keyword
matching when the AI router is unavailable or throws an error.

Typical usage:
    gov_policy = translate_and_apply_policy(
        policy, ai_router, policy_engine.get_aggregate_weights(), world_state
    )
    policy_engine._active_policies[policy.id] = gov_policy
"""

from __future__ import annotations

from typing import Dict

from shared.schemas.policy import GovernmentPolicy, Policy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.interfaces.i_ai_router import IAIRouter

__all__ = ["translate_and_apply_policy"]


def translate_and_apply_policy(
    policy: Policy,
    ai_router: IAIRouter,
    existing_weights: PolicyWeights,
    world_state: SimulationState,
) -> GovernmentPolicy:
    """Translate a free-text policy description into structured effects.

    Calls ``ai_router.translate_policy()`` to obtain LLM-generated
    ``PolicyWeights``, per-wealth-class ``ImpactDelta``, and optional
    world-level changes.  When the LLM call fails, falls back to the
    deterministic keyword matcher in :mod:`policy_fallback`.

    World-level changes (tax rate, welfare toggle, food-availability
    events) are applied directly to *world_state* before returning.

    Args:
        policy: The policy definition (``policy.description`` is the LLM
            input text).
        ai_router: Connected AI router (usually a VLLMRouter).
        existing_weights: Aggregate weights from currently active policies
            (used as a baseline by the LLM).
        world_state: Mutable world state.  World-level changes from the
            translation are applied to this object in place.

    Returns:
        A fully populated ``GovernmentPolicy`` with ``impact_deltas`` and
        ``policy_weights`` filled in.

    Raises:
        (No exception escapes — all errors are caught and result in a
        fallback ``GovernmentPolicy``.)
    """
    if not policy.description:
        # No description to translate — return a neutral policy.
        return GovernmentPolicy(
            policy=policy,
            impact_deltas={},
            policy_weights=PolicyWeights(),
        )

    try:
        new_weights, impact_deltas, world_changes = ai_router.translate_policy(
            policy_text=policy.description,
            existing_weights=existing_weights,
            world_state=world_state,
        )
    except Exception:
        # LLM call failed — fall back to deterministic keyword matching.
        return _fallback_translate(policy)

    # Apply world-level changes from the translation.
    _apply_world_changes(world_changes, world_state)

    return GovernmentPolicy(
        policy=policy,
        impact_deltas=impact_deltas,
        policy_weights=new_weights,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _apply_world_changes(
    world_changes: Dict[str, object],
    world_state: SimulationState,
) -> None:
    """Apply world-level changes returned by the LLM translation."""
    raw_tax = world_changes.get("new_tax_rate")
    if raw_tax is not None:
        world_state.tax_rate = float(raw_tax)  # type: ignore[arg-type]

    raw_welfare = world_changes.get("welfare_on")
    if raw_welfare is not None:
        world_state.welfare_enabled = bool(raw_welfare)  # type: ignore[arg-type]

    raw_food = world_changes.get("food_event")
    if raw_food is not None:
        world_state.food_availability = max(
            0.0, min(1.0, world_state.food_availability + float(raw_food))  # type: ignore[arg-type]
        )


def _fallback_translate(policy: Policy) -> GovernmentPolicy:
    """Fallback to deterministic keyword-based translation."""
    # Delayed import to avoid circular dependency at module level.
    from simulation.policies.policy_fallback import translate_policy_fallback

    gp = translate_policy_fallback(policy.description or policy.name, policy.id)
    # Preserve the original Policy object so the rest of the system sees the
    # same id/name/category as the caller intended.
    gp = GovernmentPolicy(
        policy=policy,
        impact_deltas=gp.impact_deltas,
        policy_weights=gp.policy_weights,
    )
    return gp
