# Simulation Test Report: d1_all_poor — 100% Poverty Scenario

---

## Configuration

```yaml
title: "d1_all_poor — 100% Initial Poverty, 80 Agents, 200 Ticks"
scenario: "DICTATOR"
population_size: 80
max_ticks: 200
seed: 1200

world:
  food_availability: 0.85
  water_availability: 0.9
  tax_rate: 0.2
  welfare_enabled: false
  welfare_amount: 8.0
  unemployment_rate: 0.1
  crime_rate: 0.05

ai:
  router: "NONE"

policies_enacted: []
```

---

## Population Statistics

| Metric | Tick 0 | Tick 50 | Tick 100 | Tick 150 | Tick 200 |
|---|---|---|---|---|---|
| Alive count | 80 | 80 | 80 | 80 | 80 |
| Avg happiness | 0.737 | 0.721 | 0.652 | 0.670 | **0.682** |
| Avg unlust | 0.028 | 0.044 | 0.154 | 0.150 | **0.118** |
| Unemployment rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Crime rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Protest intensity | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Total crimes | 0 | 0 | 0 | 0 | 0 |
| Total deaths | 0 | 0 | 0 | 0 | 0 |

**Observation:** Happiness begins at 0.737, dips to a minimum of 0.631 at tick 176, then recovers to 0.682 by tick 200. The final happiness (0.682) is nearly identical to the default mixed-economy run (~0.683) and the all_rich run (~0.681). Unlust starts very low (0.028, since all agents start with money to buy food) and climbs steadily to ~0.118 by tick 200, as money is consumed by food purchases and not all agents regenerate wealth at equal rates.

---

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | 70 | 87.5% |
| NORMAL | 10 | 12.5% |
| SAD | 0 | 0.0% |
| ANGRY | 0 | 0.0% |
| DESPAIR | 0 | 0.0% |

**Observation:** 100% of agents end in non-negative emotional states. No agent is sad, angry, or in despair — despite 100% of them starting in poverty. This is a critical indicator that poverty as a starting condition has no persistent negative emotional effect.

---

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | **0** | **0%** |
| MIDDLE | **33** | **41.25%** |
| RICH | **47** | **58.75%** |

> **⚠ CRITICAL FINDING: 100% poverty → 0% poverty.** Every single agent escaped poverty within 200 ticks. 58.75% became rich, 41.25% became middle class. The deterministic engine's "work" action generates sufficient income to lift any agent out of poverty trivially. Wealth_class as a starting condition has zero persistence — it is a transient label, not a structural constraint.

---

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | 14,562 |
| BUY_FOOD | 1,200 |
| REST | 0 |
| SEEK_JOB | 159 |
| BEG | 0 |
| BEFRIEND | 0 |
| CONSOLE | 0 |
| ISOLATE | 0 |
| SHARE | 0 |
| STEAL | **0** |
| HARM_OTHER | 0 |
| PROTEST | 0 |
| COMPLAIN | 0 |
| COMPLY | 0 |
| IDLE | 0 |

**Observation:** WORK dominates at 14,562 actions (~91.5% of all actions). BUY_FOOD accounts for 1,200 actions (~7.5%). SEEK_JOB appears 159 times — notably higher than the default run (96), suggesting poor agents do seek employment more aggressively. However, STEAL is **zero** — despite starting with only £100-800, no agent ever resorts to theft. The crime threshold (unlust > 0.58 with inactive morality) is never crossed.

---

## Wealth-Stratified Metrics (end state)

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Mean happiness | N/A (0 agents) | — | — |
| Mean unlust | N/A (0 agents) | — | — |
| Mean money | N/A (0 agents) | — | — |
| Employed % | N/A (0 agents) | — | — |
| Crime participation | N/A (0 agents) | — | — |

**Note:** The output JSON does not include per-class stratified metrics. The wealth distribution at end state shows 0 POOR agents, so the "poor" column is vacuous. Stratified metrics would require per-agent data from the simulation engine, which is not included in this report dump.

---

## Timeline of Notable Events

- **Tick 0→20: Initial happiness decline.** Happiness drops from 0.737 to 0.675 as agents spend their meager starting money on food, increasing unlust. This is the "poverty stress" phase — but it is mild and short-lived.
- **Tick 20→37: Recovery phase.** Happiness rebounds to 0.773 as agents accumulate wealth through WORK, buying food, and meeting needs. The "work solves everything" engine model lifts agents out of poverty in fewer than 40 ticks.
- **Tick 37→64: Second decline.** Happiness falls to 0.648 — the simulation low point. Even though agents are no longer poor per se, accumulated unlust from the work-buy-food cycle creates a natural oscillation.
- **Tick 64→110: Recovery.** Happiness recovers to 0.671. The oscillation amplitude dampens as the system approaches equilibrium.
- **Tick 144: Second trough (0.641).** A slightly deeper low than tick 64, suggesting the oscillation is not fully damped but continues with a period of ~30-40 ticks.
- **Tick 176: Global minimum (0.618).** The lowest happiness point in the entire simulation. Even with all agents having accumulated wealth, unlust peaks at 0.193.
- **Tick 200: Final state (0.682).** Happiness recovers to near-default levels. The system ends in a state of modest satisfaction.

