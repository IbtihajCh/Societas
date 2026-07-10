"""
Environmental Events System
============================

Implements a stochastic cycle of environmental events (famine, drought,
abundance, mild shortage) that modify food_availability and
water_availability over time. Events phase in gradually, persist, and
then expire — with natural regression toward baseline defaults.

All randomness uses DeterministicRNG (seeded numpy). No LLM calls.
"""

from shared.constants.defaults import (
    ENV_ABUNDANCE_CHANCE,
    ENV_ABUNDANCE_FOOD_BOOST,
    ENV_ABUNDANCE_WATER_BOOST,
    ENV_CYCLE_MAX_INTERVAL,
    ENV_CYCLE_MIN_INTERVAL,
    ENV_DROUGHT_CHANCE,
    ENV_DROUGHT_DROP,
    ENV_DROUGHT_DURATION,
    ENV_EVENT_PHASE_IN,
    ENV_FAMINE_CHANCE,
    ENV_FAMINE_DROP,
    ENV_FAMINE_DURATION,
    ENV_FOOD_DEFAULT,
    ENV_MILD_DROP_MAX,
    ENV_MILD_DROP_MIN,
    ENV_MILD_DURATION,
    ENV_MILD_SHORTAGE_CHANCE,
    ENV_REGRESSION_RATE,
    ENV_WATER_DEFAULT,
    ENV_NEED_DECAY_FOOD_MULTIPLIER,
    ENV_NEED_DECAY_WATER_MULTIPLIER,
)
from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "update_environmental_cycle",
    "apply_environmental_tick",
    "environmental_effects_on_agents",
]


def _pick_event_type(rng: DeterministicRNG) -> str | None:
    """Randomly pick an event type based on configured probabilities.

    Args:
        rng: Deterministic RNG.

    Returns:
        Event type string (``"famine"``, ``"drought"``, ``"abundance"``,
        ``"mild_shortage"``) or ``None`` if no event occurs (normal).
    """
    roll = rng.random()
    # Order matters: check from most specific to least.
    cumulative = 0.0

    cumulative += ENV_FAMINE_CHANCE
    if roll < cumulative:
        return "famine"

    cumulative += ENV_DROUGHT_CHANCE
    if roll < cumulative:
        return "drought"

    cumulative += ENV_ABUNDANCE_CHANCE
    if roll < cumulative:
        return "abundance"

    cumulative += ENV_MILD_SHORTAGE_CHANCE
    if roll < cumulative:
        return "mild_shortage"

    # Normal (35% default) — no event
    return None


