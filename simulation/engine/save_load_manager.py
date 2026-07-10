import json
import os
import uuid
from datetime import datetime, timezone
from dataclasses import is_dataclass, fields
from typing import List, Tuple
from enum import Enum

import numpy as np

from shared.schemas.agent_state import (
    AgentState,
    AgentTraits,
    AgentNeeds,
    AgentEmotions,
    AgentResources,
    AgentDecisionScores,
)
from shared.schemas.simulation_state import SimulationState
from shared.schemas.economy_state import EconomyState
from shared.schemas.crime_state import CrimeState
from shared.schemas.needs_state import NeedsState
from shared.schemas.psychology_state import PsychologyState
from shared.schemas.save_state import SimulationSaveData, SimulationSaveMetadata
from shared.types.enums import (
    ActionType,
    Culture,
    EducationLevel,
    EmotionType,
    EmploymentStatus,
    Gender,
    JobType,
    NeedType,
    WealthClass,
)
from shared.types.aliases import TickNumber
from shared.utilities.deterministic_rng import DeterministicRNG


def _to_serializable(obj):
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            result[f.name] = _to_serializable(getattr(obj, f.name))
        return result
    if isinstance(obj, dict):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    return obj


def _reconstruct_agent(data):
    traits = AgentTraits(
        morality=float(data.get("traits", {}).get("morality", 0.5)),
        creativity=float(data.get("traits", {}).get("creativity", 0.5)),
        ambition=float(data.get("traits", {}).get("ambition", 0.5)),
        resilience=float(data.get("traits", {}).get("resilience", 0.5)),
        dominance_urge=float(data.get("traits", {}).get("dominance_urge", 0.5)),
        anger_tendency=float(data.get("traits", {}).get("anger_tendency", 0.5)),
        extraversion=float(data.get("traits", {}).get("extraversion", 0.5)),
        risk_tolerance=float(data.get("traits", {}).get("risk_tolerance", 0.5)),
    )

    needs_data = data.get("needs", {})
    needs_levels = {}
    for k, v in needs_data.get("levels", {}).items():
        key = NeedType(k) if isinstance(k, str) else k
        needs_levels[key] = float(v)
    needs = AgentNeeds(levels=needs_levels)

    emotions_data = data.get("emotions", {})
    emotion_intensities = {}
    for k, v in emotions_data.get("intensities", {}).items():
        key = EmotionType(k) if isinstance(k, str) else k
        emotion_intensities[key] = float(v)
    emotions = AgentEmotions(
        primary=EmotionType(emotions_data.get("primary", "normal")),
        intensities=emotion_intensities,
        emotion_timer=int(emotions_data.get("emotion_timer", 0)),
        happiness_score=float(emotions_data.get("happiness_score", 0.5)),
    )

    resources = AgentResources(
        money=float(data.get("resources", {}).get("money", 100.0)),
        base_salary=float(data.get("resources", {}).get("base_salary", 0.0)),
        employed=bool(data.get("resources", {}).get("employed", False)),
        education=EducationLevel(data.get("resources", {}).get("education", 1)),
        property=bool(data.get("resources", {}).get("property", False)),
        property_tier=int(data.get("resources", {}).get("property_tier", 0)),
        property_value=float(data.get("resources", {}).get("property_value", 0.0)),
        rent_cost=float(data.get("resources", {}).get("rent_cost", 0.0)),
        health=float(data.get("resources", {}).get("health", 1.0)),
        wealth=float(data.get("resources", {}).get("wealth", 100.0)),
        assets=list(data.get("resources", {}).get("assets", [])),
        skills=list(data.get("resources", {}).get("skills", [])),
    )

    ds_data = data.get("decision_scores", {})
    ds_scores = {}
    for k, v in ds_data.get("scores", {}).items():
        key = ActionType(k) if isinstance(k, str) else k
        ds_scores[key] = float(v)
    decision_scores = AgentDecisionScores(
        scores=ds_scores,
        top_action=ActionType(ds_data["top_action"]) if ds_data.get("top_action") else None,
        top_score=float(ds_data.get("top_score", 0.0)),
        second_score=float(ds_data.get("second_score", 0.0)),
    )

    return AgentState(
        id=str(data.get("id", "")),
        persona=str(data.get("persona", "")),
        traits=traits,
        needs=needs,
        emotions=emotions,
        resources=resources,
        decision_scores=decision_scores,
        employment_status=EmploymentStatus(data.get("employment_status", 2)),
        wealth_class=WealthClass(data.get("wealth_class", "poor")),
        age=int(data.get("age", 25)),
        age_bracket=str(data.get("age_bracket", "young_adult")),
        cause_of_death=str(data.get("cause_of_death", "")),
        is_alive=bool(data.get("is_alive", True)),
        location=str(data.get("location", "default")),
        social_connections=[str(x) for x in data.get("social_connections", [])],
        metadata=data.get("metadata", {}),
        gender=Gender(data.get("gender", "male")),
        culture=Culture(data.get("culture", "A")),
        born_tick=TickNumber(data.get("born_tick", 0)),
        unlust=float(data.get("unlust", 0.0)),
        good_acts=int(data.get("good_acts", 0)),
        crimes_committed=int(data.get("crimes_committed", 0)),
        notoriety=float(data.get("notoriety", 0.0)),
        trust_in_govt=float(data.get("trust_in_govt", 0.5)),
        protest_count=int(data.get("protest_count", 0)),
        grid_x=int(data.get("grid_x", 0)),
        grid_y=int(data.get("grid_y", 0)),
        job_type=JobType(data.get("job_type", "unemployed")),
        spouse=str(data["spouse"]) if data.get("spouse") else None,
        siblings=[str(x) for x in data.get("siblings", [])],
        sibling_jealousy=float(data.get("sibling_jealousy", 0.0)),
        sibling_bond=float(data.get("sibling_bond", 0.5)),
        family_id=str(data["family_id"]) if data.get("family_id") else None,
        marriage_tick=int(data.get("marriage_tick", 0)),
        partner_preferences={str(k): float(v) for k, v in data.get("partner_preferences", {}).items()},
        enemies=[str(x) for x in data.get("enemies", [])],
        parent_ids=[str(x) for x in data.get("parent_ids", [])],
        children_ids=[str(x) for x in data.get("children_ids", [])],
        support_received=float(data.get("support_received", 0.0)),
        support_given=float(data.get("support_given", 0.0)),
        community_id=str(data["community_id"]) if data.get("community_id") else None,
        last_action=ActionType(data.get("last_action", "idle")),
        last_reasoning=str(data.get("last_reasoning", "")),
        insomnia_severity=float(data.get("insomnia_severity", 0.0)),
        energy=float(data.get("energy", 1.0)),
        last_sleep_tick=int(data.get("last_sleep_tick", 0)),
        ticks_without_sleep=int(data.get("ticks_without_sleep", 0)),
    )


