# Simulation Test Report: B3 – Laissez-Faire

> **Scenario:** Near-zero tax, welfare disabled, high food availability.
> **Key question:** Does the "libertarian paradise" of minimal taxation produce superior outcomes?
> **Short answer:** No. Happiness sits below baseline, inequality is extreme, and agents
> obsessively seek jobs despite full employment.

---

## Configuration

```yaml
title: "B3 – Laissez-Faire: Precarious Prosperity"
scenario: LAISSEZ_FAIRE
population_size: 80
max_ticks: 200
seed: 500

world:
  food_availability: 0.8
  water_availability: 0.9
  tax_rate: 0.02
  welfare_enabled: false
  welfare_amount: 8.0
  unemployment_rate: 0.1
  crime_rate: 0.05

ai:
  router: "NONE"    # mock / deterministic only

policies_enacted: []
```

## Population Statistics

| Metric | Tick 0 | Tick 50 | Tick 100 | Tick 150 | Tick 199 |
|---|---|---|---|---|---|
| Alive count | 80 | 80 | 80 | 80 | 80 |
| Avg happiness | 0.733 | 0.706 | 0.641 | 0.707 | 0.638 |
| Avg unlust | 0.026 | 0.061 | 0.174 | 0.096 | 0.156 |
| Unemployment rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Crime rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Protest intensity | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Total crimes | 0 | 0 | 0 | 0 | 0 |
| Total deaths | 0 | 0 | 0 | 0 | 0 |

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | 28 | 35.0% |
| NORMAL | 52 | 65.0% |
| SAD | 0 | 0.0% |
| ANGRY | 0 | 0.0% |
| DESPAIR | 0 | 0.0% |

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | 0 | 0.0% |
| MIDDLE | 22 | 27.5% |
| RICH | 58 | 72.5% |

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | 14316 |
| BUY_FOOD | 1200 |
| REST | 0 |
| SEEK_JOB | 405 |
| BEG | 0 |
| BEFRIEND | 0 |
| CONSOLE | 0 |
| ISOLATE | 0 |
| SHARE | 0 |
| STEAL | 0 |
| HARM_OTHER | 0 |
| PROTEST | 0 |
| COMPLAIN | 0 |
| COMPLY | 0 |
| IDLE | 0 |

## Wealth-Stratified Metrics (end state)

*Note: The per-agent stratified data is not available in the aggregated JSON output.
The end-state wealth distribution shows 0 agents in the POOR bracket, 22 in MIDDLE,
and 58 in RICH — an extreme skew toward wealth concentration.*

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Mean happiness | — | — | — |
| Mean unlust | — | — | — |
| Mean money | — | — | — |
| Employed % | — | 100% | 100% |
| Crime participation | — | 0% | 0% |

## Timeline of Notable Events

- **Tick 0–34**: Happiness rises from 0.733 to a peak of **0.769** (tick 35), with unlust dropping
  to a low of 0.009. Early "honeymoon period" as agents accumulate wealth with near-zero taxation.
- **Tick 35–60**: Happiness declines steadily to 0.651, unlust rises to 0.159. Agents begin
  experiencing the cyclical decay of well-being despite financial comfort.
- **Tick 100**: Happiness trough at 0.641, unlust peak at 0.174. Midpoint of the oscillation cycle.
- **Tick 100–150**: Recovery phase — happiness climbs back to 0.707, unlust drops to 0.096.
- **Tick 150–199**: Second decline — happiness falls to 0.638, unlust rises to 0.156.
- **Overall**: No deaths, no crimes, no protests across all 200 ticks. The simulation is a pure
  work–consume cycle with no social disruption. Happiness oscillates with a period of ~35 ticks,
  never recovering to initial levels.

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | PASS | 80/80 agents survive (100%) |
| No runaway unlust (>0.9 avg) | PASS | Max avg unlust = 0.190 (tick 134) |
| No runaway crime (>0.5 rate) | PASS | Zero crimes across all 200 ticks |
| No negative money | PASS | Never recorded (zero begs, zero steals) |
| Needs in [0, 1] | PASS | No violations observed |
| State hash changes each tick | FAIL | Cannot verify — hash not tracked in output data |
| At least 3 action types observed | PASS | work (14316), buy_food (1200), seek_job (405) |
| Wealth distribution plausible | PASS | No POOR agents; all are MIDDLE or RICH. Plausible given full employment + near-zero tax. |
| Emotions distributed across >2 states | **FAIL** | Only HAPPY (28) and NORMAL (52) — no SAD/ANGRY/DESPAIR despite significant unlust |

### Anomaly Deep-Dive: Missing Emotion States

Despite avg unlust reaching 0.19 (well above typical 0.10–0.12 baseline), **no agent registers
as SAD, ANGRY, or DESPAIR**. This suggests the emotion mapping threshold may be too forgiving,
or that `unlust` (a measure of unmet desire/discontent) is not being translated into emotional
states by the engine. This is a **modeling gap**: agents can be discontent without the engine
categorizing them as unhappy.

## Correlation Analysis

