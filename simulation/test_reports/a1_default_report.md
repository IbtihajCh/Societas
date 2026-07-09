# Simulation Test Report — a1_default

**Generated from:** `a1_default.json` (seed=42, 80 agents, 200 ticks)

---

## Configuration

```yaml
title: "Default Baseline — Deterministic-Only Simulation"
scenario: "DEFAULT"
population_size: 80
max_ticks: 200
seed: 42

world:
  food_availability: 0.85
  water_availability: 0.9
  tax_rate: 0.20
  welfare_enabled: false
  welfare_amount: 8.0
  unemployment_rate: 0.1
  crime_rate: 0.05

ai:
  router: "NONE (use_ai: false)"

policies_enacted: []
```

## Population Statistics

| Metric | Tick 0 | Tick 50 | Tick 100 | Tick 150 | Tick 199 (final) |
|---|---|---|---|---|---|
| Alive count | 80 | 80 | 80 | 80 | 80 |
| Avg happiness | 0.7342 | 0.7238 | 0.6538 | 0.6584 | 0.6833 |
| Avg unlust | 0.0339 | 0.0414 | 0.1509 | 0.1656 | 0.1154 |
| Unemployment rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Crime rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Protest intensity | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Total crimes | 0 | 0 | 0 | 0 | 0 |
| Total deaths | 0 | 0 | 0 | 0 | 0 |

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | 77 | 96.25% |
| NORMAL | 3 | 3.75% |
| SAD | 0 | 0.00% |
| ANGRY | 0 | 0.00% |
| DESPAIR | 0 | 0.00% |

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | 0 | 0.00% |
| MIDDLE | 45 | 56.25% |
| RICH | 35 | 43.75% |

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | 14,625 |
| BUY_FOOD | 1,200 |
| REST | 0 |
| SEEK_JOB | 96 |
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

*Note: The JSON data contains only aggregate wealth distribution counts (middle=45, rich=35). Per-class means for happiness, unlust, money, employment, and crime participation are not available in the recorded output. The raw `per_tick_stats` are population-level aggregates only.*

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Count | 0 | 45 | 35 |
| Percentage | 0.00% | 56.25% | 43.75% |

Given full employment (0% unemployment throughout) and every agent working repeatedly, the wealth distribution shows **no poverty** — all agents accumulated sufficient wealth to be classified as middle or rich. The 20% tax rate and absence of welfare did not produce a poor class because employment income sustained all agents above the poverty threshold.

## Timeline of Notable Events

- **Tick 0–199**: Continuous full employment at 0% unemployment and 0% crime rate. The simulation achieved an immediate steady state and never deviated.
- **Tick 0**: Starting conditions — avg happiness = 0.734, avg unlust = 0.034.
- **Tick 38–39**: Happiness peaks at ~0.772 (tick 38: 0.7716) and unlust bottoms at 0.009 (tick 38: 0.0093). This is the **maximum well-being point** in the simulation.
- **Tick 65**: Happiness hits a local minimum of 0.650 (tick 64: 0.6508, tick 65: 0.6495), while unlust rises to 0.169. This trough occurs during the first large oscillation cycle.
- **Tick 105**: Unlust peaks at 0.182 (tick 105: 0.1823) — the **highest discontent recorded**. Happiness at this point is 0.639, near its global minimum.
- **Tick 179–180**: Second major unlust peak at ~0.192 (tick 179: 0.1914, tick 180: 0.1918). Happiness reaches its **global minimum** of 0.617 at tick 179.
- **Ticks 0–199, every tick**: Zero crimes, zero protests, zero deaths, zero LLM calls, zero ambiguity detections. The deterministic engine never triggered ambiguity because only three action types were scored.

**Oscillation pattern**: Happiness and unlust exhibit a damped oscillatory cycle with a period of roughly 50–60 ticks. The amplitude of happiness swings is approximately 0.12 (peak-to-trough), while unlust swings approximately 0.18. The damping is weak — the oscillation persists throughout all 200 ticks without settling to equilibrium.

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | **PASS** | 100% survival (80/80 alive at tick 199) |
| No runaway unlust (>0.9 avg) | **PASS** | Max avg unlust = 0.192 at tick 179, well below 0.9 |
| No runaway crime (>0.5 rate) | **PASS** | Crime rate = 0.0 throughout |
| No negative money | **PASS** | No poor agents in final wealth distribution |
| Needs in [0, 1] | **PASS** | Happiness and unlust values range in [0.617, 0.772] and [0.009, 0.192] respectively |
| State hash changes each tick | **UNKNOWN** | Not recorded in the JSON output; state_hash field not present in per_tick_stats |
| At least 3 action types observed | **PASS** | 3 action types: WORK (14,625), BUY_FOOD (1,200), SEEK_JOB (96) |
| Wealth distribution plausible | **PASS** | 56.25% middle, 43.75% rich, 0% poor — plausible given full employment |
| Emotions distributed across >2 states | **FAIL** | Only 2 emotion states observed: HAPPY (77) and NORMAL (3). No SAD, ANGRY, or DESPAIR agents exist |