def _reconstruct_world(data):
    economy_data = data.get("economy", {})
    economy = EconomyState(
        gdp=float(economy_data.get("gdp", 0.0)),
        unemployment_rate=float(economy_data.get("unemployment_rate", 0.1)),
        inflation_rate=float(economy_data.get("inflation_rate", 0.02)),
        wealth_distribution={str(k): float(v) for k, v in economy_data.get("wealth_distribution", {}).items()},
        employment_rate=float(economy_data.get("employment_rate", 0.9)),
        consumer_confidence=float(economy_data.get("consumer_confidence", 0.5)),
        market_stability=float(economy_data.get("market_stability", 0.5)),
        tax_revenue=float(economy_data.get("tax_revenue", 0.0)),
        government_spending=float(economy_data.get("government_spending", 0.0)),
        trade_balance=float(economy_data.get("trade_balance", 0.0)),
    )

    crime_data = data.get("crime", {})
    crime = CrimeState(
        overall_crime_rate=float(crime_data.get("overall_crime_rate", 0.05)),
        crime_by_type={str(k): float(v) for k, v in crime_data.get("crime_by_type", {}).items()},
        enforcement_effectiveness=float(crime_data.get("enforcement_effectiveness", 0.7)),
        incarceration_rate=float(crime_data.get("incarceration_rate", 0.01)),
        public_safety_index=float(crime_data.get("public_safety_index", 0.8)),
        crime_victims_total=int(crime_data.get("crime_victims_total", 0)),
        crimes_reported=int(crime_data.get("crimes_reported", 0)),
        crimes_resolved=int(crime_data.get("crimes_resolved", 0)),
    )

    needs_data = data.get("needs", {})
    avg_need_levels = {}
    for k, v in needs_data.get("average_need_levels", {}).items():
        key = NeedType(k) if isinstance(k, str) else k
        avg_need_levels[key] = float(v)
    needs = NeedsState(
        average_need_levels=avg_need_levels,
        fulfillment_rate=float(needs_data.get("fulfillment_rate", 0.5)),
        unmet_needs_count=int(needs_data.get("unmet_needs_count", 0)),
        most_urgent_need=NeedType(needs_data.get("most_urgent_need", "food")),
        need_distribution={str(k): int(v) for k, v in needs_data.get("need_distribution", {}).items()},
    )

    psych_data = data.get("psychology", {})
    emotional_distribution = {}
    for k, v in psych_data.get("emotional_distribution", {}).items():
        key = EmotionType(k) if isinstance(k, str) else k
        emotional_distribution[key] = int(v)
    psychology = PsychologyState(
        average_morality=float(psych_data.get("average_morality", 0.5)),
        average_happiness=float(psych_data.get("average_happiness", 0.5)),
        average_stress=float(psych_data.get("average_stress", 0.3)),
        emotional_distribution=emotional_distribution,
        mental_health_index=float(psych_data.get("mental_health_index", 0.5)),
        social_satisfaction=float(psych_data.get("social_satisfaction", 0.5)),
        life_satisfaction=float(psych_data.get("life_satisfaction", 0.5)),
    )

    return SimulationState(
        time_step=TickNumber(data.get("time_step", 0)),
        population=int(data.get("population", 0)),
        economic_health=float(data.get("economic_health", 0.5)),
        social_cohesion=float(data.get("social_cohesion", 0.5)),
        environmental_quality=float(data.get("environmental_quality", 0.5)),
        public_order=float(data.get("public_order", 0.5)),
        innovation_index=float(data.get("innovation_index", 0.5)),
        unlust=float(data.get("unlust", 0.0)),
        morality=float(data.get("morality", 0.5)),
        economy=economy,
        crime=crime,
        needs=needs,
        psychology=psychology,
        active_policy_ids=list(data.get("active_policy_ids", [])),
        metadata=data.get("metadata", {}),
        food_availability=float(data.get("food_availability", 0.85)),
        water_availability=float(data.get("water_availability", 0.90)),
        crime_rate=float(data.get("crime_rate", 0.05)),
        protest_intensity=float(data.get("protest_intensity", 0.0)),
        unemployment_rate=float(data.get("unemployment_rate", 0.10)),
        tax_rate=float(data.get("tax_rate", 0.15)),
        welfare_enabled=bool(data.get("welfare_enabled", False)),
        welfare_amount=float(data.get("welfare_amount", 8.0)),
        job_demand={str(k): int(v) for k, v in data.get("job_demand", {}).items()},
        job_salary_multipliers={str(k): float(v) for k, v in data.get("job_salary_multipliers", {}).items()},
        active_env_events=list(data.get("active_env_events", [])),
    )


