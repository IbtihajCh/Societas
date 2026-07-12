"""Parameter sweep runner for SOCIETAS.

Varies simulation constants across configured ranges, re-patches all
importing modules at runtime, runs deterministic simulations, collects
per-value metrics, and generates markdown reports.

Usage:
    python sweep_runner.py                          # run all sweep groups
    python sweep_runner.py needs                    # run a specific group
    python sweep_runner.py FOOD_DECAY_RATE 0.01 0.1 # single param sweep
"""

import ast
import json
import os
import sys
import time
from collections import defaultdict
from copy import deepcopy
from typing import Any, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

from shared.types.enums import ActionType, EmotionType, WealthClass
from shared.schemas.simulation_state import SimulationState
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.engine.tick_loop import run_tick
from simulation.agents.agent_factory import create_initial_population
from simulation.world.property_market import assign_initial_housing


def compute_wealth_gini(agents) -> float:
    """Compute Gini coefficient of wealth distribution across living agents."""
    money_values = sorted(
        getattr(a.resources, "money", 0.0)
        for a in agents
        if getattr(a, "is_alive", True)
    )
    n = len(money_values)
    if n < 2:
        return 0.0
    total = sum(money_values)
    if total <= 0.0:
        return 0.0
    cumulative = 0.0
    weighted_diff = 0.0
    for i, m in enumerate(money_values, start=1):
        weighted_diff += (2 * i - n - 1) * m
    return weighted_diff / (n * total)