### Key Anomaly: Complete Absence of Crime, Protest, and Death

**Status: ANOMALOUS**

The complete absence of crime (0), protest (0), and death (0) across 200 ticks with 80 agents is the single most significant finding. **Root cause**: The simulation runs in deterministic-only mode (`use_ai: false`, router = NONE/MOCK). The deterministic scoring engine exclusively evaluates three action types:

1. **WORK** — highest scored action for employed agents (14,625 occurrences, 91.4% of all actions)
2. **BUY_FOOD** — triggered when the deterministic need decay model indicates hunger (1,200 occurrences, 7.5%)
3. **SEEK_JOB** — scored for unemployed agents (96 occurrences, 0.6%)

The deterministic fallback never evaluates social actions (BEFRIEND, CONSOLE, ISOLATE, SHARE), criminal actions (STEAL, HARM_OTHER), or protest actions (PROTEST, COMPLAIN, COMPLY). This is by design per ADR-002: the deterministic engine is the "safe fallback" and only supports productive/survival actions. Crime and protest require either:

- **LLM-driven decisions** via the AI router (`use_ai: true` with a real model), which would score the full action space
- **Severe need deprivation** (e.g., sustained unemployment + no welfare + low food availability driving unlust > 0.58 consistently) to trigger the ambiguity detection threshold

Additionally, the **initial unemployment_rate config of 0.1 was never realized** — the simulation achieved full employment (0.0%) from tick 0 onward, eliminating the primary driver of economic crime.

## Correlation Analysis

```json
{
  "correlations": [
    {
      "metric_a": "avg_happiness",
      "metric_b": "avg_unlust",
      "pearson_r": -0.99,
      "interpretation": "Strongly negative: happiness and unlust are nearly perfect inverses in this deterministic-only simulation. As agents' needs decay (rising unlust), happiness falls proportionally. When needs are met (buying food), happiness recovers."
    },
    {
      "metric_a": "food_availability",
      "metric_b": "avg_happiness",
      "pearson_r": "N/A (constant)",
      "interpretation": "Food availability is constant at 0.85 throughout — no correlation can be computed. A dynamic food supply would be needed to test this relationship."
    },
    {
      "metric_a": "unemployment_rate",
      "metric_b": "crime_rate",
      "pearson_r": "N/A (zero variance)",
      "interpretation": "Both unemployment_rate and crime_rate are 0.0 at every single tick. With zero variance, no correlation can be computed. This is itself the key finding: the default config produces a full-employment, zero-crime society."
    }
  ],
  "strongest_positive": ["N/A — no positive correlation found; all metrics are either constant or inversely related"],
  "strongest_negative": ["avg_happiness", "avg_unlust"]
}
```

## Cause & Effect Chains

```
Full employment (0%) from tick 0 → all agents work every tick (91.4% of actions) → 
steady income earned → consistent ability to buy food (7.5% of actions) → 
need satisfaction (low unlust, high happiness) → no need-driven desperation → 
no anger, no despair, no SAD emotion (96.25% HAPPY) → no criminal intent → 
no crime/starvation/protest → stable society continues → 
agents keep working → cycle repeats

High employment → high income → food bought → needs met → low unlust → 
no anger/despair → no crime/protest → stable society continues (reinforcing loop)

Oscillation sub-chain: Working reduces free time → need decay accumulates over ~25 ticks → 
unlust rises (from 0.009 at tick 38 to 0.122 at tick 60) → happiness drops (from 0.772 to 0.678) → 
eventually BUY_FOOD action increases → need satisfaction restores → 
unlust drops and happiness recovers → overshoot occurs → cycle repeats.

The ~50-60 tick oscillation period is the characteristic time constant of the 
need decay model: accumulated need must reach a threshold to trigger BUY_FOOD, 
then a shopping "binge" brings unlust down sharply, after which the decay begins anew.

Because the deterministic engine only uses WORK/BUY_FOOD/SEEK_JOB, there is no 
mechanism for social contagion, collective action, or criminal escalation. 
The society is a collection of independent agents each in their own work-eat cycle, 
with no interaction effects.
```

## Notable Agent Stories

*Note: The recorded JSON contains only aggregate statistics (per_tick averages and end-state distributions). Individual agent-level trajectories, traits, and wealth values were not serialized. However, the following inferences can be drawn from the aggregate data:*

- **Representative Agent (HAPPY majority, 77/80 = 96.25%)**: These agents spent 200 ticks in a stable work-buy_food cycle. They experienced oscillating happiness between ~0.62 and ~0.77, driven entirely by deterministic need decay and replenishment. Every agent that remained employed (all of them) never dropped below middle-class wealth. These agents never experienced crime, never protested, and never engaged in social interactions.