def _build_event_dict(event_type: str, tick_number: int, rng: DeterministicRNG) -> dict:
    """Build an event dictionary for the given event type.

    Args:
        event_type: One of ``"famine"``, ``"drought"``, ``"abundance"``,
            ``"mild_shortage"``.
        tick_number: Current tick number.
        rng: Deterministic RNG (used for randomising severity).

    Returns:
        Event dictionary with keys: type, severity, duration, elapsed,
        phase_in, total_food_effect, total_water_effect, tick_created,
        description.
    """
    event: dict = {
        "type": event_type,
        "tick_created": tick_number,
        "elapsed": 0,
    }

    if event_type == "famine":
        severity = ENV_FAMINE_DROP + rng.uniform(-0.1, 0.1)
        severity = max(0.2, min(0.6, severity))
        event["severity"] = severity
        event["duration"] = ENV_FAMINE_DURATION
        event["phase_in"] = ENV_EVENT_PHASE_IN
        event["total_food_effect"] = -severity
        event["total_water_effect"] = 0.0
        event["description"] = (
            f"Famine: food availability dropping by {severity:.2f} "
            f"over {ENV_EVENT_PHASE_IN} ticks."
        )

    elif event_type == "drought":
        severity = ENV_DROUGHT_DROP + rng.uniform(-0.1, 0.1)
        severity = max(0.2, min(0.6, severity))
        event["severity"] = severity
        event["duration"] = ENV_DROUGHT_DURATION
        event["phase_in"] = ENV_EVENT_PHASE_IN
        event["total_food_effect"] = 0.0
        event["total_water_effect"] = -severity
        event["description"] = (
            f"Drought: water availability dropping by {severity:.2f} "
            f"over {ENV_EVENT_PHASE_IN} ticks."
        )

    elif event_type == "abundance":
        event["severity"] = 0.0
        event["duration"] = 1  # single-tick event
        event["phase_in"] = 1
        event["total_food_effect"] = ENV_ABUNDANCE_FOOD_BOOST
        event["total_water_effect"] = ENV_ABUNDANCE_WATER_BOOST
        event["description"] = (
            f"Abundance: food +{ENV_ABUNDANCE_FOOD_BOOST:.2f}, "
            f"water +{ENV_ABUNDANCE_WATER_BOOST:.2f}."
        )

    elif event_type == "mild_shortage":
        drop = rng.uniform(ENV_MILD_DROP_MIN, ENV_MILD_DROP_MAX)
        event["severity"] = drop
        event["duration"] = ENV_MILD_DURATION
        event["phase_in"] = ENV_MILD_DURATION  # spreads evenly over duration
        event["total_food_effect"] = -drop
        event["total_water_effect"] = -drop
        event["description"] = (
            f"Mild shortage: food/water dropping by {drop:.2f} "
            f"over {ENV_MILD_DURATION} ticks."
        )

    else:
        raise ValueError(f"Unknown event type: {event_type}")

    return event


def _apply_regression(world: SimulationState) -> None:
    """Apply per-tick regression of food and water toward their defaults.

    Both ``food_availability`` and ``water_availability`` move toward
    ``ENV_FOOD_DEFAULT`` and ``ENV_WATER_DEFAULT`` by ``ENV_REGRESSION_RATE``
    per tick.

    Args:
        world: World state (modified in place).
    """
    # Food regression toward 0.85
    diff_food = ENV_FOOD_DEFAULT - world.food_availability
    if abs(diff_food) > 0.001:
        world.food_availability += diff_food * ENV_REGRESSION_RATE

    # Water regression toward 0.90
    diff_water = ENV_WATER_DEFAULT - world.water_availability
    if abs(diff_water) > 0.001:
        world.water_availability += diff_water * ENV_REGRESSION_RATE


def _clamp_availability(world: SimulationState) -> None:
    """Clamp food and water availability to [0.0, 1.0].

    Args:
        world: World state (modified in place).
    """
    world.food_availability = max(0.0, min(1.0, world.food_availability))
    world.water_availability = max(0.0, min(1.0, world.water_availability))


def update_environmental_cycle(
    world: SimulationState,
    tick_number: int,
    rng: DeterministicRNG,
) -> list[dict]:
    """Check if it is time for a new environmental event and generate one.

    An event triggers every ``ENV_CYCLE_MIN_INTERVAL`` to
    ``ENV_CYCLE_MAX_INTERVAL`` ticks. The next trigger tick is set
    when an event is emitted — the countdown resets.

    The tick count since last event is stored in ``world.metadata`` under
    ``"ticks_since_env_event"``. When the count reaches or exceeds the
    interval, a new event may roll based on configured probabilities.

    Args:
        world: World state (modified in place only if regression applies).
        tick_number: Current tick number.
        rng: Deterministic RNG.

    Returns:
        List of event dicts for newly triggered events (empty list if none).
    """
    # Retrieve (or initialise) tick count since last event.
    meta: dict = world.metadata
    ticks_since = meta.get("ticks_since_env_event", 0)
    next_interval = meta.get("next_env_event_interval", 0)

    # First call: set the initial interval.
    if next_interval == 0:
        next_interval = rng.integers(ENV_CYCLE_MIN_INTERVAL, ENV_CYCLE_MAX_INTERVAL + 1)
        meta["next_env_event_interval"] = next_interval

    ticks_since += 1
    new_events: list[dict] = []

    if ticks_since >= next_interval:
        # Roll for an event.
        event_type = _pick_event_type(rng)
        if event_type is not None:
            event = _build_event_dict(event_type, tick_number, rng)
            new_events.append(event)

        # Reset the cycle counter and compute next interval.
        meta["ticks_since_env_event"] = 0
        meta["next_env_event_interval"] = rng.integers(
            ENV_CYCLE_MIN_INTERVAL, ENV_CYCLE_MAX_INTERVAL + 1
        )
    else:
        meta["ticks_since_env_event"] = ticks_since

    return new_events


