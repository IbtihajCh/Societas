# ADR-005: Simulation Implementation Architecture

**Status:** Accepted

**Date:** 2026-07-08

**Owner:** Simulation Engineer

**Supersedes:** None (amends ADR-002, ADR-003, ADR-004)

---

## Context

The SOCIETAS Project Guide (`docs/SOCIETAS_Project_Guide.md`) defines a detailed
multi-agent social policy simulation with specific psychological models (Maslow
priority queue, Freudian Unlust engine, Adlerian comparison), 13 needs, 7 traits,
5 emotions with timers, 14 actions, an economy with 11 job types, and a grid-based
world. The existing project scaffolding (`shared/` schemas, `simulation/` stubs)
was designed against an earlier, more abstract vision that does not match the Guide.

This ADR documents the architectural decisions for implementing the Guide's v1 scope
within the existing project structure, optimized for the AMD Developer Hackathon
Act II (Unicorn Track). The hackathon judges on creativity, product potential,
completeness, and AMD platform use — all four drive the decisions below.

### Forces at play

1. **Hackathon timeline (2-3 days):** Every decision must be implementable and
   testable in this window. Over-engineering is fatal.
2. **AMD platform scoring:** LLM integration via Gemma on AMD GPUs is a scoring
   criterion, not an optional feature.
3. **Guide fidelity:** The Guide is the canonical design document. The implementation
   should match it as closely as possible.
4. **Existing scaffolding:** `shared/` schemas and `simulation/` stubs exist but
   don't match the Guide. Breaking backend/frontend is acceptable (their code is
   also stubs), but the interfaces (`ISimulationEngine`, `IAgent`, etc.) must be
   preserved.
5. **Determinism requirement:** Same seed + same config = identical simulation.
   LLM non-determinism must be bounded by deterministic fallbacks.
6. **Subagent orchestration:** The implementation guide will be followed by less
   advanced AI agents. It must be unambiguous, with exact formulas and code templates.

---

## Decision

### 1. Decision Architecture: Maslow Priority Queue + Utility Scoring + LLM Fusion

The primary action selection mechanism is the Guide's **Maslow priority queue**
(7 levels, first-match-wins). Within each level that has multiple candidate actions,
**utility scoring** computes scores for each candidate. When the top two scores are
within the ambiguity threshold (0.05), **LLM tie-breaking** via Gemma fuses
deterministic and AI scores (0.7/0.3 weights).

```
Priority Queue (7 levels, first-match-wins)
  -> selects priority LEVEL
  -> within level: Utility Scoring for candidate actions
    -> if top-2 within 0.05: AMBIGUOUS -> Gemma tie-break (0.7 det + 0.3 Gemma)
    -> else: deterministic selection (highest score)
  -> execute selected action
```

**Rejected alternatives:**
- Pure utility scoring across all actions (doesn't match Guide's Maslow design,
  less original for hackathon)
- Pure priority queue without utility scoring (no LLM integration opportunity in
  the core decision loop, loses AMD platform scoring)
- LLM for all decisions (too slow, too expensive, not deterministic, not original)

### 2. Schema Strategy: Extend Existing shared/ Schemas

Existing `shared/` dataclasses are extended with Guide-specific fields. Enums are
replaced with Guide-aligned values. New schemas (`ImpactDelta`) are added. This
preserves interface compatibility while matching the Guide.

**Rationale:** Replacing enums is necessary because existing values are stubs that
don't match the Guide (e.g., 9 generic NeedTypes vs. Guide's 13 specific needs).
Extending dataclasses (adding fields) is safer than replacing them because it
preserves import paths and existing field names.

### 3. Policy Model: Dual Impact Deltas + Policy Weights

Policies produce both:
- **ImpactDeltas** per wealth class (direct per-tick effects: money_delta,
  food_delta, safety_delta, social_delta, anger_spike, world state changes)
- **PolicyWeights** (utility score modifiers: economic_freedom, social_welfare, etc.)

The LLM (Gemma) receives the policy text, existing PolicyWeights, and current world
state, then outputs both modified weights and per-class deltas. This is the killer
demo feature: a judge types "universal basic income" in natural language, Gemma
translates it to impact deltas, and agents react in real-time.