# ---------------------------------------------------------------------------
# Patch table: for each constant, every module that imports it
# Maps  module_path -> [const_name, ...]
# ---------------------------------------------------------------------------
_PATCH_MODULES: dict[str, list[str]] = {
    "simulation.agents.adler_engine": [
        "ADLER_DOMINANCE_CHANGE_PER_GAP", "ADLER_GAP_THRESHOLD",
        "ADLER_INFERIORITY_GAIN_PER_GAP", "ADLER_SELF_ESTEEM_CHANGE_PER_GAP",
        "ADLER_SUPERIORITY_GAIN", "ADLER_UNLUST_CHANGE_PER_GAP",
    ],
    "simulation.agents.decision_engine": [
        "ANGRY_UNLUST_THRESHOLD", "BASE_FOOD_COST", "DESPAIR_UNLUST_THRESHOLD",
        "MORAL_DILEMMA_FOOD_THRESHOLD", "MORAL_DILEMMA_MORALITY_THRESHOLD",
        "MORAL_DILEMMA_UNLUST_THRESHOLD", "SCARCITY_BASE",
    ],
    "simulation.agents.emotion_engine": [
        "ANGRY_TENDENCY_THRESHOLD", "ANGRY_TIMER", "ANGRY_UNLUST_THRESHOLD",
        "DESPAIR_TIMER", "DESPAIR_UNLUST_THRESHOLD",
        "HAPPINESS_EMPLOYED_BONUS", "HAPPINESS_FINANCIAL_WEIGHT",
        "HAPPINESS_FOOD_WEIGHT", "HAPPINESS_HEALTH_WEIGHT",
        "HAPPINESS_REPUTATION_WEIGHT", "HAPPINESS_SAFETY_WEIGHT",
        "HAPPINESS_SELF_ESTEEM_WEIGHT", "HAPPINESS_SLEEP_WEIGHT",
        "HAPPINESS_SOCIAL_WEIGHT", "HAPPINESS_UNLUST_WEIGHT",
        "HAPPINESS_WATER_WEIGHT", "HAPPY_THRESHOLD", "SAD_THRESHOLD",
        "SAD_TIMER", "SLEEP_HALF_TIMER_THRESHOLD", "SLEEP_RESET_THRESHOLD",
    ],
    "simulation.agents.unlust_engine": [
        "ANGRY_UNLUST_THRESHOLD", "DESPAIR_UNLUST_THRESHOLD",
        "UNLUST_FINANCIAL_DIVISOR", "UNLUST_FINANCIAL_WEIGHT",
        "UNLUST_FOOD_WEIGHT", "UNLUST_MORALITY_GATE",
        "UNLUST_NEED_THRESHOLD", "UNLUST_SAFETY_WEIGHT",
        "UNLUST_SOCIAL_WEIGHT", "UNLUST_WATER_WEIGHT",
    ],
    "simulation.agents.needs_calculator": [
        "AGE_MORTALITY_BASE", "AGE_MORTALITY_ELDERLY", "AGE_PROGRESSION_INTERVAL",
        "DESPAIR_MORTALITY_RATE", "ECONOMIC_HARDSHIP_DEATH_RATE",
        "ENV_NEED_DECAY_FOOD_MULTIPLIER", "ENV_NEED_DECAY_WATER_MULTIPLIER",
        "FAMILY_DECAY_RATE", "FOOD_DEATH_THRESHOLD", "FOOD_DECAY_RATE",
        "HEALTH_DEATH_THRESHOLD", "INSOMNIA_DECAY_RATE", "INSOMNIA_INCREASE_RATE",
        "INSOMNIA_MAX", "INSOMNIA_SAFETY_THRESHOLD", "INSOMNIA_STRESS_THRESHOLD",
        "JOB_LOSS_RATE", "JOB_LOSS_ECON_SENSITIVITY", "REPUTATION_DECAY_RATE",
        "ROMANTIC_DECAY_RATE", "SAFETY_DECAY_RATE", "SCARCITY_BASE",
        "SELF_ESTEEM_DECAY_RATE", "SEXUAL_TENSION_GROWTH_RATE",
        "SLEEP_DEATH_THRESHOLD", "SLEEP_DECAY_RATE", "SLEEP_RECOVERY_NATURAL",
        "SOCIAL_DECAY_RATE", "UNLUST_FINANCIAL_DIVISOR",
        "WATER_DEATH_THRESHOLD", "WATER_DECAY_RATE",
    ],
    "simulation.agents.action_executor": [
        "BASE_FOOD_COST", "SCARCITY_BASE", "SEEK_JOB_BASE_CHANCE",
        "BEG_MAX_AMOUNT", "STEAL_PERCENTAGE_CAP", "STEAL_AMOUNT_CAP",
        "SHARE_PERCENTAGE", "REPUTATION_CHANGE_GOOD", "REPUTATION_CHANGE_CRIMINAL",
        "SALARY_MULTIPLIER_POOR", "SALARY_MULTIPLIER_MIDDLE",
        "SALARY_MULTIPLIER_RICH", "FOOD_COST_MULTIPLIER_POOR",
        "FOOD_COST_MULTIPLIER_MIDDLE", "FOOD_COST_MULTIPLIER_RICH",
        "SLEEP_RECOVERY_REST", "RUMOR_DOMINANCE_THRESHOLD",
        "RUMOR_MAGNITUDE_MIN", "RUMOR_MAGNITUDE_MAX",
        "GRID_SIZE", "INTERACTION_RADIUS",
    ],
    "simulation.agents.agent_factory": [
        "GRID_SIZE",
    ],
    "simulation.agents.lifecycle": [
        "BIRTH_CHANCE_BASE", "DEATH_INHERITANCE_FRACTION", "GRID_SIZE",
        "MAX_REPRODUCTION_AGE", "MIN_ADULT_AGE_FOR_BIRTH",
    ],
    "simulation.agents.community_system": [
        "COMMUNITY_MAX_SIZE", "COMMUNITY_MIN_SIZE",
        "LEADER_REPUTATION_GAIN", "LEADER_SAFETY_BONUS",
    ],
    "simulation.agents.family_system": [
        "GRID_SIZE", "MARRIAGE_AGE_MAX", "MARRIAGE_AGE_MIN",
        "MARRIAGE_BASE_PROBABILITY", "MARRIAGE_GRID_PROXIMITY",
        "MARRIAGE_MAX_AGE_GAP", "MARRIAGE_WEALTH_COMPAT",
    ],
    "simulation.agents.family_support": [
        "CHILD_ELDERLY_SUPPORT", "PARENT_EDUCATION_SUPPORT",
        "SUPPORT_FAMILY_EDUCATION_AGE_MAX", "SUPPORT_FAMILY_PARENT_AGE_MIN",
        "SUPPORT_FAMILY_PROBABILITY", "SUPPORT_FAMILY_UNLUST_RELIEF",
    ],
    "simulation.agents.gang_system": [
        "GANG_EXTORT_AMOUNT", "GANG_FORMATION_MIN_MEMBERS",
        "GANG_FORMATION_PROBABILITY", "GANG_MAX_NAME_LENGTH",
        "GANG_POWER_MEMBER_WEIGHT", "GANG_POWER_WEALTH_WEIGHT",
        "GANG_RECRUIT_BASE_CHANCE", "GRID_SIZE", "INTERACTION_RADIUS",
    ],
    "simulation.agents.purpose_system": [
        "EXISTENTIAL_DEATH_CHANCE", "PURPOSE_ASSIGN_CHANCE",
        "PURPOSE_DESPAIR_RISK", "PURPOSE_FULFILLMENT_DECAY",
        "PURPOSE_FULFILLMENT_GAIN", "PURPOSE_HAPPINESS_BONUS",
    ],
    "simulation.agents.reputation_system": [
        "GOSSIP_SPREAD_CHANCE", "REPUTATION_CRIME_PENALTY",
        "REPUTATION_DECAY_RATE", "REPUTATION_GOOD_BONUS",
        "REPUTATION_KNOWN_DECAY", "RUMOR_BFS_DEPTH",
        "RUMOR_PROPAGATION_CHANCE",
    ],
    "simulation.agents.sibling_system": [
        "SIBLING_AFFECT_UNLUST_WEIGHT", "SIBLING_BOND_DECREASE_RATE",
        "SIBLING_BOND_INCREASE_RATE", "SIBLING_JEALOUSY_DECAY_RATE",
        "SIBLING_JEALOUSY_SUCCESS_WEIGHT", "SIBLING_JEALOUSY_WEALTH_WEIGHT",
        "SIBLING_SUPPORT_PROBABILITY",
    ],
    "simulation.agents.morality_engine": [
        "FRAUD_MIN_WEALTH", "FRAUD_MORALITY_MAX", "FRAUD_GAIN_MIN",
        "FRAUD_GAIN_MAX", "FRAUD_FINE_MULTIPLIER", "FRAUD_NOTORIETY_GAIN",
    ],
    "simulation.world.grid": [
        "GRID_SIZE", "INTERACTION_RADIUS",
    ],
    "simulation.world.economy": [
        "DEFAULT_WELFARE_AMOUNT", "DEBT_INTEREST_RATE",
    ],
    "simulation.world.environmental_events": [
        "ENV_ABUNDANCE_CHANCE", "ENV_ABUNDANCE_FOOD_BOOST",
        "ENV_ABUNDANCE_WATER_BOOST", "ENV_CYCLE_MAX_INTERVAL",
        "ENV_CYCLE_MIN_INTERVAL", "ENV_DROUGHT_CHANCE", "ENV_DROUGHT_DROP",
        "ENV_DROUGHT_DURATION", "ENV_EVENT_PHASE_IN", "ENV_FAMINE_CHANCE",
        "ENV_FAMINE_DROP", "ENV_FAMINE_DURATION", "ENV_FOOD_DEFAULT",
        "ENV_MILD_DROP_MAX", "ENV_MILD_DROP_MIN", "ENV_MILD_DURATION",
        "ENV_MILD_SHORTAGE_CHANCE", "ENV_REGRESSION_RATE", "ENV_WATER_DEFAULT",
        "ENV_NEED_DECAY_FOOD_MULTIPLIER", "ENV_NEED_DECAY_WATER_MULTIPLIER",
    ],
    "simulation.events.riot_events": [
        "RIOT_FOOD_THRESHOLD", "RIOT_JOIN_CHANCE", "RIOT_PROTEST_THRESHOLD",
        "RIOT_UNLUST_THRESHOLD",
    ],
    "simulation.events.inter_community_conflict": [
        "CONFLICT_GANG_RECRUIT_THRESHOLD", "CONFLICT_HATE_CRIME_THRESHOLD",
        "CONFLICT_PROPERTY_DAMAGE_THRESHOLD", "GRID_SIZE",
        "TENSION_BASE_DECAY", "TENSION_PROXIMITY_WEIGHT",
        "TENSION_WEALTH_GAP_WEIGHT",
    ],
    "simulation.engine.config": [
        "DEFAULT_POPULATION_SIZE", "DEFAULT_SIMULATION_SEED",
        "DEFAULT_TICK_RATE_MS", "DEFAULT_MAX_TICKS",
        "DEFAULT_AGENT_LIFESPAN_TICKS", "DEFAULT_INITIAL_WEALTH",
        "DEFAULT_AMBIGUITY_THRESHOLD",
    ],
    "simulation.engine.mock_ai_router": [
        "BASE_FOOD_COST", "SCARCITY_BASE",
    ],
    "simulation.engine.vllm_router": [
        "BASE_FOOD_COST", "SCARCITY_BASE",
    ],
    "shared.schemas.agent_state": [
        "AGE_CHILD_MAX", "AGE_YOUNG_ADULT_MAX", "AGE_MIDDLE_ADULT_MAX",
        "AGE_ELDERLY_MAX",
    ],
}

