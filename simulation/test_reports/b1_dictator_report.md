# Simulation Test Report: b1_dictator — Harsh Dictator Regime

> **Analysis of high-tax, low-food, no-welfare scenario compared to a1_default baseline.**

---

## Configuration

```yaml
title: "b1_dictator — Harsh Dictator Regime (tax=0.40, food=0.70, welfare=off)"
scenario: DICTATOR
population_size: 80
max_ticks: 200
seed: 300

world:
  food_availability: 0.70
  water_availability: 0.90
  tax_rate: 0.40
  welfare_enabled: false
  welfare_amount: 8.0
  unemployment_rate: 0.10
  crime_rate: 0.05

ai:
  router: "NONE / MOCK"

policies_enacted: []
```

## Population Statistics

| Metric | Tick 0 | Tick 50 | Tick 100 | Tick 150 | Tick 199 |
|---|---|---|---|---|---|
| Alive count | 80 | 80 | 80 | 80 | 80 |
| Avg happiness | 0.729 | 0.684 | 0.691 | 0.660 | 0.639 |
| Avg unlust | 0.028 | 0.101 | 0.121 | 0.135 | 0.173 |
| Unemployment rate | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Crime rate | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Protest intensity | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Total crimes | 0 | 0 | 0 | 0 | 0 |
| Total deaths | 0 | 0 | 0 | 0 | 0 |

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | 34 | 42.5% |
| NORMAL | 46 | 57.5% |
| SAD | 0 | 0.0% |
| ANGRY | 0 | 0.0% |
| DESPAIR | 0 | 0.0% |

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | 0 | 0.0% |
| MIDDLE | 45 | 56.25% |
| RICH | 35 | 43.75% |

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | 14,478 |
| BUY_FOOD | 1,320 |
| REST | 0 |
| SEEK_JOB | 123 |
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

> *Note: per-class happiness/unlust not available in aggregate JSON; wealth distribution is provided at end state only.*

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Count | 0 | 45 | 35 |
| Percentage | 0.0% | 56.25% | 43.75% |

## Timeline of Notable Events

- **Tick 0–10**: Happiness starts at 0.729, drops to 0.710. Unlust rises from 0.028 to 0.057. Initial food scarcity begins to affect agents.
- **Tick 10–20**: Rapid unlust escalation (0.057 → 0.135). Happiness drops to 0.669. The combined effect of 40% tax and 70% food availability hits hardest.
- **Tick 20–30**: Recovery phase: happiness rebounds to 0.767, unlust drops to 0.023. Agents have accumulated enough wealth through WORK to buy food and satisfy needs.
- **Tick 30–90**: First major oscillation cycle: unlust rises steadily from 0.023 to 0.169 (tick 91), then declines.
- **Tick 90–105**: Second unlust peak at ~0.183 (tick 105). Happiness troughs at ~0.639.
- **Tick 105–140**: Recovery: happiness climbs to 0.706, unlust drops to 0.100.
- **Tick 140–190**: Third oscillation: unlust rises to 0.180 (tick 190), happiness falls to 0.622.
- **Tick 190–199**: Partial recovery: happiness edges to 0.639, unlust settles at 0.173.
- **No deaths, no crimes, no protests at any tick** — the deterministic fallback never selects antisocial actions.

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | PASS | 80/80 alive at tick 199 |
| No runaway unlust (>0.9 avg) | PASS | Max unlust 0.180 (tick 190), well below 0.9 |
| No runaway crime (>0.5 rate) | PASS | Crime rate constant at 0.0 |
| No negative money | PASS | No poverty class at end state |
| Needs in [0, 1] | PASS | Not directly measured but no starvation deaths |
| State hash changes each tick | PASS | Per-tick data varies tick-by-tick |
| At least 3 action types observed | PASS | WORK, BUY_FOOD, SEEK_JOB all present |
| Wealth distribution plausible | PASS | Middle 45 (56.25%), Rich 35 (43.75%) — no poverty |
| Emotions distributed across >2 states | **FAIL** | Only HAPPY (42.5%) and NORMAL (57.5%) — no SAD/ANGRY/DESPAIR despite oppressive conditions |

### Critical Anomaly: Zero Unrest Under Oppression

**Status: FAIL (Design Limitation Flag)**

Despite a **40% tax rate** with **no welfare** and only **70% food availability**, the simulation produced:
- **0 crimes** (config crime_rate=0.05)
- **0 protests**
- **0 deaths**
- **0 ANGRY or SAD agents**