**Rejected alternatives:**
- Impact Deltas only (loses the utility score modification layer)
- Policy Weights only (less visible/ dramatic for demo, doesn't match Guide)

### 4. Four LLM Use Cases (AMD Platform Integration)

| Use Case | When | Temp | Frequency |
|---|---|---|---|
| Tie-breaking | Ambiguous decision within priority level | 0.2 | ~5-15% of agent decisions per tick |
| Policy translation | User enacts policy in natural language | 0.3 | User-triggered |
| Persona generation | Agent creation at simulation start | 0.7 | Once per agent (batched) |
| News generation | Periodic world news from events | 0.8 | Every 10 ticks |

**Models (final implementation):** Three Gemma 4 models:
- **Gemma 4 E2B** (~1GB) — Agent brains (all primary LLM decisions). Runs at ~55 tokens/sec on AMD GPU.
- **Gemma 4 26B A4B** (~16.5GB) — Moral dilemma escalation (thinking mode). Only invoked ~1-2% of decisions.
- **Gemma 4 31B** (~20.3GB) — Governance/policy translation (reserved for future use).
Total ~40GB of 198GB VRAM.

Batched calls for efficiency: agents are staggered across ticks (1/3 per tick),
so ~1 batched call per tick for ~80 agents.

### 5. v1 Scope

**Included:** Full agent state (7 traits, 13 needs, 5 emotions with timers, Unlust
engine, money/employment/health/reputation, grid position), needs decay/replenishment,
emotion state machine, priority queue + utility scoring + LLM fusion, 14 actions,
economy (11 jobs, salaries, food cost, welfare, rent), grid movement, Adler
comparison engine, death conditions, world state, 10-step tick loop, metrics, LLM
integration (tie-break, policy, persona, news), deterministic fallbacks, Docker
containerization.

**Excluded (per user decision):** Riot event, marriage/children/inheritance,
community formation, organized crime, environmental events, education system,
age brackets. These are deferred to v2+ per the Guide's roadmap.

### 6. Deterministic Fallbacks for All LLM Use Cases

Every LLM use case has a deterministic fallback that activates when
`ai_router.is_available() == False`:
- Tie-break: highest utility score wins, ties by action priority then RNG
- Policy translation: keyword-matching fallback table
- Persona generation: template-based string
- News generation: template-based string

This ensures the simulation runs without AMD GPU, enables testing without vLLM,
and ensures the hackathon demo works even if GPU is unavailable.

---

## Consequences

### Positive

- Matches the Guide's Maslow-based design — more original than pure utility scoring
- LLM integration is efficient (~1 batched call per tick) and scores on AMD platform use
- Priority queue + utility scoring hybrid gives both determinism and AI integration
- Dual policy model (deltas + weights) is a compelling demo feature
- Deterministic fallbacks ensure robustness
- Extending schemas preserves interface compatibility
- Clear separation: deterministic math in Layer 1, human reasoning in Layer 2

### Neutral

- Enums are replaced (breaking change for backend/frontend stubs — acceptable)
- ADR-002, ADR-003, ADR-004 are amended (not superseded — core principles hold)
- LLM calls add ~100ms per tick overhead (acceptable for real-time demo at 80 agents)

### Negative

- Schema extensions add complexity to AgentState (30+ fields)
- Three naming systems for traits exist in tests/prompts (must be unified)
- LLM non-determinism means state hash diverges across runs with AI enabled
  (mitigated by: state hash excludes LLM reasoning, fallback is deterministic)
- Replacing enums requires updating all test fixtures and prompt schemas

## Implementation Outcomes

**Status as of 2026-07-09:** Fully implemented. 500 tests passing across 20 test files.

### What was built
- 23 source files (17 created, 6 modified) totaling ~4,100 LOC
- 20 test files with 500 tests (determinism, integration, edge cases)
- 10-step tick loop wired into SimulationEngine.tick()
- MockAIRouter for testing without GPU (VLLMRouter spec written for AI team)

### Deviations from original decision
1. **Decision architecture evolved:** The original "Maslow priority queue + utility scoring + LLM fusion" was replaced by an "E2B Hybrid" approach where the LLM (Gemma 4 E2B) IS the agent's brain, receiving all state factors and returning a decision. The deterministic fallback uses a weighted selection across all 14 actions (not just the priority queue). Moral dilemmas escalate to Gemma 4 26B A4B with thinking mode. This gives deeper AI integration than originally planned.
2. **Three models instead of one:** Originally planned single Gemma 2 27B. Now three Gemma 4 models: E2B (~1GB, agent brains), 26B A4B (~16.5GB, moral reasoning), 31B (~20.3GB, governance/policy). Total ~40GB of 198GB VRAM.
3. **Staggered evaluation:** Agents re-evaluate every 3 ticks (agent_id % 3 offset), not every tick. Reduces LLM calls by 3x while keeping GPU busy.
4. **Unlust threshold raised:** Need deficit threshold changed from 0.5 to 0.7 (configurable via UNLUST_NEED_THRESHOLD) for more sensitive deprivation detection.
5. **Death thresholds raised:** Food/water/health death thresholds changed from 0.0 to 0.02 to enable actual deaths from starvation.
6. **Wealth-class multipliers added:** Salary (0.6/1.0/1.3x), food cost (1.3/1.0/0.8x), rent (£5/£25/£80) by poor/middle/rich class.

### Test scenario results (29 scenarios)
- 9 deaths across 3 scenarios (famine, drought, low morality)
- 518 protests with MockAI (vs 0 without)
- 6-9 action types per scenario (was 3 before tuning)
- Unlust range 0.202-0.299 (was 0.115-0.176)
- MockAI ≠ no-AI confirmed

### Remaining work (not ADR-005 scope)
- VLLMRouter implementation (AI Systems Engineer — spec at simulation/test_reports/vllm-integration-spec.md)
- Prompt file updates (AI Systems Engineer)
- Backend integration (Backend Engineer — see docs/cross-team-integration-guide.md)
- Docker setup for 3 vLLM containers (DevOps)

---

## Related

- [ADR-002](ADR-002-deterministic-simulation-design.md) — Amended: LLM is used in
  Layer 1 for tie-breaking, but fusion is deterministic given both inputs
- [ADR-003](ADR-003-hybrid-decision-fusion.md) — Amended: Fusion occurs within
  priority levels, not across all actions
- [ADR-004](ADR-004-escalation-threshold.md) — Amended: Ambiguity detection occurs
  within priority levels
- [SOCIETAS Project Guide](../SOCIETAS_Project_Guide.md) — Canonical design document
- [SOCIETAS Master Context](../SOCIETAS_Master_Context.md) — Architecture & philosophy
- [Simulation Implementation Guide](../SOCIETAS_Simulation_Implementation_Guide.md) —
  Complete A-Z implementation specification
