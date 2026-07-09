# Feature Specification: Simulation Engine v1 — Complete Implementation

**Status:** Draft

**Owner:** Simulation Engineer

**Date:** 2026-07-08

**Related ADR:** [ADR-005](../../docs/adr/ADR-005-simulation-implementation-architecture.md)

---

## Summary

Implement the complete v1 simulation engine as defined in the
[SOCIETAS Project Guide](../../docs/SOCIETAS_Project_Guide.md): 80 agents with
Beta-distributed psychological traits, 13 Maslow needs, a Freudian Unlust engine,
5-emotion state machine with timers, Adlerian comparison engine, 14 actions selected
via a Maslow priority queue with utility scoring and LLM tie-breaking, a full economy
with 11 job types, grid-based world with movement, and LLM integration via Gemma on
AMD GPUs for tie-breaking, policy translation, persona generation, and news generation.

---

## Motivation

This is Phase 1 of the SOCIETAS roadmap — the simulation core. The project is
scaffolded but all logic is `pass`/TODO stubs with zero test coverage. The Project
Guide defines the canonical design; this spec implements its v1 scope for the
AMD Developer Hackathon Act II (Unicorn Track).

The hackathon judges on creativity, product potential, completeness, and AMD
platform use. The hybrid deterministic+LLM architecture satisfies all four:
the Maslow priority queue + Unlust engine is novel; the policy sandbox has
product potential; the full working simulation demonstrates completeness; and
Gemma 2 27B on AMD's 198GB VRAM GPU for four LLM use cases maximizes platform use.

---

## Acceptance Criteria

```gherkin
Scenario: Deterministic simulation
  Given a simulation with seed=42 and 80 agents
  When I run 100 ticks without LLM (deterministic fallback)
  Then the state hash after tick 100 is identical across runs

Scenario: Agent needs decay
  Given an agent with food=0.5 and world food_availability=1.0
  When one tick passes
  Then the agent's food need is 0.5 - (0.018 * 1.0) = 0.482

Scenario: Unlust computation
  Given an agent with food=0.2, water=0.3, safety=0.4, social=0.3, money=200
  When Unlust is computed
  Then unlust = (0.3*0.28) + (0.2*0.22) + (0.1*0.20) + (0.2*0.12) + (0.667*0.18) = 0.324

Scenario: Emotion state machine
  Given an agent with unlust=0.85 and anger_tendency=0.3
  When emotion is updated
  Then the agent enters DESPAIR state with emotion_timer = 4

Scenario: Priority queue action selection
  Given an agent with food=0.05, money=100, morality_active=True
  When the priority queue runs
  Then Level 1 (Critical Survival) triggers and buy_food is selected

Scenario: LLM tie-breaking
  Given an agent at Level 1 with buy_food_util=0.31 and steal_util=0.29
  When the difference (0.02) is less than the ambiguity threshold (0.05)
  Then the decision is escalated to Gemma for tie-breaking

Scenario: LLM policy translation
  Given a user types "raise income tax by 10% and fund welfare"
  When the policy is enacted
  Then Gemma translates it to ImpactDeltas per wealth class and modified PolicyWeights
  And agents react in subsequent ticks

Scenario: Agent death by starvation
  Given an agent with food=0.0
  When the death check runs
  Then the agent's is_alive is set to False and AgentDeceasedEvent is published

Scenario: Adler comparison
  Given agent A (Maslow score 0.8) interacts with agent B (Maslow score 0.5)
  When the Adler comparison runs
  Then agent B's inferiority_gap increases, self_esteem decreases, unlust increases

Scenario: Deterministic fallback
  Given ai_router.is_available() returns False
  When an ambiguous decision is encountered
  Then the highest utility score wins, ties broken by action priority then RNG
```

- [ ] Same seed + same config = identical state hash (without LLM)
- [ ] All 13 needs decay at exact rates from the Guide
- [ ] Unlust formula matches Guide exactly
- [ ] All 5 emotion states trigger correctly with timers
- [ ] Priority queue selects correct level (first-match-wins)
- [ ] Utility scoring computes correct scores for candidate actions
- [ ] LLM fusion uses 0.7/0.3 weights and records explainability trace
- [ ] All 14 actions execute with correct effects
- [ ] Economy: 11 job types, salary ranges, food cost, welfare, rent
- [ ] Grid movement with toroidal wrapping
- [ ] Adler comparison triggers on interaction
- [ ] All 4 death conditions checked
- [ ] 10-step tick loop executes in correct order
- [ ] Metrics computed per tick (9 metrics + wealth stratification)
- [ ] LLM policy translation produces ImpactDeltas + PolicyWeights
- [ ] LLM persona generation produces personas at init
- [ ] LLM news generation produces articles every 10 ticks
- [ ] Deterministic fallbacks work for all 4 LLM use cases
- [ ] 90% branch test coverage
- [ ] Docker containerization

---

## Design

### Data Flow

```
User enacts policy (natural language)
  -> Gemma translates to ImpactDeltas + PolicyWeights
  -> Policy stored in PolicyEngine

Each tick:
  1. Publish TickStartedEvent
  2. Apply policy effects (deltas to agents, world state changes)
  3. Need decay (13 needs, scarcity multiplier, crime pressure)
  4. Welfare application (if enabled, to unemployed)
  5. Emotion update (happiness -> Unlust -> emotion state machine)
  6. Action selection per agent (deterministic order by ID):
     a. Priority queue (7 levels, first-match-wins)
     b. Utility scoring for candidates within level
     c. If ambiguous AND LLM available: Gemma tie-break (0.7/0.3 fusion)
     d. Execute action (modify agent/world/other agents)
     e. Adler comparison on interaction
     f. Publish AgentActedEvent
  7. Agent movement (1-2 random walk steps, angry agents move more)
  8. Death check (starvation, dehydration, health, despair, old age)
  9. World metrics update (9 metrics + wealth stratification)
  10. State hash + publish TickCompletedEvent
```

