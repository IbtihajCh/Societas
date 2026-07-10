"""Morality engine — fraud detection and processing for white-collar crime."""

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.types.enums import NeedType
from shared.utilities.deterministic_rng import DeterministicRNG
from shared.constants.defaults import (
    FRAUD_MIN_WEALTH,
    FRAUD_MORALITY_MAX,
    FRAUD_GAIN_MIN,
    FRAUD_GAIN_MAX,
    FRAUD_FINE_MULTIPLIER,
    FRAUD_NOTORIETY_GAIN,
)


def detect_fraud(agent: AgentState, world: SimulationState, rng: DeterministicRNG) -> bool:
    """Detect whether a rich agent's fraud is discovered.

    Rich agents (wealth > 200) with morality < 0.3 AND notoriety < 0.1
    may commit white-collar crime. Detection chance = 1 - risk_tolerance * 0.3.

    Returns True if detected (crime discovered).
    """
    detection_chance = 1.0 - agent.traits.risk_tolerance * 0.3
    return rng.random() < detection_chance


def process_fraud(agent: AgentState, detected: bool, all_agents: list[AgentState], rng: DeterministicRNG) -> float:
    """Process the outcome of a fraud attempt.

    If detected: -0.2 notoriety, -0.1 reputation, fine = money_delta * 0.5.
    If undetected: +0.2 to notoriety.

    Returns money delta.
    """
    money_delta = rng.uniform(FRAUD_GAIN_MIN, FRAUD_GAIN_MAX)
    if detected:
        agent.notoriety = max(0.0, agent.notoriety - 0.2)
        rep = agent.needs.get_level(NeedType.REPUTATION)
        agent.needs.set_level(NeedType.REPUTATION, rep - 0.1)
        fine = money_delta * FRAUD_FINE_MULTIPLIER
        agent.resources.money -= fine
        agent.resources.wealth = agent.resources.money
    else:
        agent.notoriety = min(1.0, agent.notoriety + FRAUD_NOTORIETY_GAIN)
    agent.resources.money += money_delta
    agent.resources.wealth = agent.resources.money
    return money_delta