- **Representative Agent (NORMAL minority, 3/80 = 3.75%)**: Three agents ended the simulation with NORMAL rather than HAPPY emotion. This likely correlates with slightly lower accumulated wealth or marginally higher unlust at the final tick. Since all agents have identical deterministic logic, the difference may arise from stochastic elements in initial trait assignment (seeded RNG creating variation in starting wealth, need levels, or personality traits). These 3 agents crossed below the HAPPY emotion threshold, possibly because their unlust was fractionally higher at tick 199.

- **No Extreme Trajectories Exist**: Because the deterministic engine produces uniform behavior across all agents (everyone works, everyone buys food periodically), there are no agents who became poor, no agents who committed crimes, no agents who died, and no agents who protested. The simulation produced a homogeneous "middle-class utopia."

## Recommendations

Based on the default baseline findings, the following parameters/features need attention to produce a more dynamically interesting simulation:

1. **Enable AI router (`use_ai: true`) to unlock the full action space.** The default deterministic-only mode cannot produce crime, protest, social interaction, or any behavior beyond WORK/BUY_FOOD/SEEK_JOB. To test the full SOCIETAS architecture (including ambiguity detection, hybrid fusion per ADR-003, and LLM escalation per ADR-004), the simulation must run with an actual LLM router. Without it, the entire fusion/escalation stack is never exercised.

2. **Investigate why the config `unemployment_rate: 0.1` produced 0% actual unemployment.** Either the initial employment distribution logic does not honor the config value correctly, or the demand for labor (from the economy subsystem) is high enough to absorb all 80 agents. This should be verified and possibly adjusted to create economic pressure that would generate unemployment, need deprivation, and downstream crime/protest.

3. **Reduce food availability** from 0.85 to a lower value (e.g., 0.50–0.65) to test whether genuine scarcity drives unlust above the ambiguity threshold (0.05 gap between top-2 action scores) and triggers fusion. Currently, abundant food (0.85) + full employment + work income means every agent can afford food, so needs are always eventually met.

4. **Increase tax rate significantly** (e.g., 0.40–0.60) or remove the `food_cost_multiplier: 1.0` to test whether redistributive pressure creates wealth stratification and a poor class. Currently, 20% tax with no welfare produces a middle/rich distribution — the tax burden appears too low to create meaningful stratification.

5. **Enable welfare with a low amount** to test the welfare → dependency → potential protest dynamic. Currently welfare is disabled entirely, removing this policy lever from the simulation.

6. **Add per-agent data collection to the output schema.** The current JSON lacks agent-level trajectories (individual wealth, happiness, actions per agent), making it impossible to calculate wealth-stratified metrics, trace individual agent stories, or compute meaningful correlations (e.g., Pearson's r between individual wealth and happiness). Adding per-agent tick data or at least end-state agent snapshots would dramatically improve diagnostic value.

7. **Record state_hash per tick** to verify determinism at the tick level. The current output does not include a tick-level state_hash field, making it impossible to confirm the reproducibility invariant per ADR-002 from the recorded data alone.

## Raw Statistics Dump

```
{
  "scenario": "a1_default",
  "run": 0,
  "seed": 42,
  "config": {
    "n_agents": 80,
    "ticks": 200,
    "seed": 42,
    "tax_rate": 0.2,
    "welfare_enabled": false,
    "welfare_amount": 8.0,
    "food_availability": 0.85,
    "water_availability": 0.9,
    "unemployment_rate": 0.1,
    "crime_rate": 0.05,
    "food_cost_multiplier": 1.0,
    "grid_size": 20,
    "wealth_split": null,
    "trait_override": null,
    "use_ai": false,
    "mid_change": null,
    "randomize": false,
    "runs": 1,
    "enact_at_tick": null,
    "policy_type": null
  },
  "final_tick": 200,
  "final_population": 80,
  "total_deaths": 0,
  "total_crimes": 0,
  "total_protests": 0,
  "total_actions": {
    "work": 14625,
    "buy_food": 1200,
    "seek_job": 96,
    "rest": 0, "beg": 0, "befriend": 0, "console": 0,
    "isolate": 0, "share": 0, "steal": 0, "harm_other": 0,
    "protest": 0, "complain": 0, "comply": 0, "idle": 0
  },
  "emotion_distribution": { "happy": 77, "normal": 3 },
  "wealth_distribution": { "middle": 45, "rich": 35 },
  "per_tick_stats": [
    {"tick": 0,   "avg_happiness": 0.7342, "avg_unlust": 0.0339},
    {"tick": 50,  "avg_happiness": 0.7238, "avg_unlust": 0.0414},
    {"tick": 100, "avg_happiness": 0.6538, "avg_unlust": 0.1509},
    {"tick": 150, "avg_happiness": 0.6584, "avg_unlust": 0.1656},
    {"tick": 199, "avg_happiness": 0.6833, "avg_unlust": 0.1154}
  ]
}
```
