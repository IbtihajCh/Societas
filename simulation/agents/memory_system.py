"""
Agent Memory System
===================

Rule-based episodic memory system for SOCIETAS agents.
Stores and retrieves deterministic episodic memories with emotional valence
and decay. No LLM used for memory operations.

Constants:
    MAX_MEMORIES: Maximum number of memories stored per agent.
    MEMORY_IMPORTANCE_ACTION_BASE: Base importance for economic actions.
    MEMORY_IMPORTANCE_SOCIAL: Importance for social interactions.
    MEMORY_IMPORTANCE_TRAUMA: Importance for traumatic events.
    MEMORY_DECAY_PER_TICK: Decay rate per tick for emotional impact.
"""

from dataclasses import dataclass, field
from typing import Optional

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.types.enums import ActionType

# ── Constants ────────────────────────────────────────────────────────────────

MAX_MEMORIES: int = 50
"""Maximum number of memories stored per agent (FIFO eviction)."""

MEMORY_IMPORTANCE_ACTION_BASE: float = 0.3
"""Base importance for routine economic actions (work, buy_food)."""

MEMORY_IMPORTANCE_SOCIAL: float = 0.4
"""Importance for social interaction memories (befriend, console, share)."""

MEMORY_IMPORTANCE_TRAUMA: float = 0.7
"""Importance for traumatic/criminal memories (steal, harm_other)."""

MEMORY_DECAY_PER_TICK: float = 0.01
"""Decay rate per tick applied to emotional impact of memories."""


# ── Data Classes ─────────────────────────────────────────────────────────────

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
    involved_agents: list[str] = field(default_factory=list)
    importance: float = 0.3
    action: Optional[str] = None


# ── Core Functions ───────────────────────────────────────────────────────────

def store_memory(agent: AgentState, memory: Memory) -> None:
    """Append a memory to the agent's memory list.

    If the agent already has MAX_MEMORIES entries, the oldest memory is
    evicted (FIFO).

    Args:
        agent: The agent whose memory list is being modified.
        memory: The Memory instance to store.
    """
    agent.memories.append(memory)
    if len(agent.memories) > MAX_MEMORIES:
        agent.memories.pop(0)


def get_recent_memories(agent: AgentState, k: int = 10) -> list[Memory]:
    """Return the *k* most recent memories.

    Args:
        agent: The agent whose memories are being queried.
        k: Maximum number of memories to return.

    Returns:
        A list of the last *k* Memory objects (most recent first).
    """
    return list(agent.memories[-k:])


def get_important_memories(
    agent: AgentState, threshold: float = 0.7
) -> list[Memory]:
    """Return memories whose importance exceeds *threshold*.

    Results are ordered newest-first.

    Args:
        agent: The agent whose memories are being queried.
        threshold: Minimum importance value to include.

    Returns:
        Filtered list of Memory objects.
    """
    return [m for m in reversed(agent.memories) if m.importance > threshold]


def get_memories_by_type(
    agent: AgentState, event_type: str, k: int = 5
) -> list[Memory]:
    """Return the *k* most recent memories of a specific event type.

    Args:
        agent: The agent whose memories are being queried.
        event_type: The event type string to filter by.
        k: Maximum number of memories to return.

    Returns:
        A list of matching Memory objects (most recent first).
    """
    matching = [m for m in reversed(agent.memories) if m.event_type == event_type]
    return matching[:k]


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
    if not agent.memories:
        return ""

    important = [m for m in reversed(agent.memories) if m.importance >= 0.5][:5]
    recent = list(agent.memories[-3:])

    # Deduplicate: combine important + recent, preserve order, avoid repeats
    seen: set[str] = set()
    selected: list[Memory] = []
    for m in important + recent:
        key = f"{m.tick}:{m.description}"
        if key not in seen:
            seen.add(key)
            selected.append(m)

    descriptions = []
    for mem in selected[:7]:
        desc = mem.description
        descriptions.append(desc)

    if not descriptions:
        return ""

    return "Recent memories: " + " ".join(descriptions)


