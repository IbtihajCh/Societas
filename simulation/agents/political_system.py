"""Political system — campaign, influence, and career tracking."""

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import ActionType, NeedType
from shared.utilities.deterministic_rng import DeterministicRNG


def can_campaign(agent: AgentState) -> bool:
    """Check if agent can campaign: notoriety > 0.4 AND ambition > 0.5 AND money > 100."""
    return (
        agent.notoriety > 0.4
        and agent.traits.ambition > 0.5
        and agent.resources.money > 100
    )


def do_campaign(agent: AgentState, rng: DeterministicRNG, result: object) -> None:
    """Execute a campaign action. Deducts 10-30 money."""
    cost = rng.uniform(10.0, 30.0)
    agent.resources.money -= cost
    agent.resources.wealth = agent.resources.money
    agent.notoriety = min(1.0, agent.notoriety + 0.1)
    rep = agent.needs.get_level(NeedType.REPUTATION)
    agent.needs.set_level(NeedType.REPUTATION, rep + 0.05)
    speech_chance = agent.traits.ambition * 0.02
    if rng.random() < speech_chance:
        agent.notoriety = min(1.0, agent.notoriety + 0.2)


def process_political_influence(agent: AgentState, all_agents: list[AgentState], world: SimulationState) -> None:
    """High-notoriety agent (>0.7) can influence nearby agents' morale."""
    if agent.notoriety <= 0.7:
        return
    from simulation.agents.action_executor import get_nearby_agents
    nearby = get_nearby_agents(agent, all_agents)
    for other in nearby:
        if other.wealth_class == agent.wealth_class:
            other.unlust = max(0.0, other.unlust - 0.02)


def track_political_career(agent: AgentState, world: SimulationState) -> None:
    """If notoriety > 0.8 AND actions include 10+ CAMPAIGN total, set politician flag."""
    if agent.notoriety > 0.8:
        action_history = agent.metadata.get("action_history", [])
        campaign_count = sum(1 for a in action_history if a == ActionType.CAMPAIGN)
        if campaign_count >= 10:
            agent.metadata["politician"] = True
