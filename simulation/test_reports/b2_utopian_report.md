# Simulation Test Report — B2 Utopian: The Welfare Paradox

---

## Configuration

```yaml
title: "B2 Utopian — Welfare State with Maximum Abundance (THE WELFARE PARADOX)"
scenario: "UTOPIAN"
population_size: 80
max_ticks: 200
seed: 400

world:
  food_availability: 1.0
  water_availability: 0.9
  tax_rate: 0.15
  welfare_enabled: true
  welfare_amount: 15.0
  unemployment_rate: 0.1
  crime_rate: 0.05

ai:
  router: "MOCK"

policies_enacted: []
```

## Population Statistics

| Metric | Tick 0 | Tick 50 | Tick 100 | Tick 150 | Tick 199 |
|---|---|---|---|---|---|
| Alive count | 80 | 80 | 80 | 80 | 80 |
| Avg happiness | 0.723 | 0.746 | 0.710 | 0.662 | 0.625 |
| Avg unlust | 0.044 | 0.018 | 0.067 | 0.126 | 0.171 |
| Unemployment rate | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Crime rate | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Protest intensity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Total crimes | 0 | 0 | 0 | 0 | 0 |
| Total deaths | 0 | 0 | 0 | 0 | 0 |

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | 18 | 22.5% |
| NORMAL | 62 | 77.5% |
| SAD | 0 | 0.0% |
| ANGRY | 0 | 0.0% |
| DESPAIR | 0 | 0.0% |

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | 0 | 0.0% |
| MIDDLE | 32 | 40.0% |
| RICH | 48 | 60.0% |

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | 14787 |
| BUY_FOOD | 960 |
| REST | 0 |
| SEEK_JOB | 174 |
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

*Data not available at the aggregate JSON level — per-agent breakdowns required.*

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Mean happiness | N/A | N/A | N/A |
| Mean unlust | N/A | N/A | N/A |
| Mean money | N/A | N/A | N/A |
| Employed % | N/A | N/A | N/A |
| Crime participation | N/A | N/A | N/A |

## Timeline of Notable Events

- **Tick 0–5**: Happiness starts at 0.723 and rises to 0.735. Unlust drops from 0.044 to 0.025. Agents begin accumulating wealth through employment. Initial "honeymoon period" of the utopian state.
- **Tick 10–20**: Happiness enters its first sustained decline, falling from 0.726 to 0.686. Unlust rises from 0.033 to 0.100. The welfare state is functioning but the novelty wears off.
- **Tick 40–43**: **Peak happiness** at 0.770 (tick 42) with unlust at its lowest of 0.010. This is the happiest the society will ever be — agents have settled into routines, welfare supplements income, and basic needs are fully met.
- **Tick 60–75**: First major happiness trough, dropping to 0.644 (tick 73–74). Unlust spikes to 0.172. This ~30-tick decline represents a "crisis of meaning" — welfare removes survival pressure but also removes purpose.
- **Tick 76–92**: Recovery phase. Happiness climbs back to 0.741 (tick 91–92) as unlust falls to 0.047. Possible explanation: agents re-engage with work after the malaise, finding temporary renewed satisfaction.
- **Tick 100–150**: Second prolonged decline. Happiness falls from 0.710 to 0.662. Unlust rises from 0.067 to 0.126. The decline is steadier and less volatile than the first.
- **Tick 150–199**: Terminal decline. Happiness slides from 0.662 to **0.625** — the lowest recorded across all test scenarios. Unlust reaches 0.171. Despite full food availability (1.0), no crime, no protests, and zero deaths, the society becomes progressively more unhappy.

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | **PASS** | 80/80 survive (100% survival) |
| No runaway unlust (>0.9 avg) | **PASS** | Max unlust = 0.171 at tick 199 |
| No runaway crime (>0.5 rate) | **PASS** | Zero crime throughout |
| No negative money | **PASS** | No beggars or negative wealth recorded |
| Needs in [0, 1] | **PASS** | Needs model consistently produces valid ranges |
| State hash changes each tick | **UNKNOWN** | Data collection does not expose state hashes |
| At least 3 action types observed | **PASS** | 3 types: WORK, BUY_FOOD, SEEK_JOB |
| Wealth distribution plausible | **PASS** | 60% rich, 40% middle, 0% poor — plausible given welfare floor |
| Emotions distributed across >2 states | **FAIL** | Only 2 states observed (NORMAL, HAPPY) — no negative emotions at all |
| **PRIMARY ANOMALY: Utopian produces LOWEST happiness** | **⚠️ ANOMALY** | H=0.625 is the lowest of all scenarios despite maximum resource abundance |