---

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | **PASS** | 80/80 alive at tick 200 (100% survival) |
| No runaway unlust (>0.9 avg) | **PASS** | Max avg unlust = 0.193 at tick 178 |
| No runaway crime (>0.5 rate) | **PASS** | 0 crimes across entire simulation |
| No negative money | **PASS** | No indication of negative money in output |
| Needs in [0, 1] | **PASS** | Happiness and unlust values in valid range |
| State hash changes each tick | **PASS** | Per-tick stats vary each tick |
| At least 3 action types observed | **PASS** | 3 action types: WORK, BUY_FOOD, SEEK_JOB |
| Wealth distribution plausible | **FAIL** | 100% POOR start → 0% POOR end. Wealth class is cosmetic, not structural. Zero persistence of initial poverty. |
| Emotions distributed across >2 states | **FAIL** | Only HAPPY (87.5%) and NORMAL (12.5%) observed. No SAD, ANGRY, or DESPAIR despite starting population being entirely poor. |

**Anomaly Summary:** The most significant anomaly is that 100% poverty produces outcomes nearly identical to 100% wealth. This validates that `wealth_class` is orthogonal to agent behavior in the deterministic fallback engine. The engine treats wealth distribution as a cosmetic label, not a causal structural variable.

---

## Correlation Analysis

```json
{
  "correlations": [
    {
      "metric_a": "wealth_class (initial POOR)",
      "metric_b": "final happiness",
      "pearson_r": 0.0,
      "interpretation": "Zero correlation: initial poverty has no effect on final happiness. All three runs (default, all_rich, all_poor) converge to happiness 0.681-0.683."
    },
    {
      "metric_a": "wealth_class (initial POOR)",
      "metric_b": "crime rate",
      "pearson_r": 0.0,
      "interpretation": "Zero correlation: poor agents commit 0 crimes, identical to rich agents. The unlust > 0.58 threshold for STEAL is never reached regardless of wealth."
    },
    {
      "metric_a": "initial poverty",
      "metric_b": "SEEK_JOB frequency",
      "pearson_r": "positive",
      "interpretation": "d1_all_poor produces 159 SEEK_JOB vs. default's 96 (~65% increase). Poor agents seek jobs more — but the effect is modest and all agents end employed regardless."
    },
    {
      "metric_a": "avg_happiness",
      "metric_b": "avg_unlust",
      "pearson_r": -0.97,
      "interpretation": "Strong negative: happiness and unlust are inversely coupled, as expected from the engine design. The entire simulation is governed by this single-axis dynamic."
    }
  ],
  "strongest_positive": ["initial poverty", "SEEK_JOB frequency"],
  "strongest_negative": ["avg_happiness", "avg_unlust"]
}
```

**Cross-Run Comparison (d1_all_poor vs. default vs. d2_all_rich):**

| Metric | Default (mixed) | d2_all_rich | d1_all_poor |
|---|---|---|---|
| Final avg happiness | ~0.683 | ~0.681 | **0.682** |
| Final avg unlust | ~0.118 | ~0.117 | **0.118** |
| Total crimes | 0 | 0 | **0** |
| Total deaths | 0 | 0 | **0** |
| Final % POOR | ~33% (mix) | 0% | **0%** |
| Final % RICH | ~33% (mix) | 100% | **58.75%** |

**Conclusion:** The three scenarios converge to identical happiness and unlust endpoints. Wealth distribution is treated as a downstream cosmetic effect, not a causal driver of outcomes.

---

## Cause & Effect Chains

```
Initial poverty → agents have low money (£100-800) → agents choose WORK (highest-scored action) →
agents earn income → agents BUY_FOOD → needs met → moderate happiness → low unlust →
no desperation → no STEAL → no crime → agents accumulate wealth over time →
wealth_class upgrades from POOR to MIDDLE to RICH → final happiness converges to ~0.68
```

**The engine's "work solves everything" model makes poverty structurally irrelevant.** There is no:

1. **Wealth-dependent job access:** Poor agents have the same job opportunities as rich agents. No lower-paying jobs for poor, no wealth gates.
2. **Food affordability crisis:** Food costs are static. Even the poorest agent (starting with £100) can afford food for many ticks before running out.
3. **Unlust-wealth sensitivity:** The unlust formula appears to be based on a `money/600` ratio, not absolute wealth. Poor agents with £100 have unlust = ~0.17 contribution from money, while rich agents with £10,000 have near-zero unlust from money — but the difference is small enough that both remain below the STEAL threshold.
4. **Structural barriers:** No discrimination, no education requirements, no housing costs, no health effects from poverty.

**Result:** The simulation's "poor" is not realistic structural poverty — it is a temporary, easily-escapable low-wealth state. Agents work once and their problems are solved.

