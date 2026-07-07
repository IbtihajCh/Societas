# ADR-003: Hybrid Decision Fusion

**Status:** Proposed

**Date:** 2026-07-07

**Owner:** Simulation Engineer / AI Systems Engineer

**Supersedes:** None

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

## Related

- [ADR-002: Deterministic Simulation Design](ADR-002-deterministic-simulation-design.md)
- [ADR-004: LLM Escalation Threshold](ADR-004-escalation-threshold.md)
- [Master Context §8](../../SOCIETAS_Master_Context.md)
- [Tie-Break Prompt](../../prompts/tie-break.md)