### Interfaces

**Input — Policy enactment:**
```json
{
    "policy_text": "raise income tax by 10% and fund welfare",
    "context": {
        "world_state": {"tax_rate": 0.20, "unemployment_rate": 0.12, ...},
        "population_summary": {"poor": 40, "middle": 28, "rich": 12}
    }
}
```

**Output — Policy translation:**
```json
{
    "policy_weights": {"economic_freedom": -0.3, "social_welfare": 0.4, ...},
    "impact_deltas": {
        "poor": {"money_delta": 8.0, "food_delta": 0.0, "safety_delta": 0.02, ...},
        "middle": {"money_delta": -5.0, "food_delta": 0.0, ...},
        "rich": {"money_delta": -50.0, "anger_spike": 0.05, ...}
    },
    "world_changes": {"new_tax_rate": 0.30, "welfare_on": true},
    "reasoning": "Tax increase funds welfare for the poor..."
}
```

**Input — Tie-break request:**
```json
{
    "agent_id": "42",
    "state": {"unlust": 0.62, "morality": 0.45, "emotion": "ANGRY", ...},
    "options": [
        {"action": "PROTEST", "utility_scores": {...}, "base_score": 0.31},
        {"action": "STEAL", "utility_scores": {...}, "base_score": 0.29}
    ],
    "context": {"nearby_agents": 5, "crime_rate": 0.08, ...}
}
```

**Output — Tie-break response:**
```json
{
    "action": "PROTEST",
    "confidence": 0.65,
    "reason": "Agent is angry and nearby protesters provide solidarity",
    "scores": {"PROTEST": 0.8, "STEAL": 0.2}
}
```

### State Changes

New state variables added to `AgentState`: `gender`, `culture`, `born_tick`,
`unlust`, `good_acts`, `crimes_committed`, `notoriety`, `trust_in_govt`,
`protest_count`, `grid_x`, `grid_y`, `job_type`, `spouse`, `enemies`,
`community_id`.

New state variables added to `AgentEmotions`: `emotion_timer`, `happiness_score`.

New state variables added to `AgentResources`: `money`, `base_salary`, `employed`,
`education`, `property`, `health`.

New state variables added to `SimulationState`: `food_availability`,
`water_availability`, `crime_rate`, `protest_intensity`, `unemployment_rate`,
`tax_rate`, `welfare_enabled`, `welfare_amount`.

New schema: `ImpactDelta` (per wealth class impact deltas).

New enums: `Gender`, `Culture`, `EducationLevel`, `JobType`.

Replaced enums: `NeedType` (13 values), `ActionType` (15 values), `EmotionType`
(5 values), `WealthClass` (3 values).

New constants: ~20 Guide constants (decay rates, thresholds, costs, grid size).

---

## Dependencies

- [ADR-005](../../docs/adr/ADR-005-simulation-implementation-architecture.md) — Governing architectural decisions
- [ADR-002](../../docs/adr/ADR-002-deterministic-simulation-design.md) — Determinism requirements (amended)
- [ADR-003](../../docs/adr/ADR-003-hybrid-decision-fusion.md) — Fusion formula (amended)
- [ADR-004](../../docs/adr/ADR-004-escalation-threshold.md) — Ambiguity threshold (amended)
- `shared/` — All schemas, types, constants, interfaces, utilities (to be extended)
- `models/` — AI router, tie-breaker, policy translator, persona generator, narrative generator (to be implemented)
- `prompts/` — Tie-break, policy-translation, persona-generation, narrative-generation (to be updated)
- `tools/mocks/mock_ai_router.py` — For testing without vLLM

---

## Determinism & Explainability

- [x] This feature is deterministic (simulation engine — all math is deterministic, LLM has fallbacks)
- [x] This feature includes an explainability trace (every fused decision records deterministic scores, Gemma scores, blend factor, final scores, selected action, reasoning)
- [x] This feature uses LLM (tie-break via `prompts/tie-break.md`, policy translation via `prompts/policy-translation.md`, persona generation via `prompts/persona-generation.md`, news generation via `prompts/narrative-generation.md`)

---

## Testing Plan

- **Unit tests** for each subsystem: needs decay, Unlust engine, emotion state machine,
  priority queue, utility scoring, each of 14 actions, economy, grid, Adler, death check
- **Determinism tests**: same seed = same state hash after N ticks (without LLM)
- **Integration tests**: full tick loop with 80 agents, 100 ticks, verify metrics
- **LLM integration tests**: mock router for fusion formula, fallback when unavailable
- **Policy tests**: delta application, weight modification, deterministic fallback
- **90% branch coverage** (CI-enforced, highest bar in project)

---

## Open Questions

- None at this time. All architectural decisions resolved in ADR-005 and user
  discussion. Implementation details are fully specified in the
  [Simulation Implementation Guide](../../docs/SOCIETAS_Simulation_Implementation_Guide.md).

---

## Related

- [Feature Vault](../060-Features/)
- [Sprint Plan](../030-Sprints/)
- [SOCIETAS Project Guide](../../docs/SOCIETAS_Project_Guide.md)
- [Simulation Implementation Guide](../../docs/SOCIETAS_Simulation_Implementation_Guide.md)
- [ADR-005](../../docs/adr/ADR-005-simulation-implementation-architecture.md)
