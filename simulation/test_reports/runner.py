"""Simulation runner for batch testing.

Usage: python runner.py <scenario_name> [--seed SEED] [--ticks N] [--agents N]
Outputs JSON to stdout with full metrics per tick.
"""

import sys
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

from collections import defaultdict
from shared.types.enums import ActionType, EmotionType, WealthClass, NeedType
from shared.schemas.simulation_state import SimulationState
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.engine.tick_loop import run_tick

SCENARIOS = {
    "a1_default": {"n_agents": 80, "ticks": 200, "seed": 42},
    "a2_extended": {"n_agents": 80, "ticks": 500, "seed": 42},
    "a3_small": {"n_agents": 30, "ticks": 500, "seed": 100},
    "a4_large": {"n_agents": 200, "ticks": 200, "seed": 200},
    "b1_dictator": {"n_agents": 80, "ticks": 200, "seed": 300, "tax_rate": 0.40, "welfare_enabled": False, "food_availability": 0.70},
    "b2_utopian": {"n_agents": 80, "ticks": 200, "seed": 400, "tax_rate": 0.15, "welfare_enabled": True, "welfare_amount": 15.0, "food_availability": 1.0},
    "b3_laissez_faire": {"n_agents": 80, "ticks": 200, "seed": 500, "tax_rate": 0.02, "welfare_enabled": False, "food_availability": 0.80},
    "b4_welfare_state": {"n_agents": 80, "ticks": 200, "seed": 600, "tax_rate": 0.25, "welfare_enabled": True, "welfare_amount": 12.0, "food_availability": 0.90},
    "c1_famine": {"n_agents": 80, "ticks": 200, "seed": 700, "food_availability": 0.15, "water_availability": 0.20},
    "c2_drought": {"n_agents": 80, "ticks": 200, "seed": 800, "food_availability": 0.30, "water_availability": 0.15, "unemployment_rate": 0.30, "crime_rate": 0.10},
    "c3_abundance": {"n_agents": 80, "ticks": 200, "seed": 900, "food_availability": 1.0, "water_availability": 1.0, "unemployment_rate": 0.02, "crime_rate": 0.01},
    "c4_high_crime": {"n_agents": 80, "ticks": 200, "seed": 1000, "food_availability": 0.80, "water_availability": 0.80, "crime_rate": 0.30},
    "c5_unstable": {"n_agents": 80, "ticks": 200, "seed": 1100, "food_availability": 0.50, "water_availability": 0.50, "unemployment_rate": 0.50, "crime_rate": 0.25},
    "d1_all_poor": {"n_agents": 80, "ticks": 200, "seed": 1200, "wealth_split": [1.0, 0.0, 0.0]},
    "d2_all_rich": {"n_agents": 80, "ticks": 200, "seed": 1300, "wealth_split": [0.0, 0.0, 1.0]},
    "d3_high_morality": {"n_agents": 80, "ticks": 200, "seed": 1400, "trait_override": {"morality": {"a": 8, "b": 2}}},
    "d4_low_morality": {"n_agents": 80, "ticks": 200, "seed": 1500, "trait_override": {"morality": {"a": 2, "b": 8}}},
    "d5_high_anger": {"n_agents": 80, "ticks": 200, "seed": 1600, "trait_override": {"anger_tendency": {"a": 8, "b": 2}}},
    "e1_zero_tax": {"n_agents": 80, "ticks": 200, "seed": 1700, "tax_rate": 0.0},
    "e2_max_welfare": {"n_agents": 80, "ticks": 200, "seed": 1800, "welfare_enabled": True, "welfare_amount": 50.0},
    "e3_huge_food_cost": {"n_agents": 80, "ticks": 200, "seed": 1900, "food_cost_multiplier": 10.0},
    "e4_sparse": {"n_agents": 50, "ticks": 200, "seed": 2000, "grid_size": 50},
    "e5_dense": {"n_agents": 80, "ticks": 200, "seed": 2100, "grid_size": 5},
    "f1_tax_cut": {"n_agents": 80, "ticks": 200, "seed": 2200, "tax_rate": 0.40, "mid_change": {"tick": 100, "tax_rate": 0.15}},
    "f2_welfare_intro": {"n_agents": 80, "ticks": 200, "seed": 2300, "welfare_enabled": False, "mid_change": {"tick": 100, "welfare_enabled": True, "welfare_amount": 15.0}},
    "f3_police": {"n_agents": 80, "ticks": 200, "seed": 2400, "enact_at_tick": 50, "policy_type": "police"},
    "g1_with_ai": {"n_agents": 80, "ticks": 200, "seed": 2500, "use_ai": True},
    "g2_no_ai": {"n_agents": 80, "ticks": 200, "seed": 2500, "use_ai": False},
    "h1_random": {"n_agents": 80, "ticks": 200, "seed": 2600, "randomize": True, "runs": 10},
}