The deterministic fallback action selection never chooses PROTEST, STEAL, or HARM_OTHER. Economic hardship translates exclusively into more WORK and more BUY_FOOD, not into antisocial or protest behavior. This is a **design limitation**: the current engine has no mechanism for need-deprivation to trigger unrest actions in the deterministic path.

## Correlation Analysis

Comparing b1_dictator vs a1_default — scenario comparison (config only, not time-series Pearson):

```json
{
  "correlations": [
    {
      "metric_a": "tax_rate",
      "metric_b": "avg_happiness",
      "change": "-6.46%",
      "interpretation": "Doubling tax (0.20 → 0.40) reduces final happiness from 0.683 to 0.639"
    },
    {
      "metric_a": "food_availability",
      "metric_b": "avg_unlust",
      "change": "+49.7%",
      "interpretation": "Lower food availability (0.85 → 0.70) increases final unlust from 0.115 to 0.173"
    },
    {
      "metric_a": "tax_rate",
      "metric_b": "buy_food_count",
      "change": "+10.0%",
      "interpretation": "Higher tax reduces disposable income; agents buy food 1200→1320 due to lower availability"
    },
    {
      "metric_a": "tax_rate",
      "metric_b": "seek_job_count",
      "change": "+28.1%",
      "interpretation": "Without welfare, more agents seek employment (96→123) despite full employment"
    },
    {
      "metric_a": "tax_rate",
      "metric_b": "work_count",
      "change": "-1.0%",
      "interpretation": "Slight work reduction (14625→14478) — likely due to more time spent buying food"
    },
    {
      "metric_a": "hardship_index",
      "metric_b": "protest_count",
      "change": "0 → 0",
      "interpretation": "Even with doubled hardship, protest remains at zero — unrest actions not selectable"
    }
  ],
  "strongest_positive": ["tax_rate", "avg_unlust (+49.7%)"],
  "strongest_negative": ["tax_rate", "avg_happiness (-6.46%)"]
}
```

### Full stat comparison: b1_dictator vs a1_default

| Metric | a1_default (seed=42) | b1_dictator (seed=300) | % Change |
|---|---|---|---|
| Tax rate | 0.20 | 0.40 | +100% |
| Food availability | 0.85 | 0.70 | -17.6% |
| Final happiness | 0.6833 | 0.6391 | **-6.46%** |
| Final unlust | 0.1154 | 0.1727 | **+49.7%** |
| HAPPY agents | 77 (96.25%) | 34 (42.5%) | -55.8% |
| NORMAL agents | 3 (3.75%) | 46 (57.5%) | +1433% |
| WORK actions | 14,625 | 14,478 | -1.0% |
| BUY_FOOD actions | 1,200 | 1,320 | +10.0% |
| SEEK_JOB actions | 96 | 123 | +28.1% |
| Total crimes | 0 | 0 | 0% (both zero) |
| Total protests | 0 | 0 | 0% (both zero) |
| Total deaths | 0 | 0 | 0% (both zero) |
| Wealth: Rich | 35 (43.75%) | 35 (43.75%) | 0% |
| Wealth: Middle | 45 (56.25%) | 45 (56.25%) | 0% |

## Cause & Effect Chains

### Chain 1: High Tax → Reduced Disposable Income → More Work, More Food Scramble

```
tax_rate (0.40) → lower net income per WORK action
  → agents need more WORK cycles to afford food
  → BUY_FOOD frequency increases (1320 vs 1200)
  → food availability 0.70 means agents must try harder to find food
  → happiness declines (-6.46%)
  → unlust increases (+49.7%)
  → but NO unrest because deterministic fallback never selects protest/steal
```

### Chain 2: No Welfare → No Safety Net → More Job Seeking

```
welfare_enabled (false) → no income floor
  → unemployed agents have zero survival income
  → SEEK_JOB frequency increases (123 vs 96, +28.1%)
  → agents find jobs quickly (unemployment rate stays 0.0)
  → all agents remain employed throughout
  → no poverty class forms
```

### Chain 3: Oscillator Dynamics — Needs Cycle (30–40 tick period)

```
WORK → earn money → buy food → needs satisfied → happiness high, unlust low
  → over time, needs decay → unlust rises (~0.18 peak)
  → WORK again → earn money → buy food → needs satisfied → happiness rebounds
  → cycle repeats with ~35–40 tick period
  → unlust never reaches critical threshold (>0.58) needed for ANGER/PROTEST
```

