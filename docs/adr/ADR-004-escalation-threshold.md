# ADR-004: LLM Escalation Threshold

**Status:** Proposed

**Date:** 2026-07-07

**Owner:** Simulation Engineer

**Supersedes:** None

---

## Context

LLM inference is expensive and slow compared to deterministic computation. Invoking Gemma for every agent decision would make the simulation impractical at scale (10,000+ agents). The decision pipeline must only escalate to Gemma when deterministic computation is genuinely uncertain.

## Decision

We will use a configurable **ambiguity threshold** to determine when to escalate.

### Threshold Definition

The system computes action utility scores for all available actions. If the difference between the top two scores is less than the threshold, the decision is considered ambiguous.

```
top_score = max(scores)
second_score = second_max(scores)

if (top_score - second_score) < AMBIGUITY_THRESHOLD:
    escalate_to_gemma()
else:
    execute(top_score_action)
```

### Default Threshold

```python
AMBIGUITY_THRESHOLD = 0.05  # Configurable per simulation run
```

### Additional Conditions

Beyond score proximity, escalation may also trigger when:
- Emotional state variance exceeds a configurable bound
- Internal conflict between morality and survival scores is detected
- Multiple actions (3+) have scores within the threshold band
- An agent's current need profile matches a configurable "turmoil" pattern

### Configuration

The threshold and all additional conditions are defined in a single `escalation_config` dictionary, allowing policy-level tuning without code changes.

## Consequences

**Positive:**
- LLM calls are proportional to uncertainty, not population size
- For most agents in most ticks, the deterministic engine suffices
- Configuration is externalized — no code changes for tuning
- Explains the "System 1 → System 2" transition clearly

**Neutral:**
- Threshold selection requires empirical tuning
- Different policy scenarios may need different thresholds

**Negative:**
- Agents near the threshold behave differently than those clearly above/below
- Risk of threshold gaming if policies are designed to exploit ambiguity

## Related

- [ADR-003: Hybrid Decision Fusion](ADR-003-hybrid-decision-fusion.md)
- [ADR-002: Deterministic Simulation Design](ADR-002-deterministic-simulation-design.md)
- [Master Context §7](../../SOCIETAS_Master_Context.md)
- [Decision Pipeline Vault Note](../../vault/010-Architecture/decision-pipeline.md)