def _capture_rng_state(rng):
    state = dict(rng._rng.bit_generator.state)
    state["_seed"] = rng.seed
    return state


def save_simulation(agents, world, rng, tick_number, filepath) -> str:
    agents_data = [_to_serializable(a) for a in agents]
    world_data = _to_serializable(world)
    rng_state = _capture_rng_state(rng)

    save_data = {
        "agents": agents_data,
        "world": world_data,
        "tick": int(tick_number),
        "rng_state": rng_state,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.2",
    }

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(save_data, f, indent=2)

    return os.path.splitext(os.path.basename(filepath))[0]


def load_simulation(filepath) -> tuple:
    with open(filepath, "r") as f:
        data = json.load(f)

    agents = [_reconstruct_agent(a) for a in data["agents"]]
    world = _reconstruct_world(data["world"])
    tick = int(data.get("tick", 0))
    rng_state = data.get("rng_state", {})

    return agents, world, tick, rng_state


def list_saves(save_dir) -> List[SimulationSaveMetadata]:
    result = []
    if not os.path.isdir(save_dir):
        return result
    for fname in sorted(os.listdir(save_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(save_dir, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            result.append(SimulationSaveMetadata(
                save_id=os.path.splitext(fname)[0],
                tick=int(data.get("tick", 0)),
                population=len(data.get("agents", [])),
                timestamp=str(data.get("timestamp", "")),
                tick_rate=0.0,
            ))
        except (json.JSONDecodeError, OSError):
            continue
    return result


def delete_save(save_id: str, save_dir: str) -> bool:
    fpath = os.path.join(save_dir, f"{save_id}.json")
    if not os.path.isfile(fpath):
        return False
    os.remove(fpath)
    return True