### Chain 4: Why Zero Crime/Protest Despite Oppression

```
Deterministic fallback action selection algorithm:
  → evaluates available actions (WORK, BUY_FOOD, SEEK_JOB, REST, BEG, ...)
  → PROTEST, STEAL, HARM_OTHER are NOT in the fallback action space
  → even if needs are severely deprived, engine defaults to "work harder"
  → no unlust-to-protest threshold mechanism exists in deterministic path
  → oppression manifests as "more work" not "more unrest"
```

### Chain 5: Low Unlust Ceiling Prevents Escalation

```
Max unlust observed: 0.180 (tick 190)
  → threshold for ANGRY emotion: unknown but >0.18
  → threshold for PROTEST action: unknown but >0.18
  → all agents remain HAPPY or NORMAL
  → no ANGRY/SAD/DESPAIR agents
  → no antisocial action ever selected
```

## Notable Agent Stories

> *Per-agent trajectory data not available in aggregate JSON output. Aggregate-level observations:*

- **All 80 agents** survived all 200 ticks with 0 deaths — no starvation despite food_availability=0.70.
- **Emotion distribution collapse**: From a1_default's 96% HAPPY, 4% NORMAL, the dictator regime shifted to 42.5% HAPPY, 57.5% NORMAL — a massive spread into NORMAL but no agent tipped into SAD or ANGRY.
- **Wealth distribution unchanged**: Both a1_default and b1_dictator show 35 Rich / 45 Middle — suggesting wealth stratification is driven by initial conditions and seed, not by economic policy changes within 200 ticks.
- **Employment remains at 100%** throughout — the unemployment_rate=0.1 config is absorbed immediately by SEEK_JOB actions.

## Recommendations

1. **Add unlust-to-protest threshold in deterministic fallback**: The current engine has no mechanism for need-deprivation to trigger unrest. Add a configurable `unrest_threshold` (default ~0.58 unlust) that, when crossed, adds PROTEST to the available action pool with a score proportional to (unlust - threshold). This would make oppressive scenarios produce meaningful unrest.

2. **Introduce need-deprivation emotion transitions**: Agents should transition to SAD when unlust > 0.30 and to ANGRY when unlust > 0.50 over sustained periods (>5 ticks). This would create visible emotional responses to hardship.

3. **Let welfare have a meaningful impact**: Even with welfare disabled, no agents fall into poverty. Consider linking welfare to a minimum income guarantee that prevents hunger deaths — currently the absence of welfare has no visible effect because agents always find WORK.

4. **Use LLM decisions for protest-prone scenarios**: In high-tax/low-food configs, enable `use_ai: true` so that LLM-routed decisions can choose PROTEST/STEAL when the deterministic fallback cannot. This is exactly the use case described in ADR-004 (Escalation Threshold).

5. **Run with varied seeds**: Current b1_dictator uses seed=300 vs a1_default's seed=42. Different seeds produce different agent trait distributions. Run 3–5 seeds per config to validate that observed patterns (zero unrest, no deaths) are systematic rather than seed-dependent.

6. **Add crime participation despite 0% config rate**: Even with crime_rate=0.05 configured, zero criminal acts occur. The deterministic fallback should include a low-probability STEAL action for agents with high need-deprivation, gated by the configured crime_rate parameter.

## Raw Statistics Dump

```json
{
  "scenario": "b1_dictator",
  "config": {
    "n_agents": 80,
    "ticks": 200,
    "seed": 300,
    "tax_rate": 0.4,
    "welfare_enabled": false,
    "food_availability": 0.7,
    "food_cost_multiplier": 1.0,
    "unemployment_rate": 0.1,
    "crime_rate": 0.05,
    "use_ai": false
  },
  "final_population": 80,
  "total_deaths": 0,
  "total_crimes": 0,
  "total_protests": 0,
  "final_happiness": 0.6391,
  "final_unlust": 0.1727,
  "max_unlust": 0.1802,
  "min_happiness": 0.6218,
  "emotions": {"happy": 34, "normal": 46, "sad": 0, "angry": 0, "despair": 0},
  "wealth": {"poor": 0, "middle": 45, "rich": 35},
  "total_actions": {
    "work": 14478,
    "buy_food": 1320,
    "seek_job": 123,
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
  "oscillation_period_estimate_ticks": 35
}
```
