# Simulation Test Report Template

All subagent-generated reports must follow this format. Replace `{PLACEHOLDER}` values.

---

## Configuration

```yaml
title: "{DESCRIPTIVE_TITLE}"
scenario: "{DICTATOR / UTOPIAN / LAISSEZ_FAIRE / DEFAULT / STRESS / BIZARRE}"
population_size: {N}
max_ticks: {T}
seed: {SEED}

world:
  food_availability: {0.0-1.0}
  water_availability: {0.0-1.0}
  tax_rate: {0.0-1.0}
  welfare_enabled: {true/false}
  welfare_amount: {FLOAT}
  unemployment_rate: {0.0-1.0}
  crime_rate: {0.0-1.0}

ai:
  router: "{MOCK / NONE}"

policies_enacted: [{LIST}]
```

## Population Statistics

| Metric | Tick 0 | Tick {T/4} | Tick {T/2} | Tick {3T/4} | Tick {T} |
|---|---|---|---|---|---|
| Alive count | | | | | |
| Avg happiness | | | | | |
| Avg unlust | | | | | |
| Unemployment rate | | | | | |
| Crime rate | | | | | |
| Protest intensity | | | | | |
| Total crimes | | | | | |
| Total deaths | | | | | |

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | | |
| NORMAL | | |
| SAD | | |
| ANGRY | | |
| DESPAIR | | |

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | | |
| MIDDLE | | |
| RICH | | |

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | |
| BUY_FOOD | |
| REST | |
| SEEK_JOB | |
| BEG | |
| BEFRIEND | |
| CONSOLE | |
| ISOLATE | |
| SHARE | |
| STEAL | |
| HARM_OTHER | |
| PROTEST | |
| COMPLAIN | |
| COMPLY | |
| IDLE | |

## Wealth-Stratified Metrics (end state)

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Mean happiness | | | |
| Mean unlust | | | |
| Mean money | | | |
| Employed % | | | |
| Crime participation | | | |

## Timeline of Notable Events

List events in chronological order with tick number:

- Tick {N}: {WHAT_HAPPENED} — {CAUSE_ANALYSIS}
- Tick {N}: {WHAT_HAPPENED} — {CAUSE_ANALYSIS}
- ...

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | PASS/FAIL | |
| No runaway unlust (>0.9 avg) | PASS/FAIL | |
| No runaway crime (>0.5 rate) | PASS/FAIL | |
| No negative money | PASS/FAIL | |
| Needs in [0, 1] | PASS/FAIL | |
| State hash changes each tick | PASS/FAIL | |
| At least 3 action types observed | PASS/FAIL | |
| Wealth distribution plausible | PASS/FAIL | |
| Emotions distributed across >2 states | PASS/FAIL | |

## Correlation Analysis

```json
{
  "correlations": [
    {
      "metric_a": "food_availability",
      "metric_b": "avg_happiness",
      "pearson_r": 0.XX,
      "interpretation": "Strong positive: more food = happier agents"
    },
    {
      "metric_a": "unemployment_rate",
      "metric_b": "crime_rate",
      "pearson_r": 0.XX,
      "interpretation": "..."
    }
  ],
  "strongest_positive": ["{A}", "{B}"],
  "strongest_negative": ["{A}", "{B}"]
}
```

## Cause & Effect Chains

```
{CHAIN_DESCRIPTION}
e.g.: Low food availability → high food decay → starvation → mass death → reduced population → lower crime rate
```

## Notable Agent Stories

Pick 3-5 agents with extreme trajectories:

- **Agent {ID}** (Class: {WEALTH_CLASS}, Traits: {KEY_TRAITS}): {STORY} — {SIGNIFICANCE}
- ...

## Recommendations

Based on findings, what parameters/values/policies need attention:

1. {RECOMMENDATION}
2. ...

## Raw Statistics Dump

```
{DUMP_ALL_METRICSDTO_AS_JSON}
```