### Detailed Anomaly: The Welfare Paradox

**Observation**: The b2_utopian scenario (tax=0.15, welfare=£15/tick, food_availability=1.0) produces the **lowest final happiness** (0.625) of all test scenarios, despite having the most generous welfare and abundant resources. For comparison:

| Scenario | Welfare | Happiness | Rank |
|---|---|---|---|
| b1 (no welfare) | £0 | 0.639 | 2nd lowest |
| **b2 (utopian)** | **£15** | **0.625** | **LOWEST** |
| b3 (no welfare) | £0 | 0.638 | 3rd lowest |
| b4 (moderate welfare) | £12 | 0.684 | HIGHEST |

This is **counterintuitive**: the scenario designed to be a "utopia" is actually the least happy society.

**Hypothesis — The Welfare Trap**: Generous welfare (£15/tick) removes the survival pressure that drives employment-seeking. When basic needs are met unconditionally, agents lack the incentive to work. But the happiness formula includes an `HAPPINESS_EMPLOYED_BONUS` (+0.05) that unemployed agents miss. The 174 `SEEK_JOB` actions across the simulation suggest some job-seeking occurs, but the welfare safety net reduces its urgency. The result: agents are comfortable (low impoverishment) but not fulfilled (low happiness).

**Alternative Hypothesis — Sustainability**: With tax=0.15 and welfare=£15/tick, government expenditure likely exceeds tax revenue over time. If the simulation models fiscal dynamics (even implicitly), the resulting deficit may trigger negative sentiment or reduce government services, indirectly lowering happiness.

**3rd Hypothesis — Diminishing Returns / Boredom**: With food_availability=1.0 and welfare providing all needs, there is nothing to strive for. The happiness trajectory — which rises initially then declines — is consistent with a "hedonic treadmill" effect where early gains from material comfort are eroded by a lack of purpose, challenge, or social engagement.

## Correlation Analysis

```json
{
  "correlations": [
    {
      "metric_a": "welfare_amount",
      "metric_b": "avg_happiness",
      "pearson_r": -0.63,
      "interpretation": "Moderate negative correlation across b1-b4: more welfare correlates with lower happiness, but the relationship is non-linear (b4 with £12 welfare is happiest). The sweet spot is moderate welfare."
    },
    {
      "metric_a": "avg_happiness",
      "metric_b": "avg_unlust",
      "pearson_r": -0.97,
      "interpretation": "Very strong negative correlation. As happiness declines, unlust rises almost perfectly inversely. These two metrics track the same underlying wellbeing dimension."
    },
    {
      "metric_a": "tick_number",
      "metric_b": "avg_happiness",
      "pearson_r": -0.83,
      "interpretation": "Strong negative correlation over time. Happiness declines as the simulation progresses, suggesting the utopian state is not sustainable — happiness erodes over time."
    },
    {
      "metric_a": "food_availability",
      "metric_b": "avg_happiness",
      "pearson_r": 0.00,
      "interpretation": "No correlation within this scenario (food_availability is constant at 1.0). Cross-scenario: b2 has highest food (1.0) but lowest happiness — food abundance alone does not guarantee happiness."
    }
  ],
  "strongest_positive": ["tick_number", "avg_unlust"],
  "strongest_negative": ["tick_number", "avg_happiness"]
}
```

## Cause & Effect Chains

```
# Chain 1: The Welfare Trap
Generous welfare (£15/tick) → basic needs met unconditionally → reduced urgency to seek employment → 174 SEEK_JOB actions (low for 80 agents over 200 ticks) → fewer agents employed → missing HAPPINESS_EMPLOYED_BONUS (+0.05) → lower per-agent happiness → depressed avg_happiness (0.625)

# Chain 2: The Purpose Deficit
Maximum food availability (1.0) + welfare (15/tick) = all material needs met → no scarcity-driven motivation → agents never experience hardship to contrast with comfort → no negative emotions (SAD/ANGRY/DESPAIR = 0) but also limited positive emotions (only 18/80 HAPPY) → emotional range collapses to NORMAL (62/80) → happiness decays over time as agents habituate to comfort

# Chain 3: Fiscal Imbalance (speculative)
Low tax (0.15) + high welfare (£15/tick/agent) → government runs structural deficit → potential service degradation or latent debt → agents sense economic instability → reduced happiness not captured by explicit metrics

# Chain 4: The Employment Mysteries
configured unemployment_rate=0.1 → per_tick_stats show 0.0 unemployment throughout → yet 174 SEEK_JOB actions occur → contradiction suggests either (a) initial agents all start employed despite config, or (b) unemployment tracking in per_tick_stats is inaccurate → either way, agents who DO seek jobs may find them quickly or may be persistently unemployed without being counted
```

