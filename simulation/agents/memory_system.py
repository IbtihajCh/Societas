"""Memory system — episodic memory collection for agents each tick."""

from dataclasses import dataclass, field
from typing import Any

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.types.aliases import TickNumber

__all__ = ["Memory", "collect_tick_memories", "compute_memory_prompt"]


@dataclass
class Memory:
    """A single episodic memory for an agent.

    Attributes:
        tick: Simulation tick when the memory was formed.
        event_type: Category of the memory (action_taken, event_witnessed,
                    social_interaction, economic_change, env_event).
        description: Human-readable description of the event.
        emotional_valence: Emotional tone (-1.0 negative, 0.0 neutral, 1.0 positive).
        involved_agents: IDs of other agents involved in the event.
        importance: How significant this memory is (0.0 trivial, 1.0 life-changing).
        action: Optional ActionType value (as string) that produced this memory.
    """

    tick: int
    event_type: str
    description: str
    emotional_valence: float = 0.0
    involved_agents: list = field(default_factory=list)
    importance: float = 0.5
    action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def compute_memory_prompt(agent: AgentState) -> str:
    """Build a natural-language summary of recent memories for prompt injection.

    The summary includes the 5 most recent important memories (importance >= 0.5)
    and the 3 most recent memories of any type.

    Args:
        agent: The agent whose memories are being summarised.

    Returns:
        A string like ``"Recent memories: You worked and earned £50. …"``,
        or an empty string if there are no memories.
    """
    if not getattr(agent, "memories", None):
        return ""

    important: list = []
    recent: list = []
    for m in reversed(agent.memories):
        if isinstance(m, Memory):
            if m.importance >= 0.5 and len(important) < 5:
                important.append(m)
            if len(recent) < 3:
                recent.append(m)
        else:
            # dict-based memory: treat all as important/recent
            if len(important) < 5:
                important.append(m)
            if len(recent) < 3:
                recent.append(m)

    seen: set[str] = set()
    selected: list = []
    for m in important + recent:
        if isinstance(m, Memory):
            key = f"{m.tick}:{m.description}"
        else:
            key = f"{m.get('tick', 0)}:{m.get('description', m.get('type', ''))}"
        if key not in seen:
            seen.add(key)
            selected.append(m)

    if not selected:
        return ""

    parts: list[str] = []
    for m in selected:
        if isinstance(m, Memory):
            parts.append(m.description)
        else:
            t = m.get("type", "observation")
            action = m.get("action", "")
            parts.append(f"{t}{(': ' + action) if action else ''}")

    return "Recent memories: " + "; ".join(parts) + "."


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

    event_type = "action_taken" if result else "event_witnessed"
    action_str: str | None = None
    description = f"Tick {tick_number} observation"
    emotional_valence = 0.0
    importance = 0.3
    metadata: dict[str, Any] = {}

    if result is not None:
        action_str = str(result.action)
        description = f"You took action: {action_str}"
        if hasattr(result, "score_delta") and result.score_delta:
            hap = result.score_delta.get("happiness", 0.0)
            emotional_valence = max(-1.0, min(1.0, float(hap)))
            importance = min(1.0, 0.3 + abs(emotional_valence) * 0.5)
        if hasattr(result, "metadata") and result.metadata:
            metadata = dict(result.metadata)
            if "reasoning" in metadata:
                description += f" — {metadata['reasoning']}"

    memory = Memory(
        tick=int(tick_number),
        event_type=event_type,
        description=description,
        emotional_valence=emotional_valence,
        involved_agents=[],
        importance=importance,
        action=action_str,
        metadata=metadata,
    )
    agent.memories.append(memory)
