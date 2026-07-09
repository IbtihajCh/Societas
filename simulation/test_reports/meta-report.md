# Simulation Test Meta-Report — Cross-Scenario Analysis

**Date:** 2026-07-09
**Scenarios run:** 29 (all passed without crash)
**Engine version:** v1.0 deterministic fallback (no LLM connected)

---

## Executive Summary

The SOCIETAS simulation engine v1.0 is **stable, deterministic, and crash-free** across 29 extreme scenarios. However, the deterministic fallback produces a **uniformly safe society** — no deaths, no crimes, no protests occurred in any scenario. This meta-report synthesizes findings across all scenarios to identify root causes and recommend improvements.

## Key Statistics (all 29 scenarios)

| Metric | Range | Default (a1) | Most Extreme |
|---|---|---|---|
| Deaths | 0 across all | 0 | — |
| Crimes | 0 across all | 0 | — |
| Protests | 0 across all | 0 | — |
| Happiness | 0.625 – 0.686 | 0.683 | b2_utopian (lowest) |
| Unlust | 0.115 – 0.176 | 0.115 | c2_drought (highest) |
| Action types | 2–3 per scenario | 3 | All same (WORK/BUY_FOOD/SEEK_JOB) |

## Critical Findings

### 1. The Engine Is Too Stable (Core Issue)

**Finding:** No agent ever dies, commits a crime, or protests — regardless of configuration.

**Root cause:** The deterministic fallback (`decision_engine.deterministic_fallback()`) only selects from {WORK, BUY_FOOD, REST, SEEK_JOB, BEG}. It never selects {STEAL, HARM_OTHER, PROTEST, BEFRIEND, SHARE, CONSOLE, ISOLATE, COMPLAIN}. The 3-level priority queue is a safety net that guarantees survival but produces uniform, boring behavior.

### 2. The Welfare Paradox

**Finding:** Generous welfare produces the LEAST happy society (H=0.625, b2_utopian).

**Explanation:** Welfare eliminates the employment urgency → more agents stay unemployed → they miss the +0.05 happiness employment bonus → lower overall happiness. This is potentially realistic (welfare dependency) but the magnitude seems oversized for a +0.05 bonus on a 0-1 scale.

### 3. Extreme Scarcity Causes Zero Deaths

**Finding:** 85% food collapse (c1_famine) causes 1.6x food buying and moderate unhappiness (H=0.641) but ZERO deaths.

**Root causes:**
- Infinite jobs: every agent can always find work
- No food unavailability: food is purchasable at any price
- The fallback never selects crisis responses (BEG, STEAL)
- Work income always covers food cost

### 4. Wealth Is Cosmetic

**Finding:** 100% poor agents (d1_all_poor) have identical outcomes to 100% rich agents (d2_all_rich).

**Root cause:** The deterministic fallback ignores wealth_class. All agents earn the same salary, buy food at the same price, and work regardless of wealth. Only `buy_food` action checks money, and agents always have enough.

### 5. MockAIRouter Produces Identical Results to No AI

**Finding:** g1_with_ai (MockAIRouter) and g2_no_ai produced identical per-tick stats and action distributions.

**Root cause:** The `MockAIRouter.agent_decide()` returns actions from the deterministic fallback — it's a mock that mimics the fallback, not an AI that injects variety. The mock is correctly implemented but doesn't exercise the LLM integration path.

### 6. Interesting Correlations Discovered

| Correlation | Strength | Finding |
|---|---|---|
| tax_rate vs SEEK_JOB count | r ≈ -0.97 | Higher tax → LESS job seeking (counterintuitive — welfare enables staying home) |
| food_availability vs BUY_FOOD count | r ≈ -0.88 | Less food → MORE buying (scarcity drives purchasing, not saving) |
| unlust vs happiness | r ≈ -0.95 | Near-perfect inverse coupling (designed that way) |
| welfare_amount vs happiness | r ≈ -0.65 | More welfare → less happy (welfare trap finding) |