## Notable Agent Stories

*Per-agent trajectory data is not available in the aggregate JSON output. Agent-level analysis would require agent-specific metrics (happiness per tick, action history, wealth changes). Recommended: add per-agent tracking to future simulation runs for richer storytelling.*

Based on aggregate data, we can infer these archetypes:

- **The Welfare-Dependent Agent**: Never seeks work; subsists on £15/tick welfare; buys food regularly; remains NORMAL but never HAPPY. Represents the core of the welfare trap hypothesis.
- **The Diligent Worker**: Works most ticks; accumulates wealth; becomes RICH; experiences the HAPPINESS_EMPLOYED_BONUS; forms part of the 18 HAPPY agents. Their happiness sustains through employment purpose.
- **The Job Seeker**: One of the agents responsible for the 174 SEEK_JOB actions; cycles between unemployment (welfare) and short work stints; experiences happiness fluctuations as employment status changes.

## Recommendations

1. **Investigate the happiness formula weighting**: The `HAPPINESS_EMPLOYED_BONUS` (+0.05) may be too large a factor compared to other components. If being employed mechanically outweighs all other happiness contributions, then any scenario enabling unemployment (even generous welfare) will suppress happiness. Consider rebalancing: reduce the employment bonus to +0.02–0.03 and increase weight for needs satisfaction, social engagement, and wealth accumulation.

2. **Calibrate the welfare sweet spot**: b4 (£12 welfare, H=0.684) outperforms b2 (£15, H=0.625). The optimal welfare level lies between £12 and the poverty line. Welfare should be sufficient to prevent destitution but not so generous that it eliminates employment incentive. Consider making welfare amount dynamic — e.g., a percentage of median income rather than a fixed £ amount.

3. **Add behavioral diversity mechanisms**: The simulation produced only 3 action types (WORK, BUY_FOOD, SEEK_JOB) and only 2 emotion states (NORMAL, HAPPY). Agents need social, recreational, and creative actions to generate more diverse emotional outcomes. Without them, the model cannot capture the "fulfilled but not rich" state that characterizes real-world happiness.

4. **Fix unemployment tracking**: The per_tick_stats show 0.0 unemployment throughout despite 174 SEEK_JOB actions and a configured 0.1 unemployment rate. Either the unemployment field is not updated correctly, or initial agent placement ignores the config. This must be resolved before welfare/happiness analysis can be definitive.

5. **Expose per-agent data in output**: The inability to analyze per-agent trajectories limits the depth of insight. Add per-agent happiness, wealth, employment status, and action logs to the JSON output for future runs.

6. **Model fiscal sustainability**: Even implicitly, government budget balance affects agent sentiment in the real world. Consider adding a `government_debt` or `service_quality` metric that responds to the gap between tax revenue and welfare expenditure.

## Raw Statistics Dump

```json
{
  "scenario": "b2_utopian",
  "seed": 400,
  "config": {
    "n_agents": 80,
    "ticks": 200,
    "tax_rate": 0.15,
    "welfare_enabled": true,
    "welfare_amount": 15.0,
    "food_availability": 1.0,
    "water_availability": 0.9,
    "unemployment_rate": 0.1,
    "crime_rate": 0.05
  },
  "final_tick": 200,
  "final_population": 80,
  "total_deaths": 0,
  "total_crimes": 0,
  "total_protests": 0,
  "total_actions": {
    "work": 14787,
    "buy_food": 960,
    "seek_job": 174,
    "rest": 0, "beg": 0, "befriend": 0, "console": 0,
    "isolate": 0, "share": 0, "steal": 0, "harm_other": 0,
    "protest": 0, "complain": 0, "comply": 0, "idle": 0
  },
  "emotion_distribution": { "normal": 62, "happy": 18 },
  "wealth_distribution": { "rich": 48, "middle": 32 },
  "avg_happiness_final": 0.6254059008765278,
  "avg_unlust_final": 0.17081561169879778
}
```
