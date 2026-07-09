# ADR-002: Deterministic Simulation Design

**Status:** Accepted (amended by ADR-005)

**Date:** 2026-07-07

**Owner:** Simulation Engineer

**Supersedes:** None

**Amended by:** [ADR-005](ADR-005-simulation-implementation-architecture.md) (2026-07-08)

---

## Context

The simulation engine must produce identical outputs given identical inputs. This is fundamental to the project's goal of explainability and reproducibility. Any non-determinism in the core engine would make it impossible to trace policy decisions to their effects.

However, the simulation must also integrate with Gemma (an LLM), which is inherently non-deterministic. The boundary between these two systems must be clearly defined.

## Decision

### Core Engine is Fully Deterministic

- All pseudo-random number generation uses a seeded `numpy.random.Generator`
- No floating-point operations that produce platform-dependent results
- Agent state updates follow strict sequential execution within each tick
- The engine produces a verifiable hash of each tick's state for reproducibility checks

### Deterministic Boundary

- The engine computes action utility scores deterministically
- Ambiguity detection (if scores are too close) triggers an escalation event
- Escalation events are logged with full input state
- Gemma's response is treated as an external input, not part of the deterministic chain
- The fusion step (mixing deterministic scores with Gemma weights) is deterministic given both inputs

### Seeding Strategy

- Each simulation run receives a single seed
- Seeds are derived from the run configuration hash
- The same seed + same configuration = identical simulation
- Agent-specific RNG streams are derived from the master seed using a deterministic splitting algorithm

## Consequences

**Positive:**
- Simulation runs are fully reproducible
- Debugging is straightforward (replay any tick with the same seed)
- Testing can assert exact state after N ticks
- Deterministic baseline allows clean measurement of LLM impact

**Neutral:**
- Requires careful attention to avoid non-deterministic operations
- Parallel execution of agents within a tick is possible but must be deterministic (e.g., using deterministic parallel patterns)

**Negative:**
- Floating-point determinism across platforms requires using fixed-point or deterministic libraries
- Adding new random elements requires updating the seeding strategy

## Amendment (ADR-005, 2026-07-08)

The deterministic boundary is clarified: LLM IS used in Layer 1 for tie-breaking
within priority levels and for policy translation. However:

- The **fusion step** (mixing deterministic scores with Gemma scores) is deterministic
  given both inputs — this principle from the original ADR holds.
- The **priority queue** (Maslow hierarchy, first-match-wins) is fully deterministic
  and is the primary selection mechanism.
- **Utility scoring** within priority levels is fully deterministic.
- LLM is only invoked when the top two utility scores are within the ambiguity
  threshold (0.05) — approximately 5-15% of decisions per tick.
- **Deterministic fallbacks** exist for all LLM use cases, ensuring the simulation
  is fully reproducible without AMD GPU.
- The **state hash** excludes LLM reasoning strings (only includes deterministic
  state: agent needs, money, emotion, unlust, alive status, world variables).

The core principle remains: same seed + same config + same LLM responses = identical
simulation. Without LLM, deterministic fallbacks ensure full reproducibility.

**Implementation verified:** 500 tests confirm determinism. Same seed + same config = identical state_hash (SHA-256). LLM reasoning excluded from hash per design.

---

## Related

- [ADR-003: Hybrid Decision Fusion](ADR-003-hybrid-decision-fusion.md)
- [ADR-004: LLM Escalation Threshold](ADR-004-escalation-threshold.md)
- [Master Context §4-6](../../SOCIETAS_Master_Context.md)
- [Simulation README](../../simulation/README.md)