_REVERSE_PATCH: dict[str, list[str]] = {}
for mod, consts in _PATCH_MODULES.items():
    for c in consts:
        _REVERSE_PATCH.setdefault(c, []).append(mod)

_CONSTANT_CACHE: dict[str, Any] = {}


def _cache_originals() -> None:
    """Snapshot current values from the source defaults module."""
    from shared.constants import defaults
    for const_name in _REVERSE_PATCH:
        _CONSTANT_CACHE[const_name] = getattr(defaults, const_name, None)


def _patch_constant(name: str, value: Any) -> None:
    """Set ``name`` to ``value`` in every module that imports it."""
    for mod_path in _REVERSE_PATCH.get(name, []):
        try:
            mod = __import__(mod_path, fromlist=[""])
            setattr(mod, name, value)
        except (ImportError, AttributeError):
            pass
    # Also patch the source defaults module so future imports see the value.
    try:
        from shared.constants import defaults
        setattr(defaults, name, value)
    except (ImportError, AttributeError):
        pass


def _restore_all() -> None:
    """Restore all patched constants to their original values."""
    for name, val in _CONSTANT_CACHE.items():
        _patch_constant(name, val)


# ---------------------------------------------------------------------------
# Sweep groups
# ---------------------------------------------------------------------------
NEEDS_SWEEP = [
    ("FOOD_DECAY_RATE", [0.01, 0.02, 0.04, 0.06, 0.10, 0.15]),
    ("WATER_DECAY_RATE", [0.01, 0.02, 0.04, 0.06, 0.10, 0.15]),
    ("SAFETY_DECAY_RATE", [0.005, 0.01, 0.02, 0.04, 0.08]),
    ("SOCIAL_DECAY_RATE", [0.005, 0.01, 0.02, 0.04, 0.08]),
    ("FOOD_DEATH_THRESHOLD", [0.01, 0.03, 0.05, 0.08, 0.12]),
    ("WATER_DEATH_THRESHOLD", [0.01, 0.03, 0.05, 0.08, 0.12]),
    ("SCARCITY_BASE", [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]),
]