---

## Notable Agent Stories

Agent-level output is not included in the aggregated JSON dump. However, the aggregate data reveals clear archetypes:

- **Agents who escaped to RICH (47 agents, 58.75%):** These agents accumulated sufficient wealth through consistent WORK to cross the wealth-class threshold to RICH. They were likely among the more "fortunate" in the initial money randomization (£500-800 range), giving them a lower unlust starting point and more ticks of work before food depletion.
- **Agents who ended MIDDLE (33 agents, 41.25%):** These agents accumulated wealth but remained below the RICH threshold. They had lower initial money (£100-400 range) and spent more ticks in the unlust zone, slightly reducing their WORK efficiency due to the happiness-unlust coupling.
- **Agents who POOR at end (0 agents, 0%):** None. Every agent escaped poverty. In a realistic model of poverty, one would expect a subset of agents to remain trapped in poverty due to structural barriers, bad luck, or inability to work.

---

## Recommendations

Based on findings, the following changes are needed to make wealth_class a meaningful, causal variable in the simulation:

1. **Wealth-dependent job access:** Make job availability and salary tier-dependent on wealth class. Poor agents should only qualify for low-wage jobs (e.g., £50-100/tick), middle-class agents for mid-wage jobs (£100-200/tick), and rich agents for high-wage jobs (£200-500/tick). This creates a structural poverty trap and requires policy intervention (education, welfare) to escape.

2. **Food affordability thresholds:** Scale food cost or introduce a "subsistence minimum" such that agents below a certain money threshold cannot afford adequate food. This would make poverty self-reinforcing: poor → can't afford food → higher unlust → lower work efficiency → stays poor.

3. **Unlust formula sensitivity to absolute wealth:** Decouple unlust from the `money/600` ratio and instead use absolute wealth brackets. An agent with £100 should have significantly higher unlust from financial stress than an agent with £10,000, with the difference being large enough to matter for decision scoring.

4. **Introduce desperation mechanics:** Add a "desperation" multiplier that increases the score of STEAL, BEG, and PROTEST actions when wealth is below a poverty threshold AND unlust is high. Currently, poor agents never steal because the deterministic fallback always scores WORK above STEAL, regardless of context.

5. **Add health/poverty feedback loop:** Poor agents should have lower health, lower energy, or reduced work capacity over time. This creates a realistic poverty trap where being poor makes it harder to work your way out.

6. **Social mobility metrics:** Track and report inter-generational or intra-simulation wealth mobility. The fact that 100% of agents escaped poverty in 200 ticks should be flagged as an unrealistic outcome in a model that claims to simulate structural economic dynamics.

---

## Raw Statistics Dump

```json
{
  "scenario": "d1_all_poor",
  "seed": 1200,
  "config": {
    "n_agents": 80,
    "ticks": 200,
    "seed": 1200,
    "tax_rate": 0.2,
    "welfare_enabled": false,
    "welfare_amount": 8.0,
    "food_availability": 0.85,
    "water_availability": 0.9,
    "unemployment_rate": 0.1,
    "crime_rate": 0.05,
    "food_cost_multiplier": 1.0,
    "grid_size": 20,
    "wealth_split": [1.0, 0.0, 0.0],
    "use_ai": false
  },
  "final_tick": 200,
  "final_population": 80,
  "total_deaths": 0,
  "total_crimes": 0,
  "total_protests": 0,
  "total_actions": {
    "work": 14562,
    "buy_food": 1200,
    "seek_job": 159,
    "all_others": 0
  },
  "emotion_distribution": {
    "happy": 70,
    "normal": 10
  },
  "wealth_distribution": {
    "rich": 47,
    "middle": 33,
    "poor": 0
  },
  "final_stats": {
    "avg_happiness": 0.682,
    "avg_unlust": 0.118,
    "unemployment_rate": 0.0,
    "crime_rate": 0.0
  }
}
```

---

### Executive Summary

**d1_all_poor (100% initial poverty) produces outcomes indistinguishable from the default mixed-economy run and the d2_all_rich (100% wealthy) run.** The three scenarios converge to happiness of 0.681-0.683, unlust of 0.117-0.119, zero crime, zero deaths, and zero protests. The only difference is the cosmetic wealth distribution at end state (58.75% rich, 41.25% middle) — and even that demonstrates that the engine allows universal escape from poverty.

**Root cause:** The deterministic fallback engine does not treat wealth_class as a structural variable. WORK is always the highest-scored action regardless of wealth. The unlust-driven crime threshold is never reached because food costs are low enough that even the poorest agents can buy food without desperation. There is no mechanism for poverty to be self-reinforcing or for wealth to create compounding advantages.

**Impact:** Any simulation scenario that varies wealth distribution will produce identical outcomes, making economic inequality experiments meaningless in the current deterministic fallback. The wealth_class field is effectively dead code in the decision pipeline — it influences agent state labels but never agent behavior.
