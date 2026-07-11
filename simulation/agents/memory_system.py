"""Memory system — episodic memory collection for agents each tick."""

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.types.aliases import TickNumber

__all__ = ["collect_tick_memories"]


def collect_tick_memories(
    agent: AgentState,
    result: AgentActionResult | None,
    world: SimulationState,
    tick_number: TickNumber | int,
) -> None:
    """Collect an episodic memory for the agent from this tick.

    Each call stores a lightweight memory entry in the agent's internal
    memory list (``agent.memories``). When ``result`` is provided the
    memory includes the action outcome, score changes, and any metadata.
    The base call (``result=None``) records a passive tick observation.

    Args:
        agent: The agent whose memory is being recorded.
        result: The action result from this tick, or ``None`` for passive
            tick observations (e.g. community effects).
        world: The current world state.
        tick_number: The current simulation tick number.
    """
    if not hasattr(agent, "memories"):
        agent.memories = []

    # Keep memory bounded — only the most recent 500 entries
    if len(agent.memories) >= 500:
        agent.memories.pop(0)

    memory = {
        "tick": int(tick_number),
        "type": "action" if result else "observation",
        "health": float(agent.resources.health),
        "money": float(agent.resources.money),
        "happiness": float(agent.emotions.happiness_score),
        "unlust": float(getattr(agent, "unlust", 0.0)),
        "needs": {
            "food": float(agent.needs.get_level(agent.needs.FOOD)) if hasattr(agent.needs, "FOOD") else 0.0,
            "social": float(agent.needs.get_level(agent.needs.SOCIAL_CONNECTION)) if hasattr(agent.needs, "SOCIAL_CONNECTION") else 0.0,
            "safety": float(agent.needs.get_level(agent.needs.SAFETY)) if hasattr(agent.needs, "SAFETY") else 0.0,
        },
    }

    if result is not None:
        memory["action"] = str(result.action)
        memory["outcome"] = result.outcome
        memory["score_delta"] = dict(result.score_delta) if result.score_delta else {}
        if hasattr(result, "metadata") and result.metadata:
            memory["source"] = result.metadata.get("source", "unknown")
            memory["reasoning"] = result.metadata.get("reasoning", "")

    agent.memories.append(memory)