UNLUST_SWEEP = [
    ("UNLUST_FOOD_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("UNLUST_WATER_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("UNLUST_FINANCIAL_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("UNLUST_SAFETY_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("UNLUST_SOCIAL_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("UNLUST_FINANCIAL_DIVISOR", [50, 100, 200, 500, 1000]),
    ("DESPAIR_UNLUST_THRESHOLD", [0.6, 0.7, 0.8, 0.9, 0.95]),
    ("ANGRY_UNLUST_THRESHOLD", [0.4, 0.5, 0.6, 0.7, 0.8]),
]

EMOTION_SWEEP = [
    ("HAPPINESS_FOOD_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPINESS_FINANCIAL_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPINESS_SOCIAL_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPINESS_SAFETY_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPINESS_HEALTH_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPINESS_UNLUST_WEIGHT", [0.10, 0.20, 0.35, 0.50, 0.65]),
    ("HAPPINESS_SELF_ESTEEM_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPINESS_SLEEP_WEIGHT", [0.02, 0.05, 0.10, 0.20, 0.30]),
    ("HAPPINESS_REPUTATION_WEIGHT", [0.02, 0.05, 0.10, 0.20, 0.30]),
    ("HAPPINESS_WATER_WEIGHT", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("HAPPY_THRESHOLD", [0.5, 0.6, 0.7, 0.8, 0.9]),
    ("SAD_THRESHOLD", [0.2, 0.3, 0.4, 0.5, 0.6]),
    ("HAPPINESS_EMPLOYED_BONUS", [0.0, 0.05, 0.10, 0.20, 0.30]),
]

ECONOMY_SWEEP = [
    ("BASE_FOOD_COST", [1.0, 2.0, 3.0, 5.0, 8.0, 12.0]),
    ("SALARY_MULTIPLIER_POOR", [0.5, 0.8, 1.0, 1.2, 1.5]),
    ("SALARY_MULTIPLIER_MIDDLE", [0.5, 0.8, 1.0, 1.2, 1.5]),
    ("SALARY_MULTIPLIER_RICH", [0.5, 0.8, 1.0, 1.2, 1.5]),
    ("FOOD_COST_MULTIPLIER_POOR", [0.5, 1.0, 1.5, 2.0, 3.0]),
    ("FOOD_COST_MULTIPLIER_MIDDLE", [0.5, 1.0, 1.5, 2.0, 3.0]),
    ("FOOD_COST_MULTIPLIER_RICH", [0.5, 1.0, 1.5, 2.0, 3.0]),
    ("DEFAULT_WELFARE_AMOUNT", [2.0, 5.0, 8.0, 12.0, 20.0]),
    ("DEBT_INTEREST_RATE", [0.01, 0.03, 0.05, 0.10, 0.20]),
]

DEATH_SWEEP = [
    ("AGE_MORTALITY_BASE", [0.0, 0.001, 0.005, 0.01, 0.02]),
    ("AGE_MORTALITY_ELDERLY", [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]),
    ("DESPAIR_MORTALITY_RATE", [0.0, 0.005, 0.01, 0.02, 0.05]),
    ("ECONOMIC_HARDSHIP_DEATH_RATE", [0.0, 0.001, 0.005, 0.01, 0.02]),
    ("FOOD_DEATH_THRESHOLD", [0.01, 0.03, 0.05, 0.08, 0.12]),
    ("WATER_DEATH_THRESHOLD", [0.01, 0.03, 0.05, 0.08, 0.12]),
    ("HEALTH_DEATH_THRESHOLD", [0.01, 0.03, 0.05, 0.08, 0.12]),
    ("SLEEP_DEATH_THRESHOLD", [0.01, 0.03, 0.05, 0.08, 0.12]),
    ("EXISTENTIAL_DEATH_CHANCE", [0.0, 0.001, 0.005, 0.01, 0.02]),
]

ACTIONS_SWEEP = [
    ("STEAL_PERCENTAGE_CAP", [0.1, 0.2, 0.3, 0.5, 0.75]),
    ("STEAL_AMOUNT_CAP", [20, 50, 100, 200, 500]),
    ("SHARE_PERCENTAGE", [0.05, 0.10, 0.20, 0.35, 0.50]),
    ("BEG_MAX_AMOUNT", [1.0, 2.0, 5.0, 10.0, 20.0]),
    ("SEEK_JOB_BASE_CHANCE", [0.1, 0.3, 0.5, 0.7, 1.0]),
    ("REPUTATION_CHANGE_GOOD", [0.01, 0.03, 0.05, 0.10, 0.20]),
    ("REPUTATION_CHANGE_CRIMINAL", [0.02, 0.05, 0.08, 0.15, 0.25]),
]

SOCIAL_SWEEP = [
    ("COMMUNITY_MAX_SIZE", [10, 20, 50, 100]),
    ("COMMUNITY_MIN_SIZE", [2, 3, 5, 10]),
    ("GOSSIP_SPREAD_CHANCE", [0.1, 0.3, 0.5, 0.7, 0.9]),
    ("REPUTATION_DECAY_RATE", [0.001, 0.005, 0.01, 0.02, 0.05]),
    ("MARRIAGE_BASE_PROBABILITY", [0.01, 0.03, 0.05, 0.10, 0.20]),
    ("BIRTH_CHANCE_BASE", [0.01, 0.03, 0.05, 0.10, 0.20]),
    ("RIOT_PROTEST_THRESHOLD", [0.1, 0.2, 0.3, 0.5, 0.7]),
    ("RIOT_JOIN_CHANCE", [0.1, 0.2, 0.3, 0.5, 0.7]),
]

LIFECYCLE_SWEEP = [
    ("AGE_PROGRESSION_INTERVAL", [0.01, 0.025, 0.05, 0.1, 0.2]),
    ("AGE_MORTALITY_BASE", [0.0, 0.001, 0.005, 0.01, 0.02]),
    ("AGE_MORTALITY_ELDERLY", [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]),
    ("MARRIAGE_AGE_MIN", [16, 18, 19, 21, 25]),
    ("MARRIAGE_AGE_MAX", [50, 55, 60, 65, 70]),
    ("BIRTH_CHANCE_BASE", [0.01, 0.03, 0.05, 0.10, 0.20]),
    ("DEATH_INHERITANCE_FRACTION", [0.3, 0.5, 0.7, 0.9, 1.0]),
    ("SUPPORT_FAMILY_PROBABILITY", [0.1, 0.3, 0.5, 0.7, 0.9]),
]

ENVIRONMENT_SWEEP = [
    ("ENV_FAMINE_CHANCE", [0.0, 0.05, 0.10, 0.20, 0.40]),
    ("ENV_DROUGHT_CHANCE", [0.0, 0.05, 0.10, 0.20, 0.40]),
    ("ENV_ABUNDANCE_CHANCE", [0.0, 0.05, 0.10, 0.20, 0.40]),
    ("ENV_FAMINE_DROP", [0.3, 0.5, 0.7, 0.9]),
    ("ENV_DROUGHT_DROP", [0.3, 0.5, 0.7, 0.9]),
    ("ENV_REGRESSION_RATE", [0.01, 0.03, 0.05, 0.10, 0.20]),
    ("ENV_NEED_DECAY_FOOD_MULTIPLIER", [1.0, 1.5, 2.0, 3.0, 5.0]),
    ("ENV_NEED_DECAY_WATER_MULTIPLIER", [1.0, 1.5, 2.0, 3.0, 5.0]),
]

SWEEP_GROUPS: dict[str, list[tuple[str, list]]] = {
    "needs": NEEDS_SWEEP,
    "unlust": UNLUST_SWEEP,
    "emotion": EMOTION_SWEEP,
    "economy": ECONOMY_SWEEP,
    "death": DEATH_SWEEP,
    "actions": ACTIONS_SWEEP,
    "social": SOCIAL_SWEEP,
    "lifecycle": LIFECYCLE_SWEEP,
    "environment": ENVIRONMENT_SWEEP,
}

GROUP_DESCRIPTIONS = {
    "needs": "Need decay rates and death thresholds for all 5 Maslow layers",
    "unlust": "Weights and thresholds that drive the unlust → emotion system",
    "emotion": "Happiness weights, emotion thresholds, state machine timers",
    "economy": "Food costs, salary multipliers, welfare, debt interest",
    "death": "All mortality rates: age, despair, hardship, starvation, thirst, health",
    "actions": "Action parameters: theft caps, share %, beg amounts, job search",
    "social": "Community, reputation, marriage, birth, and riot parameters",
    "lifecycle": "Age progression, mortality, marriage age bounds, family support",
    "environment": "Famine/drought/abundance event probabilities, intensities, regressions",
}


def build_world(**overrides) -> SimulationState:
    cfg = dict(overrides)
    return SimulationState(
        time_step=0,
        population=cfg.get("n_agents", 80),
        economic_health=0.5,
        social_cohesion=0.5,
        environmental_quality=0.8,
        public_order=0.7,
        innovation_index=0.3,
        unlust=0.3,
        morality=0.6,
        food_availability=cfg.get("food_availability", 0.85),
        water_availability=cfg.get("water_availability", 0.90),
        crime_rate=cfg.get("crime_rate", 0.05),
        protest_intensity=0.0,
        unemployment_rate=cfg.get("unemployment_rate", 0.10),
        tax_rate=cfg.get("tax_rate", 0.20),
        welfare_enabled=cfg.get("welfare_enabled", False),
        welfare_amount=cfg.get("welfare_amount", 8.0),
    )


def run_single(
    n_agents: int = 80,
    n_ticks: int = 200,
    seed: int = 42,
) -> dict:
    rng = DeterministicRNG(seed)
    world = build_world()
    agents = create_initial_population(n_agents, rng)
    for agent in agents:
        assign_initial_housing(agent)
    per_tick = []
    total_crimes = 0
    total_protests = 0
    total_deaths = 0
    total_actions: dict = {}

    for tick in range(n_ticks):
        result = run_tick(tick, agents, world, rng, policies=[])
        living = [a for a in agents if a.is_alive]
        total_deaths = sum(1 for a in agents if not a.is_alive)
        total_crimes = sum(getattr(a, "crimes_committed", 0) for a in agents)
        total_protests = sum(getattr(a, "protest_count", 0) for a in agents)

        for ar in result.agent_actions:
            action = ar.action if isinstance(ar.action, str) else str(ar.action)
            total_actions[action] = total_actions.get(action, 0) + 1

        avg_h = sum(a.emotions.happiness_score for a in living) / max(1, len(living))
        avg_u = sum(a.unlust for a in living) / max(1, len(living))
        unemployed = sum(1 for a in living if not getattr(a.resources, "employed", False)) / max(1, len(living))

        # Sample per_tick every 5 ticks (plus tick 0 and final) to keep
        # output size reasonable while preserving full trajectory shape.
        if tick % 5 != 0 and tick != n_ticks - 1 and len(living) > 0:
            pass  # skip detailed per-tick capture
        else:
            per_tick.append({
                "tick": tick, "alive": len(living), "dead": total_deaths,
            "avg_happiness": round(avg_h, 4), "avg_unlust": round(avg_u, 4),
            "avg_unemployment": round(unemployed, 4),
            "crime_rate": world.crime_rate, "protest_intensity": world.protest_intensity,
            "food_availability": world.food_availability,
            "water_availability": world.water_availability,
            "economic_health": round(world.economic_health, 4),
            "social_cohesion": round(world.social_cohesion, 4),
            "environmental_quality": round(world.environmental_quality, 4),
            "public_order": round(world.public_order, 4),
            "innovation_index": round(world.innovation_index, 4),
            "unlust_world": round(world.unlust, 4),
            "morality_world": round(world.morality, 4),
            "national_debt": round(world.national_debt, 4),
            "remittance_income": round(world.remittance_income, 4),
            "energy_price": round(world.energy_price, 4),
            "tax_rate": round(world.tax_rate, 4),
            "unemployment_rate": round(world.unemployment_rate, 4),
            "welfare_enabled": world.welfare_enabled,
            "welfare_amount": round(world.welfare_amount, 4),
            "tax_revenue_pool": round(getattr(world, "tax_revenue_pool", 0.0), 4),
            "salary_multiplier": round(getattr(world, "salary_multiplier", 1.0), 4),
            "active_events": len(getattr(world, "active_events", [])),
            "active_env_events": len(getattr(world, "active_env_events", [])),
            "media_articles": len(world.media_state.get("articles", [])) if isinstance(world.media_state, dict) else 0,
            "media_trust": world.media_state.get("trust_in_media", 0.6) if isinstance(world.media_state, dict) else 0.6,
            "media_sensationalism": world.media_state.get("sensationalism", 0.3) if isinstance(world.media_state, dict) else 0.3,
            "media_fake_news_level": world.media_state.get("fake_news_level", 0.0) if isinstance(world.media_state, dict) else 0.0,
            "media_sentiment_gov": world.media_state.get("sentiment_gov", 0.0) if isinstance(world.media_state, dict) else 0.0,
            "media_sentiment_economy": world.media_state.get("sentiment_economy", 0.0) if isinstance(world.media_state, dict) else 0.0,
            "economy_gdp": round(getattr(world.economy, "gdp", 0.0), 4),
            "economy_inflation": round(getattr(world.economy, "inflation_rate", 0.02), 4),
            "economy_employment": round(getattr(world.economy, "employment_rate", 0.9), 4),
            "economy_consumer_confidence": round(getattr(world.economy, "consumer_confidence", 0.5), 4),
            "economy_market_stability": round(getattr(world.economy, "market_stability", 0.5), 4),
            "economy_tax_revenue": round(getattr(world.economy, "tax_revenue", 0.0), 4),
            "economy_government_spending": round(getattr(world.economy, "government_spending", 0.0), 4),
            "economy_trade_balance": round(getattr(world.economy, "trade_balance", 0.0), 4),
            "crime_overall_rate": round(getattr(world.crime, "overall_crime_rate", 0.05), 4),
            "crime_enforcement": round(getattr(world.crime, "enforcement_effectiveness", 0.7), 4),
            "crime_incarceration": round(getattr(world.crime, "incarceration_rate", 0.01), 4),
            "crime_public_safety": round(getattr(world.crime, "public_safety_index", 0.8), 4),
            "crime_victims": getattr(world.crime, "crime_victims_total", 0),
            "crimes_reported": getattr(world.crime, "crimes_reported", 0),
            "crimes_resolved": getattr(world.crime, "crimes_resolved", 0),
            "psych_morality": round(getattr(world.psychology, "average_morality", 0.5), 4),
            "psych_happiness": round(getattr(world.psychology, "average_happiness", 0.5), 4),
            "psych_stress": round(getattr(world.psychology, "average_stress", 0.3), 4),
            "psych_mental_health": round(getattr(world.psychology, "mental_health_index", 0.5), 4),
            "psych_social_satisfaction": round(getattr(world.psychology, "social_satisfaction", 0.5), 4),
            "psych_life_satisfaction": round(getattr(world.psychology, "life_satisfaction", 0.5), 4),
            "wealth_gini": round(compute_wealth_gini(agents), 4) if len(living) > 1 else 0.0,
        })

        if len(living) == 0:
            break

    living_end = [a for a in agents if a.is_alive]
    emotion_dist = defaultdict(int)
    wealth_dist = defaultdict(int)
    for a in agents:
        if a.is_alive:
            emotion_dist[a.emotions.primary.value] += 1
            wealth_dist[a.wealth_class.value] += 1

    return {
        "final_population": len(living_end),
        "total_deaths": total_deaths,
        "total_crimes": total_crimes,
        "total_protests": total_protests,
        "total_actions": total_actions,
        "emotion_distribution": dict(emotion_dist),
        "wealth_distribution": dict(wealth_dist),
        "final_avg_happiness": per_tick[-1]["avg_happiness"] if per_tick else 0,
        "final_avg_unlust": per_tick[-1]["avg_unlust"] if per_tick else 0,
        "per_tick_stats": per_tick,
    }



def run_sweep(
    param_name: str,
    values: list,
    n_agents: int = 80,
    n_ticks: int = 200,
    seed: int = 42,
) -> list[dict]:
    _cache_originals()
    results = []

    for val in values:
        _patch_constant(param_name, val)
        try:
            result = run_single(n_agents=n_agents, n_ticks=n_ticks, seed=seed)
        except Exception as e:
            result = {"error": str(e)}
        result["param_value"] = val
        results.append(result)

    _restore_all()
    return results


def generate_report(group_name: str, param_name: str, values: list, results: list[dict]) -> str:
    lines = []
    lines.append(f"## Sweep: `{param_name}`")
    lines.append(f"  - Group: `{group_name}`")
    lines.append(f"  - Description: {GROUP_DESCRIPTIONS.get(group_name, '')}")
    lines.append(f"  - Seed: 42, Agents: 80, Ticks: 200")
    lines.append("")

    header = "| Value | Final Pop | Deaths | Crimes | Protests | Happiness | Unlust |"
    sep = "|-------|-----------|--------|--------|----------|-----------|--------|"
    lines.append(header)
    lines.append(sep)

    for r in results:
        v = r["param_value"]
        if "error" in r:
            lines.append(f"| {v} | ERROR: {r['error']} |")
        else:
            lines.append(
                f"| {v} | {r['final_population']} | {r['total_deaths']} | "
                f"{r['total_crimes']} | {r['total_protests']} | "
                f"{r['final_avg_happiness']:.3f} | {r['final_avg_unlust']:.3f} |"
            )

    lines.append("")

    # Verdict
    pops = [r.get("final_population", 0) for r in results if "error" not in r]
    if all(p > 0 for p in pops):
        verdict = "WORKING — all values produce viable simulations"
    elif any(p > 0 for p in pops):
        verdict = "PARTIAL — some values cause total extinction"
    else:
        verdict = "DEAD — all values cause total extinction"

    lines.append(f"**Verdict:** {verdict}")
    lines.append("")
    return "\n".join(lines)


def sweep_group(group_name: str, output_dir: str = ".") -> dict:
    params = SWEEP_GROUPS.get(group_name)
    if not params:
        print(f"Unknown group: {group_name}. Available: {list(SWEEP_GROUPS.keys())}")
        return {}

    print(f"\n{'='*60}")
    print(f"Sweep group: {group_name}")
    print(f"{'='*60}")
    print(f"{GROUP_DESCRIPTIONS.get(group_name, '')}")
    print(f"{'='*60}")
    print()

    group_results = {}
    for param_name, values in params:
        print(f"  Sweeping {param_name}... ", end="", flush=True)
        t0 = time.time()
        results = run_sweep(param_name, values)
        elapsed = time.time() - t0
        print(f"done ({elapsed:.1f}s)")
        group_results[param_name] = results

        report = generate_report(group_name, param_name, values, results)
        safe_name = param_name.lower()
        report_path = os.path.join(output_dir, f"sweep_{group_name}_{safe_name}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        meta_path = os.path.join(output_dir, f"sweep_{group_name}_{safe_name}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"param": param_name, "group": group_name, "values": values, "results": results}, f, indent=2, default=str)

    # Group summary
    summary_lines = [f"# Sweep Summary: {group_name}", "", "| Parameter | Values | Verdict |", "|-----------|--------|---------|"]
    for param_name, values in params:
        results = group_results[param_name]
        pops = [r.get("final_population", 0) for r in results if "error" not in r]
        if not pops:
            verdict = "ERROR"
        elif all(p > 0 for p in pops):
            verdict = "WORKING"
        elif any(p > 0 for p in pops):
            verdict = "PARTIAL"
        else:
            verdict = "DEAD"
        summary_lines.append(f"| {param_name} | {', '.join(str(v) for v in values)} | {verdict} |")

    summary_path = os.path.join(output_dir, f"sweep_{group_name}_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"\nSummary: {summary_path}")

    return group_results


def main():
    # Run from the test_reports directory
    output_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target in SWEEP_GROUPS:
            sweep_group(target, output_dir)
        else:
            # Single param sweep: python sweep_runner.py FOOD_DECAY_RATE 0.01 0.05 0.1
            param_name = target.upper()
            values = [float(v) if "." in v else int(v) for v in sys.argv[2:]]
            if not values:
                print(f"Usage: python sweep_runner.py <group> | <param_name> <val1> <val2> ...")
                sys.exit(1)
            print(f"\nSingle param sweep: {param_name}")
            print(f"Values: {values}")
            print()
            results = run_sweep(param_name, values)
            report = generate_report("custom", param_name, values, results)
            print(report)
            safe = param_name.lower()
            with open(os.path.join(output_dir, f"sweep_custom_{safe}.md"), "w", encoding="utf-8") as f:
                f.write(report)
            with open(os.path.join(output_dir, f"sweep_custom_{safe}.json"), "w", encoding="utf-8") as f:
                json.dump({"param": param_name, "values": values, "results": results}, f, indent=2, default=str)
    else:
        # Run all sweep groups
        print("SOCIETAS Parameter Sweep Runner")
        print("=" * 60)
        for group_name in SWEEP_GROUPS:
            sweep_group(group_name, output_dir)

        print("\nDone.")


if __name__ == "__main__":
    main()