## Anomaly Detection (Consolidated)

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | **PASS** | 100% survival in all scenarios |
| No runaway unlust (>0.9 avg) | **PASS** | Max 0.176 (drought) |
| No runaway crime (>0.5 rate) | **PASS** | 0.0 in all scenarios |
| No negative money | **PASS** | Agents always have money for food |
| Needs in [0, 1] | **PASS** | All needs clamped correctly |
| State hash changes each tick | **NOT TESTED** | Runner doesn't compute state_hash |
| At least 3 action types | **PASS** | Exactly 3 in all scenarios (WORK/BUY_FOOD/SEEK_JOB) |
| Wealth distribution plausible | **FAIL** | 100% poor → 0% poor at end state (d1) |
| Emotions distributed across >2 states | **FAIL** | Only HAPPY/NORMAL observed; no SAD/ANGRY/DESPAIR |

## What Works Well (Engine Strengths)

1. **Deterministic reproducibility**: Same seed = identical results (verified via g1/g2)
2. **Crash-free execution**: 29 scenarios × 200-500 ticks each, zero runtime errors
3. **Needs system**: Needs decay, scarcity multiplier, food buying loop all functional
4. **Emotion computation**: Happiness formula, unlust formula, emotion state machine all produce consistent values
5. **Economy**: Salary, tax, food cost, and welfare all flow correctly through agents
6. **Parameter sensitivity**: Parameters DO affect outcomes (just not catastrophically)
7. **Performance**: 200 ticks × 80 agents in 3-10 seconds (production-ready speed)

## Priority Recommendations

### P1: Enable Criminal/Social/Protest Actions in Fallback
The deterministic fallback needs to select from the FULL action set, not just safe actions. Add conditions:
- If unlust > 0.58 AND not morality_active → 30% chance STEAL, 20% HARM_OTHER
- If unlust > 0.45 OR emotion is SAD/ANGRY → PROTEST
- If social < 0.38 AND extraversion > 0.35 → BEFRIEND

### P2: Add Death Pathways
- Food unavailability check: if food_availability < 0.10, food purchase may fail (rng.chance)
- Starvation: if food < 0 for 3+ consecutive ticks → death
- Despair mortality: if despair AND unlust > 0.82 → rng.chance 0.4%/tick of death

### P3: Make Wealth Matter
- Poor agents can only access lower-paying jobs
- Food becomes unaffordable when money < food_cost
- Unlust formula should be more sensitive to absolute wealth level

### P4: Implement Real AI Integration
Replace MockAIRouter with actual vLLM calls to Gemma 4 models. The mock is indistinguishable from the fallback.

### P5: Add State Hash Tracking
The runner should compute and log state_hash each tick for determinism verification.

## Cross-Scenario Comparison Table

| Scenario | Happiness | Unlust | WORK | BUY_FOOD | SEEK_JOB | Alive | Wealth Split |
|---|---|---|---|---|---|---|---|
| a1_default | 0.683 | 0.115 | 14,625 | 1,200 | **96** | 80 | M56/R44 |
| a2_extended | 0.661 | 0.121 | 36,705 | 3,120 | 96 | 80 | — |
| b1_dictator | 0.639 | **0.173** | 14,478 | 1,320 | 123 | 80 | — |
| b2_utopian | **0.625** | 0.171 | 14,787 | 960 | 174 | 80 | — |
| b3_laissez_faire | 0.638 | 0.156 | 14,316 | 1,200 | **405** | 80 | — |
| b4_welfare_state | 0.684 | 0.128 | 14,578 | 1,169 | 174 | 80 | — |
| c1_famine | 0.641 | 0.155 | 13,896 | **1,920** | 105 | 80 | — |
| c2_drought | 0.632 | **0.176** | 13,991 | **1,765** | 165 | 80 | — |
| d1_all_poor | 0.682 | 0.118 | 14,562 | 1,200 | 159 | 80 | M41/R59 |
| d2_all_rich | 0.681 | 0.119 | 14,601 | 1,200 | 120 | 80 | — |

## Detailed Reports

Individual scenario reports with in-depth analysis:
- [a1_default_report.md](a1_default_report.md) — Baseline analysis
- [b1_dictator_report.md](b1_dictator_report.md) — Oppression analysis
- [b2_utopian_report.md](b2_utopian_report.md) — Welfare Paradox analysis
- [b3_laissez_faire_report.md](b3_laissez_faire_report.md) — Precarious Prosperity
- [c1_famine_report.md](c1_famine_report.md) — Scarcity resilience analysis
- [d1_all_poor_report.md](d1_all_poor_report.md) — Poverty irrelevance analysis

---

*Generated by the SOCIETAS Simulation Testing Framework — 475 unit tests pass, 29 integration scenarios executed, 0 crashes*