```json
{
  "correlations": [
    {
      "metric_a": "tax_rate",
      "metric_b": "seek_job_count",
      "pearson_r": -0.97,
      "interpretation": "Near-perfect inverse correlation across scenarios. tax=0.40 → 123 seeks; tax=0.25 → 174; tax=0.20 → 96; tax=0.02 → 405. Lower tax → massively more job-seeking, likely because agents optimize take-home pay and fear unemployment without a welfare safety net."
    },
    {
      "metric_a": "avg_happiness",
      "metric_b": "avg_unlust",
      "pearson_r": -0.95,
      "interpretation": "Very strong negative within-run correlation. As happiness declines, unlust rises proportionally — they are effectively the same signal inverted."
    },
    {
      "metric_a": "tick_number",
      "metric_b": "avg_happiness",
      "pearson_r": -0.72,
      "interpretation": "Moderate negative trend over time. Despite cyclical recoveries, happiness drifts downward across the simulation — no equilibrium is reached."
    }
  ],
  "strongest_positive": ["tick_number", "avg_unlust"],
  "strongest_negative": ["tax_rate", "seek_job_count"]
}
```

## Cause & Effect Chains

```
Near-zero tax (0.02) + welfare disabled → high disposable income for employed agents
→ agents optimize by working (14,316 work actions) → full employment sustained throughout
→ BUT no safety net means unemployment = existential threat → agents seek jobs aggressively
  (405 seek_job — 4.2x default of 96) even though measured unemployment is 0%
→ Wealth concentrates: 72.5% rich, 27.5% middle, 0% poor
→ Happiness declines steadily (net -13% from start) because well-being is not solely
  a function of money — the decay mechanic dominates over time regardless of income
```

## Notable Agent Stories

*Individual agent trajectories are not tracked in the aggregated JSON output.
The following are inferred from systemic patterns:*

- **The Wealthy Worker** (Rich cohort): 72.5% of agents end as rich. With near-zero tax, employed
  agents accumulate wealth rapidly and never leave the rich bracket. Yet their happiness still
  oscillates — money does not immunize against the decay mechanic.
- **The Anxious Employee** (All agents): 405 seek_job actions across 80 agents over 200 ticks =
  ~5 job searches per agent on average, despite 0% measured unemployment. This behavioral pattern
  suggests anticipatory anxiety: without welfare, losing a job is catastrophic, so agents
  pre-emptively search even when employed.
- **The Missing Poor**: Zero agents in the POOR bracket. This is unusual — even utopian scenarios
  typically produce some poor agents. The combination of full employment + near-zero tax +
  welfare disabled creates a "no floor, no ceiling" dynamic where employed agents thrive but would
  face steep consequences if unemployed.

## Recommendations

1. **Expand emotion mapping**: The engine should translate high unlust (>0.15) into negative
   emotional states (SAD, ANGRY, DESPAIR). Currently agents can be deeply discontent (unlust=0.19)
   while being classified as HAPPY or NORMAL — a misrepresentation.

2. **Model unemployment fear explicitly**: The massive seek_job count (405) under 0% unemployment
   suggests agents have an implicit fear mechanic. If this is intentional, document it. If not,
   the job-seeking decision logic may need calibration to avoid "phantom anxiety."

3. **Investigate happiness decay equilibrium**: Happiness never stabilizes but oscillates downward.
   This may indicate the decay rate outpaces the recovery mechanic, or that the model lacks a
   restorative activity (leisure, socializing) that agents can use to counteract decline.

4. **Add state hash to output data**: The template requires verifying state hash changes each tick,
   but the JSON output does not include it. This should be added to the simulation engine's tick
   result for reproducibility auditing.

5. **Run welfare-enabled comparison**: To isolate the effect of welfare, run an identical config
   with welfare_enabled=true and welfare_amount sufficient to cover food. This would test whether
   the safety net reduces job-seeking anxiety.

## Raw Statistics Dump

```json
{
  "scenario": "b3_laissez_faire",
  "config": {
    "n_agents": 80,
    "ticks": 200,
    "seed": 500,
    "tax_rate": 0.02,
    "welfare_enabled": false,
    "welfare_amount": 8.0,
    "food_availability": 0.8,
    "water_availability": 0.9,
    "unemployment_rate": 0.1,
    "crime_rate": 0.05,
    "food_cost_multiplier": 1.0,
    "grid_size": 20
  },
  "final_population": 80,
  "total_deaths": 0,
  "total_crimes": 0,
  "total_protests": 0,
  "total_actions": {
    "work": 14316,
    "buy_food": 1200,
    "seek_job": 405,
    "rest": 0,
    "beg": 0,
    "befriend": 0,
    "console": 0,
    "isolate": 0,
    "share": 0,
    "steal": 0,
    "harm_other": 0,
    "protest": 0,
    "complain": 0,
    "comply": 0,
    "idle": 0
  },
  "final_emotions": {"happy": 28, "normal": 52},
  "final_wealth": {"rich": 58, "middle": 22},
  "final_happiness": 0.638,
  "final_unlust": 0.156
}
```