def apply_environmental_tick(
    world: SimulationState,
    tick_number: int,
    rng: DeterministicRNG,
    active_events: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Process active environmental events for one tick.

    For each active event:
      - During phase-in (``elapsed < phase_in``): apply the per-tick
        fraction of the total effect to food/water availability.
      - After phase-in: no additional change from this event.
      - When ``elapsed >= duration``: the event is expired and removed.

    After processing active events, applies regression toward default
    values and calls ``update_environmental_cycle`` to potentially
    trigger new events.

    Args:
        world: World state (modified in place).
        tick_number: Current tick number.
        rng: Deterministic RNG.
        active_events: Current list of active event dicts.

    Returns:
        Tuple of (new_events_this_tick, updated_active_events).
    """
    remaining_events: list[dict] = []

    for event in active_events:
        event["elapsed"] += 1

        if event["elapsed"] <= event.get("phase_in", ENV_EVENT_PHASE_IN):
            # Phase-in: apply fraction of total effect.
            factor = 1.0 / event.get("phase_in", ENV_EVENT_PHASE_IN)
            world.food_availability += event.get("total_food_effect", 0.0) * factor
            world.water_availability += event.get("total_water_effect", 0.0) * factor

        # After phase-in, the effect is already applied cumulatively.
        # No additional per-tick change from this event.

        if event["elapsed"] < event["duration"]:
            remaining_events.append(event)
        # else: event expired — drop it (the cumulative effect remains,
        # and regression will handle recovery).

    # Apply regression toward defaults.
    _apply_regression(world)
    _clamp_availability(world)

    # Check for new events.
    new_events = update_environmental_cycle(world, tick_number, rng)

    return new_events, remaining_events


def environmental_effects_on_agents(
    agent: AgentState,
    world: SimulationState,
    rng: DeterministicRNG,
) -> None:
    """Apply environmental effects on individual agent state each tick.

    Effects:
      - Low food availability (<0.4) increases food decay (handled in
        ``decay_needs`` via availability check — this function applies
        emotional / behaviour modifiers).
      - During famine (active famine event): agents become more desperate
        (``unlust += 0.02``).
      - During abundance (active abundance event): agents are slightly
        happier (``happiness_score += 0.01``).

    The food/water decay multiplier is applied in ``decay_needs`` using
    ``world.food_availability`` and ``world.water_availability`` directly.
    This function handles the emotional / psychological side effects.

    Args:
        agent: The agent to modify (modified in place).
        world: Current world state.
        rng: Deterministic RNG (reserved for future stochastic effects).
    """
    # Check active events for their type — apply emotional modifiers.
    for event in world.active_env_events:
        if event["type"] == "famine":
            # Agents become more desperate during famine.
            agent.unlust = min(1.0, agent.unlust + 0.02)

        elif event["type"] == "abundance":
            # Agents are slightly happier during abundance.
            agent.emotions.happiness_score = min(
                1.0, agent.emotions.happiness_score + 0.01
            )

    # NOTE: Low food/water availability crisis multipliers are applied
    # in needs_calculator.decay_needs() which checks world.food_availability
    # and world.water_availability directly.