DEFAULTS = {
    "n_agents": 80,
    "ticks": 200,
    "seed": 42,
    "tax_rate": 0.20,
    "welfare_enabled": False,
    "welfare_amount": 8.0,
    "food_availability": 0.85,
    "water_availability": 0.90,
    "unemployment_rate": 0.10,
    "crime_rate": 0.05,
    "food_cost_multiplier": 1.0,
    "grid_size": 20,
    "wealth_split": None,
    "trait_override": None,
    "use_ai": False,
    "mid_change": None,
    "randomize": False,
    "runs": 1,
    "enact_at_tick": None,
    "policy_type": None,
}


def build_world(**overrides):
    cfg = {**DEFAULTS, **overrides}

    world = SimulationState(
        time_step=0,
        population=cfg["n_agents"],
        economic_health=0.5,
        social_cohesion=0.5,
        environmental_quality=0.8,
        public_order=0.7,
        innovation_index=0.3,
        unlust=0.3,
        morality=0.6,
        food_availability=cfg["food_availability"],
        water_availability=cfg["water_availability"],
        crime_rate=cfg["crime_rate"],
        protest_intensity=0.0,
        unemployment_rate=cfg["unemployment_rate"],
        tax_rate=cfg["tax_rate"],
        welfare_enabled=cfg["welfare_enabled"],
        welfare_amount=cfg["welfare_amount"],
    )
    return world


def run_scenario(name):
    from simulation.agents.agent_factory import create_initial_population
    from simulation.engine.mock_ai_router import MockAIRouter
    from simulation.scheduler.tick_scheduler import TickScheduler

    cfg = {**DEFAULTS, **SCENARIOS.get(name, {})}

    seed = cfg["seed"]
    n_agents = cfg["n_agents"]
    n_ticks = cfg["ticks"]
    use_ai = cfg["use_ai"]
    mid_change = cfg["mid_change"]
    randomize = cfg["randomize"]
    n_runs = cfg["runs"]
    grid_size = cfg.get("grid_size", 20)
    food_cost_multiplier = cfg.get("food_cost_multiplier", 1.0)

    results_all = []

    for run_idx in range(n_runs):
        run_seed = seed + run_idx * 1000
        rng = DeterministicRNG(run_seed)

        world = build_world(**cfg)

        agents = create_initial_population(n_agents, rng)

        ai_router = MockAIRouter() if use_ai else None

        all_ticks = []
        total_crimes = 0
        total_deaths = 0
        total_protests = 0
        total_actions = {a: 0 for a in ActionType}
        per_tick_stats = []
        tick_states = []

        for tick in range(n_ticks):
            if mid_change and tick >= mid_change["tick"]:
                for key, value in mid_change.items():
                    if key != "tick":
                        setattr(world, key, value)

            result = run_tick(tick, agents, world, rng, policies=[], ai_router=ai_router)

            living = [a for a in agents if a.is_alive]
            dead = len(agents) - len(living)

            for ar in result.agent_actions:
                action = ar.action
                if isinstance(action, str):
                    try:
                        action = ActionType(action)
                    except ValueError:
                        action = ActionType.IDLE
                total_actions[action] = total_actions.get(action, 0) + 1

            total_crimes = sum(a.crimes_committed for a in agents)
            total_protests = sum(a.protest_count for a in agents)
            total_deaths = sum(1 for a in agents if not a.is_alive)

            stats = {
                "tick": tick,
                "alive": len(living),
                "dead": total_deaths,
                "total_crimes": total_crimes,
                "total_protests": total_protests,
                "avg_happiness": sum(a.emotions.happiness_score for a in living) / max(1, len(living)),
                "avg_unlust": sum(a.unlust for a in living) / max(1, len(living)),
                "unemployment_rate": sum(1 for a in living if not a.resources.employed) / max(1, len(living)),
                "crime_rate": world.crime_rate,
                "protest_intensity": world.protest_intensity,
                "food_availability": world.food_availability,
                "llm_calls": result.ai_calls,
                "ambiguity_count": result.ambiguity_count,
            }
            per_tick_stats.append(stats)

            if len(living) == 0:
                break

        living_end = [a for a in agents if a.is_alive]
        emotion_counts = defaultdict(int)
        wealth_counts = defaultdict(int)
        for a in agents:
            if a.is_alive:
                emotion_counts[a.emotions.primary.value] += 1
                wealth_counts[a.wealth_class.value] += 1

        run_data = {
            "scenario": name,
            "run": run_idx,
            "seed": run_seed,
            "config": cfg,
            "final_tick": n_ticks,
            "final_population": len(living_end),
            "total_deaths": total_deaths,
            "total_crimes": total_crimes,
            "total_protests": total_protests,
            "total_actions": total_actions,
            "emotion_distribution": dict(emotion_counts),
            "wealth_distribution": dict(wealth_counts),
            "per_tick_stats": per_tick_stats,
        }
        results_all.append(run_data)

    return results_all


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "a1_default"
    results = run_scenario(name)
    json.dump(results, sys.stdout, indent=2, default=str)


if __name__ == "__main__":
    main()