def collect_tick_memories(
    agent: AgentState,
    action_result: AgentActionResult | None,
    world: SimulationState,
    tick_number: int,
) -> None:
    """Auto-store episodic memories based on the agent's last action and state.

    Called after each action (or at the end of a tick for deterministic agents).
    Uses ``agent.last_action`` to determine what kind of memory to store.

    Args:
        agent: The agent whose memory is being recorded.
        action_result: Optional result from the action execution.
        world: Current world state (used for context).
        tick_number: Current simulation tick.
    """
    # ── Death memory (highest importance) ────────────────────────────────
    if agent.cause_of_death and not agent.is_alive:
        death_memory = Memory(
            tick=tick_number,
            event_type="env_event",
            description=f"You died from {agent.cause_of_death}.",
            emotional_valence=-0.9,
            importance=0.9,
        )
        store_memory(agent, death_memory)
        return  # No other memories matter after death

    # ── Emotional valence from current happiness ─────────────────────────
    happiness = agent.emotions.happiness_score
    valence = happiness * 2.0 - 1.0  # 0.5 → 0.0, 1.0 → 1.0, 0.0 → -1.0

    action = agent.last_action if agent.last_action else ActionType.IDLE

    # ── Action-based memories ────────────────────────────────────────────
    if action in (ActionType.WORK, ActionType.BUY_FOOD):
        noun = "worked" if action == ActionType.WORK else "bought food"
        store_memory(
            agent,
            Memory(
                tick=tick_number,
                event_type="economic_change",
                description=f"You {noun}.",
                emotional_valence=valence,
                importance=MEMORY_IMPORTANCE_ACTION_BASE,
                action=action.value,
            ),
        )

    elif action in (ActionType.BEFRIEND, ActionType.CONSOLE, ActionType.SHARE):
        action_verb = {
            ActionType.BEFRIEND: "befriended",
            ActionType.CONSOLE: "consoled",
            ActionType.SHARE: "shared with",
        }.get(action, "interacted with")
        store_memory(
            agent,
            Memory(
                tick=tick_number,
                event_type="social_interaction",
                description=f"You {action_verb} someone.",
                emotional_valence=valence,
                importance=MEMORY_IMPORTANCE_SOCIAL,
                action=action.value,
            ),
        )

    elif action in (ActionType.STEAL, ActionType.HARM_OTHER):
        action_verb = {
            ActionType.STEAL: "stole from",
            ActionType.HARM_OTHER: "harmed",
        }.get(action, "wronged")
        store_memory(
            agent,
            Memory(
                tick=tick_number,
                event_type="action_taken",
                description=f"You {action_verb} someone.",
                emotional_valence=valence,
                importance=MEMORY_IMPORTANCE_TRAUMA,
                action=action.value,
            ),
        )

    elif action == ActionType.PROTEST:
        store_memory(
            agent,
            Memory(
                tick=tick_number,
                event_type="action_taken",
                description="You joined a protest.",
                emotional_valence=valence,
                importance=0.5,
                action=action.value,
            ),
        )

    elif action == ActionType.COMPLY:
        store_memory(
            agent,
            Memory(
                tick=tick_number,
                event_type="action_taken",
                description="You complied with the authorities.",
                emotional_valence=valence,
                importance=0.1,
                action=action.value,
            ),
        )


def compute_emotional_impact(memory: Memory, agent: AgentState) -> float:
    """Compute how much a memory affects the agent's current decisions.

    Impact decays linearly with tick distance:
        impact = importance × max(0, 1 - (current_tick - memory.tick) × DECAY)

    Args:
        memory: The memory whose emotional impact is being evaluated.
        agent: The agent (used to derive current tick from memory count).

    Returns:
        A float between 0.0 (fully decayed) and 1.0 (fresh, highly important).
    """
    # Estimate current tick from the most recent memory's tick
    if agent.memories:
        current_tick = agent.memories[-1].tick
    else:
        current_tick = memory.tick

    ticks_ago = current_tick - memory.tick
    decay_factor = max(0.0, 1.0 - ticks_ago * MEMORY_DECAY_PER_TICK)
    return memory.importance * decay_factor
