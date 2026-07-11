"""Birth and inheritance lifecycle events for agents.

Provides ``try_birth`` for creating new agents during a simulation tick,
including financial inheritance and age-appropriate initialisation.
"""

from typing import Optional

from shared.constants.defaults import (
    BIRTH_CHANCE_BASE,
    DEATH_INHERITANCE_FRACTION,
    GRID_SIZE,
    MAX_REPRODUCTION_AGE,
    MIN_ADULT_AGE_FOR_BIRTH,
)
from shared.constants.simulation_constants import BETA_PARAMS
from shared.schemas.agent_state import (
    AgentEmotions,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
    get_age_bracket,
)
from shared.types.aliases import AgentId, TickNumber
from shared.types.enums import (
    ActionType,
    Culture,
    EducationLevel,
    EmploymentStatus,
    Gender,
    JobType,
    NeedType,
    WealthClass,
)
from shared.utilities.deterministic_rng import DeterministicRNG

__all__ = [
    "try_birth",
]


def _generate_traits(rng: DeterministicRNG) -> AgentTraits:
    """Generate Beta-distributed traits for a newborn agent.

    Same distribution as the main agent factory:

    - All traits default to Beta(2, 2) except anger_tendency which uses
      Beta(2, 3) (skewed low).

    Args:
        rng: Deterministic RNG instance.

    Returns:
        AgentTraits with Beta-distributed values.
    """
    return AgentTraits(
        creativity=rng.beta(BETA_PARAMS["creativity"][0], BETA_PARAMS["creativity"][1]),
        morality=rng.beta(BETA_PARAMS["morality"][0], BETA_PARAMS["morality"][1]),
        anger_tendency=rng.beta(
            BETA_PARAMS["anger_tendency"][0], BETA_PARAMS["anger_tendency"][1]
        ),
        extraversion=rng.beta(
            BETA_PARAMS["extraversion"][0], BETA_PARAMS["extraversion"][1]
        ),
        ambition=rng.beta(BETA_PARAMS["ambition"][0], BETA_PARAMS["ambition"][1]),
        resilience=rng.beta(BETA_PARAMS["resilience"][0], BETA_PARAMS["resilience"][1]),
        dominance_urge=rng.beta(
            BETA_PARAMS["dominance_urge"][0], BETA_PARAMS["dominance_urge"][1]
        ),
        risk_tolerance=rng.beta(
            BETA_PARAMS["risk_tolerance"][0], BETA_PARAMS["risk_tolerance"][1]
        ),
    )


def try_birth(
    agent: AgentState,
    all_agents: list[AgentState],
    rng: DeterministicRNG,
    current_tick: int,
) -> Optional[AgentState]:
    """Attempt to create a child for a living, eligible agent.

    Eligibility requirements (all must be met):

    - Agent is alive.
    - ``MIN_ADULT_AGE_FOR_BIRTH <= agent.age <= MAX_REPRODUCTION_AGE``.
    - ``agent.spouse`` is not None.

    On success, the parent's money is reduced by
    ``DEATH_INHERITANCE_FRACTION`` and transferred to the child.

    Args:
        agent: The parent agent (modified in place on birth).
        all_agents: All agents in the simulation (used to compute the next
            available ID).
        rng: Deterministic RNG for the probability roll.
        current_tick: The current simulation tick number.

    Returns:
        A new ``AgentState`` if birth occurs, ``None`` otherwise.
    """
    # --- Eligibility checks ---
    if not agent.is_alive:
        return None
    if agent.age < MIN_ADULT_AGE_FOR_BIRTH or agent.age > MAX_REPRODUCTION_AGE:
        return None
    if agent.spouse is None:
        return None

    # --- Birth chance ---
    birth_chance = BIRTH_CHANCE_BASE
    if agent.traits.ambition > 0.5:
        birth_chance += 0.0002
    if agent.emotions.happiness_score > 0.5:
        birth_chance += 0.0001

    if rng.random() >= birth_chance:
        return None

    # --- Next available ID ---
    existing_numeric_ids: list[int] = []
    for a in all_agents:
        try:
            existing_numeric_ids.append(int(a.id))
        except (ValueError, TypeError):
            pass
    next_id = max(existing_numeric_ids) + 1 if existing_numeric_ids else 0

    # --- Traits & gender ---
    traits = _generate_traits(rng)
    gender = Gender.MALE if rng.random() < 0.5 else Gender.FEMALE

    # --- Needs (child starts well-satisfied) ---
    needs = AgentNeeds()
    needs.set_level(NeedType.FOOD, rng.uniform(0.7, 0.9))
    needs.set_level(NeedType.WATER, rng.uniform(0.7, 0.9))
    needs.set_level(NeedType.SLEEP, rng.uniform(0.8, 1.0))
    needs.set_level(NeedType.SEXUAL_TENSION, 0.0)
    needs.set_level(NeedType.SAFETY, rng.uniform(0.6, 0.9))
    needs.set_level(NeedType.FINANCIAL_SECURITY, 0.5)
    needs.set_level(NeedType.SHELTER, 1.0 if agent.resources.property else 0.3)
    needs.set_level(NeedType.SOCIAL_CONNECTION, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.FAMILY_BOND, rng.uniform(0.6, 0.9))
    needs.set_level(NeedType.ROMANTIC_BOND, 0.0)
    needs.set_level(NeedType.SELF_ESTEEM, rng.uniform(0.5, 0.8))
    needs.set_level(NeedType.REPUTATION, rng.uniform(0.4, 0.7))
    needs.set_level(NeedType.INFERIORITY_GAP, 0.0)

    # --- Financial inheritance ---
    inheritance = agent.resources.money * DEATH_INHERITANCE_FRACTION
    agent.resources.money -= inheritance
    agent.resources.wealth = agent.resources.money

    # --- Persona ---
    child_persona = ""
    if agent.persona:
        child_persona = f"Child of {agent.persona}"

    # Health (children are generally healthy)
    health = rng.uniform(0.8, 1.0)

    # --- Parent/child linkage ---
    parent_ids_list = [agent.id]
    spouse = None
    if agent.spouse is not None:
        for a in all_agents:
            if a.id == agent.spouse and a.is_alive:
                spouse = a
                break
        if spouse is not None:
            parent_ids_list.append(spouse.id)

    child = AgentState(
        id=AgentId(str(next_id)),
        persona=child_persona,
        traits=traits,
        needs=needs,
        emotions=AgentEmotions(happiness_score=0.7),
        resources=AgentResources(
            money=inheritance,
            wealth=inheritance,
            employed=False,
            education=EducationLevel.NONE,
            property=False,
            health=health,
        ),
        employment_status=EmploymentStatus.UNEMPLOYED,
        wealth_class=agent.wealth_class,
        gender=gender,
        culture=agent.culture,
        age=0,
        age_bracket="child",
        born_tick=TickNumber(current_tick),
        grid_x=agent.grid_x,
        grid_y=agent.grid_y,
        job_type=JobType.UNEMPLOYED,
        last_action=ActionType.IDLE,
        parent_ids=parent_ids_list,
    )

    agent.children_ids.append(child.id)
    if spouse is not None:
        spouse.children_ids.append(child.id)

    from simulation.agents.sibling_system import link_siblings_at_birth
    link_siblings_at_birth(child, parent_ids_list, all_agents)

    return child
