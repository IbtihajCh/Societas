# ADR-003: Hybrid Decision Fusion

**Status:** Proposed

**Date:** 2026-07-07

**Owner:** Simulation Engineer / AI Systems Engineer

**Supersedes:** None

**Amended by:** [ADR-005](ADR-005-simulation-implementation-architecture.md) (2026-07-08)

---

## Context

When Gemma is called to resolve an ambiguous decision, the result must be integrated back into the deterministic engine. There are several possible integration strategies:

1. **Gemma overrides** — Gemma's chosen action replaces the deterministic result entirely
2. **Weighted fusion** — Deterministic scores and Gemma scores are blended
3. **Gemma as tie-breaker only** — Gemma only selects among actions within the ambiguity threshold

The chosen strategy must preserve explainability while allowing Gemma to provide meaningful input.

## Decision

We will use **weighted fusion** with configurable blend factors.

### Fusion Formula

```
final_score = (deterministic_weight * deterministic_score)
            + (gemma_weight * gemma_score)
```

Where:
- `deterministic_weight` defaults to 0.7 (configurable)
- `gemma_weight` defaults to 0.3 (configurable)
- Weights are normalized to sum to 1.0

### Escalation Constraint

Fusion only occurs when ambiguity is detected (see ADR-004). For non-ambiguous decisions, the deterministic score wins directly (weights are 1.0 and 0.0).

### Explainability

Every fused decision records:
- The original deterministic scores
- The Gemma-provided scores
- The blend factor used
- The final fused scores
- The selected action

This trace is available to the dashboard and can be replayed for auditing.

## Consequences

**Positive:**
- Gemma influences but does not control decisions
- The deterministic engine always retains the majority weight
- Explainability is preserved through the trace log
- Blend factors can be tuned per scenario or policy type

**Neutral:**
- Requires both engines to produce scores for the same action set
- Gemma must receive the full context for meaningful scoring

**Negative:**
- Adds complexity to the decision pipeline
- If Gemma provides wildly divergent scores, fusion may produce unexpected results

## Amendment (ADR-005, 2026-07-08)

The fusion mechanism is clarified: fusion occurs **within priority levels**, not
across all actions. The decision pipeline is now:

1. **Priority queue** (deterministic, 7 Maslow levels, first-match-wins) selects
   the priority level.
2. **Utility scoring** (deterministic) computes scores for candidate actions within
   that level.
3. **Ambiguity detection** checks if top-2 scores are within 0.05.
4. If ambiguous AND LLM available: **fusion** (0.7 det + 0.3 Gemma).
5. If not ambiguous OR LLM unavailable: **deterministic selection** (highest score).

The fusion formula, weights (0.7/0.3), and explainability mandate are unchanged.
Fusion simply operates on a smaller action set (the candidates within a priority
level, typically 2-3 actions) rather than all 14 actions. This is more efficient
and more meaningful — Gemma only weighs in when the deterministic engine is genuinely
uncertain between actions at the same Maslow priority level.

---

## Related

- [ADR-002: Deterministic Simulation Design](ADR-002-deterministic-simulation-design.md)
- [ADR-004: LLM Escalation Threshold](ADR-004-escalation-threshold.md)
- [Master Context §8](../../SOCIETAS_Master_Context.md)
- [Tie-Break Prompt](../../prompts/tie-break.md)
