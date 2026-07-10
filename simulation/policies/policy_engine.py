"""
Policy Engine
=============

Manages policy application and effect calculation.
"""

from typing import Dict, List, Optional

from shared.schemas.policy import Policy, GovernmentPolicy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.interfaces.i_ai_router import IAIRouter
from shared.interfaces.i_policy_engine import IPolicyEngine
from simulation.policies.policy_translator import translate_and_apply_policy


class PolicyEngine(IPolicyEngine):
    """
    Engine for managing government policies and their effects.

    Tracks active policies and calculates their aggregate effects
    on agent decision-making.

    Attributes:
        _active_policies: Dictionary of active policies
    """

    def __init__(self):
        """Initialize an empty policy engine."""
        self._active_policies: Dict[str, GovernmentPolicy] = {}

    def apply_policy(
        self,
        policy: Policy,
        ai_router: Optional[IAIRouter] = None,
        world_state: Optional[SimulationState] = None,
    ) -> None:
        """Apply a policy to the simulation.

        When *ai_router* is available and *policy* has a non-empty
        *description*, the description is translated into structured
        ``PolicyWeights`` and ``ImpactDelta`` using the LLM.  When the LLM
        is unavailable, falls back to deterministic keyword matching (see
        :mod:`~simulation.policies.policy_fallback`).

        Args:
            policy: The policy to apply.
            ai_router: Optional AI router for LLM-based policy translation.
            world_state: Optional world state for translation context.
        """
        if ai_router is not None and world_state is not None and policy.description:
            try:
                existing_weights = self.get_aggregate_weights()
                gov_policy = translate_and_apply_policy(
                    policy=policy,
                    ai_router=ai_router,
                    existing_weights=existing_weights,
                    world_state=world_state,
                )
            except Exception:
                # translate_and_apply_policy already catches LLM errors, but
                # guard against unexpected bugs in the bridge itself.
                from simulation.policies.policy_fallback import translate_policy_fallback

                gp = translate_policy_fallback(
                    policy.description or policy.name, policy.id
                )
                gov_policy = GovernmentPolicy(
                    policy=policy,
                    impact_deltas=gp.impact_deltas,
                    policy_weights=gp.policy_weights,
                )
        else:
            # No AI router or no description — use rule-based fallback.
            from simulation.policies.policy_fallback import translate_policy_fallback

            gp = translate_policy_fallback(
                policy.description or policy.name, policy.id
            )
            gov_policy = GovernmentPolicy(
                policy=policy,
                impact_deltas=gp.impact_deltas,
                policy_weights=gp.policy_weights,
            )

        self._active_policies[policy.id] = gov_policy

    def revoke_policy(self, policy_id: str) -> None:
        """
        Revoke an active policy.

        Args:
            policy_id: ID of the policy to revoke
        """
        if policy_id in self._active_policies:
            del self._active_policies[policy_id]

    def get_active_policies(self) -> List[GovernmentPolicy]:
        """
        Get all active policies.

        Returns:
            List of active GovernmentPolicy objects
        """
        return list(self._active_policies.values())

    def get_policy(self, policy_id: str) -> Optional[GovernmentPolicy]:
        """
        Get a specific policy.

        Args:
            policy_id: ID of the policy to retrieve

        Returns:
            GovernmentPolicy if found, None otherwise
        """
        return self._active_policies.get(policy_id)

    def get_aggregate_weights(self) -> PolicyWeights:
        """Aggregate all active policy weights, normalised to [-1, 1].

        Sums the ``policy_weights`` of every active ``GovernmentPolicy``
        and clamps each dimension to the range [-1, 1] so that extreme
        combinations do not produce unbounded values.

        Returns:
            Combined ``PolicyWeights`` with each component in [-1, 1].
        """
        total = PolicyWeights()
        for gp in self._active_policies.values():
            w = gp.policy_weights
            total.economic_freedom += w.economic_freedom
            total.social_welfare += w.social_welfare
            total.environmental_protection += w.environmental_protection
            total.public_order += w.public_order
            total.innovation += w.innovation
            total.cultural_preservation += w.cultural_preservation

        # Clamp to [-1, 1]
        def _clamp(v: float) -> float:
            return max(-1.0, min(1.0, v))

        return PolicyWeights(
            economic_freedom=_clamp(total.economic_freedom),
            social_welfare=_clamp(total.social_welfare),
            environmental_protection=_clamp(total.environmental_protection),
            public_order=_clamp(total.public_order),
            innovation=_clamp(total.innovation),
            cultural_preservation=_clamp(total.cultural_preservation),
        )

    def calculate_policy_effect(self, policy: Policy, agent_context: dict) -> dict:
        """
        Calculate the effect of a policy on a specific agent.

        Args:
            policy: The policy to evaluate
            agent_context: Agent context for effect calculation

        Returns:
            Dictionary of effect values

        TODO: Implement effect calculation
            - Apply policy weights to agent context
            - Calculate modified utility scores
        """
        # TODO: Implement
        return {}
