"""Policy effects — applies impact deltas and policy weights to agents.

Dual model:
1. ImpactDeltas: per-wealth-class direct effects applied each tick
2. PolicyWeights: modify utility scores for action selection
"""


from shared.schemas.agent_state import AgentState
from shared.schemas.policy import GovernmentPolicy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import ActionType, NeedType

__all__ = [
    "apply_policy_effects",
    "apply_policy_weights",
    "apply_all_policies",
]


def apply_policy_effects(
    agent: AgentState,
    policy: GovernmentPolicy,
    world: SimulationState,
    world_changed: dict[str, bool],
) -> None:
    """Apply a policy's impact deltas to an agent.

    Args:
        agent: The agent to apply effects to (modified in place).
        policy: The government policy with impact deltas.
        world: Mutable world state (world-level changes applied once).
        world_changed: Dict tracking which world changes have been applied
                       (prevents applying the same world change multiple times).
    """
    delta = policy.impact_deltas.get(agent.wealth_class)
    if delta is None:
        return

    agent.resources.money += delta.money_delta
    agent.resources.wealth = agent.resources.money
    agent.needs.set_level(
        NeedType.FOOD,
        agent.needs.get_level(NeedType.FOOD) + delta.food_delta,
    )
    agent.needs.set_level(
        NeedType.SAFETY,
        agent.needs.get_level(NeedType.SAFETY) + delta.safety_delta,
    )
    agent.needs.set_level(
        NeedType.SOCIAL_CONNECTION,
        agent.needs.get_level(NeedType.SOCIAL_CONNECTION) + delta.social_delta,
    )
    agent.unlust = min(1.0, agent.unlust + delta.anger_spike)

    # World state changes (applied once per policy, not per agent)
    policy_key = str(id(policy))
    if delta.new_tax_rate is not None and not world_changed.get(f"{policy_key}_tax"):
        world.tax_rate = delta.new_tax_rate
        world_changed[f"{policy_key}_tax"] = True
    if delta.welfare_on is not None and not world_changed.get(f"{policy_key}_welfare"):
        world.welfare_enabled = delta.welfare_on
        world_changed[f"{policy_key}_welfare"] = True
    if delta.food_event is not None and not world_changed.get(f"{policy_key}_food"):
        world.food_availability = max(
            0.0, min(1.0, world.food_availability + delta.food_event)
        )
        world_changed[f"{policy_key}_food"] = True


def apply_policy_weights(
    base_scores: dict[ActionType, float],
    policy_weights: PolicyWeights,
) -> dict[ActionType, float]:
    """Modify utility scores based on active policy weights.

    Policy weights shift the utility landscape:
    - economic_freedom > 0: boosts WORK
    - social_welfare > 0: boosts SHARE, CONSOLE, reduces STEAL
    - public_order > 0: reduces PROTEST, STEAL, HARM_OTHER
    - environmental_protection > 0: boosts HOBBY, reduces STEAL/HARM_OTHER
    - innovation > 0: boosts WORK, INVEST
    - cultural_preservation > 0: boosts HOBBY, CONSOLE

    Args:
        base_scores: Base utility scores per action.
        policy_weights: Policy weight modifiers.

    Returns:
        Modified scores dict (new dict, base not modified).
    """
    modified = dict(base_scores)
    for action, score in modified.items():
        modifier = 0.0
        if action == ActionType.WORK:
            modifier += policy_weights.economic_freedom * 0.1
            modifier += policy_weights.innovation * 0.08
        elif action == ActionType.SHARE:
            modifier += policy_weights.social_welfare * 0.15
        elif action == ActionType.CONSOLE:
            modifier += policy_weights.social_welfare * 0.1
            modifier += policy_weights.cultural_preservation * 0.06
        elif action == ActionType.STEAL:
            modifier -= policy_weights.social_welfare * 0.1
            modifier -= policy_weights.public_order * 0.15
            modifier -= policy_weights.environmental_protection * 0.05
        elif action == ActionType.HARM_OTHER:
            modifier -= policy_weights.public_order * 0.2
            modifier -= policy_weights.environmental_protection * 0.05
        elif action == ActionType.PROTEST:
            modifier -= policy_weights.public_order * 0.1
        elif action == ActionType.HOBBY:
            modifier += policy_weights.environmental_protection * 0.1
            modifier += policy_weights.cultural_preservation * 0.12
        elif action == ActionType.INVEST:
            modifier += policy_weights.innovation * 0.12
        modified[action] = score + modifier
    return modified


def apply_all_policies(
    agents: list[AgentState],
    policies: list[GovernmentPolicy],
    world: SimulationState,
) -> None:
    """Apply all active policy effects to all agents for one tick.

    Args:
        agents: All living agents.
        policies: All active government policies.
        world: World state (may be modified by policy world changes).
    """
    world_changed: dict[str, bool] = {}
    for agent in agents:
        if not agent.is_alive:
            continue
        for policy in policies:
            apply_policy_effects(agent, policy, world, world_changed)
