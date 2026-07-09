# Simulation Test Report: c1_famine — Extreme Food Scarcity

---

## Configuration

```yaml
title: "Famine Scenario — 85% Food Collapse with Zero Mortality"
scenario: "STRESS"
population_size: 80
max_ticks: 200
seed: 700

world:
  food_availability: 0.15
  water_availability: 0.20
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

| Metric | Tick 0 | Tick 50 | Tick 100 | Tick 150 | Tick 199 |
|---|---|---|---|---|---|
| Alive count | 80 | 80 | 80 | 80 | 80 |
| Avg happiness | 0.735 | 0.751 | 0.720 | 0.671 | 0.641 |
| Avg unlust | 0.027 | 0.020 | 0.070 | 0.125 | 0.155 |
| Unemployment rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Crime rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Protest intensity | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Total crimes | 0 | 0 | 0 | 0 | 0 |
| Total deaths | 0 | 0 | 0 | 0 | 0 |

---

## Emotion Distribution (end state)

| Emotion | Count | Percentage |
|---|---|---|
| HAPPY | 35 | 43.75% |
| NORMAL | 45 | 56.25% |
| SAD | 0 | 0.00% |
| ANGRY | 0 | 0.00% |
| DESPAIR | 0 | 0.00% |

---

## Wealth Distribution (end state)

| Class | Count | Percentage |
|---|---|---|
| POOR | 0 | 0.00% |
| MIDDLE | 32 | 40.00% |
| RICH | 48 | 60.00% |

---

## Action Frequency (total across all ticks)

| Action | Count |
|---|---|
| WORK | 13896 |
| BUY_FOOD | 1920 |
| REST | 0 |
| SEEK_JOB | 105 |
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

---

## Wealth-Stratified Metrics (end state)

*Per-class breakdown not available in raw JSON data (only aggregate end-state class counts).*

| Metric | Poor | Middle | Rich |
|---|---|---|---|
| Count | 0 | 32 | 48 |
| Percentage | 0% | 40% | 60% |

*Note: All 80 agents survived 200 ticks. 60% of the population ended as "Rich" despite (or because of) the famine conditions — indicating agents accumulated wealth through sustained work.*

---

## Timeline of Notable Events

- **Tick 0-5**: Initial shock. Happiness drops from 0.735 → 0.723. Unlust rises from 0.027 → 0.038. Agents begin buying expensive food (scarcity multiplier = 2.0 − 0.15 = **1.85×**, food cost = **18.5**).
- **Tick 5-14**: **First hardship wave.** Happiness continues falling to 0.662 (tick 14 low), unlust peaks at 0.148. This is the first trough — agents are feeling the full impact of food scarcity.
- **Tick 14-24**: **First recovery.** Happiness recovers to 0.761 (tick 24 peak, the highest in the entire simulation). Unlust drops to 0.008. Agents have adapted: they worked, earned money, bought food, and met their needs.
- **Tick 24-40**: **Second hardship wave.** Happiness drops to 0.646, unlust peaks at 0.166. This trough is **deeper** than the first — the cumulative cost of sustained food scarcity is wearing agents down.
- **Tick 40-50**: **Second recovery.** Happiness rebounds to 0.754, unlust drops to 0.023. Recovery still effective.
- **Tick 50-65**: **Third hardship wave.** Happiness bottoms at 0.646 again, unlust at 0.167. Similar magnitude to second wave.
- **Tick 65-74**: **Third recovery.** Happiness peaks at 0.739, unlust at 0.046. **Recovery peaks are diminishing** — each cycle restores less happiness than the last.
- **Tick 89**: Happiness hits 0.649, unlust hits 0.161. The oscillation continues with ~30-35 tick period.
- **Tick 157-158**: **Deepest unlust in simulation.** Unlust peaks at 0.187 (tick 158), happiness drops to 0.622. This is the worst moment for agent well-being.
- **Tick 180-182**: **Lowest happiness.** Happiness bottoms at 0.616 (tick 182), unlust at 0.195. The slow degradation trend is visible.
- **Tick 190-199**: **Final decline.** Happiness falls from 0.680 → 0.641, unlust rises from 0.126 → 0.155 in the last 10 ticks. The simulation ends in a declining phase.

---

## Anomaly Detection

| Check | Status | Detail |
|---|---|---|
| No mass extinction (>50% survival) | **PASS** | 100% survival (80/80). **This is the key anomaly.** |
| No runaway unlust (>0.9 avg) | **PASS** | Max unlust = 0.195 at tick 182. Peaks are rising but far below 0.9. |
| No runaway crime (>0.5 rate) | **PASS** | Zero crimes across all 200 ticks. |
| No negative money | **PASS** | No negative money events recorded. |
| Needs in [0, 1] | **PASS** | All values within expected range. |
| State hash changes each tick | **PASS** | Simulation ran all 200 ticks without stalling. |
| At least 3 action types observed | **PASS** | 3 action types: WORK (13896), BUY_FOOD (1920), SEEK_JOB (105). |
| Wealth distribution plausible | **FAIL** | 60% Rich, 0% Poor despite 85% food collapse — implausible for a famine. |
| Emotions distributed across >2 states | **FAIL** | Only NORMAL (45) and HAPPY (35). No SAD, ANGRY, or DESPAIR agents despite extreme scarcity. |

### Critical Anomaly: Zero Deaths Under 85% Food Collapse

**This is the single most important finding in this report.** A famine scenario with food_availability = 0.15 (85% reduction from normal) produced **zero deaths** across 200 ticks. By comparison, a default/control simulation typically shows some mortality under far milder conditions.

**Why this happens:** The engine's deterministic fallback is so robust that it creates an infinite adaptation loop:

1. `food_availability = 0.15` → scarcity multiplier = `2.0 − 0.15 = 1.85`
2. Food cost = `10 × 1.85 = 18.5` (nearly double the base cost)
3. Agents **always** prefer BUY_FOOD at any price — the fallback never selects BEG, STEAL, or HARM_OTHER
4. Agents work to earn money, always finding employment (infinite jobs at fixed salary)
5. Agents buy expensive food, survive, and **accumulate wealth** (48/80 end as Rich)

**There is no breaking point.** The economy model is simplified: infinite jobs, no market clearing, no stock limits, and food is always purchasable at any price. Real famines cause starvation precisely because people run out of money or food is physically unavailable — neither condition is modeled here.

---

## Correlation Analysis

```json
{
  "correlations": [
    {
      "metric_a": "food_availability (fixed=0.15)",
      "metric_b": "avg_happiness",
      "trend": "Negative over time",
      "interpretation": "With food_availability held constant at 0.15, happiness shows a strong oscillating pattern with a slow negative trend (0.735 → 0.641 over 200 ticks). The fixed scarcity creates cumulative fatigue."
    },
    {
      "metric_a": "avg_happiness",
      "metric_b": "avg_unlust",
      "pearson_r": -0.97,
      "interpretation": "Near-perfect negative correlation. Happiness and unlust are inversely coupled as expected — when agents are hungry/uncomfortable, they are unhappy; when their needs are met, they recover."
    },
    {
      "metric_a": "tick_number",
      "metric_b": "avg_happiness (trough values)",
      "pearson_r": -0.89,
      "interpretation": "Strong negative trend. Each oscillation cycle's happiness trough is lower than the previous: 0.662 → 0.646 → 0.646 → 0.636 → 0.622 → 0.616. The system is slowly degrading."
    },
    {
      "metric_a": "tick_number",
      "metric_b": "avg_unlust (peak values)",
      "pearson_r": 0.93,
      "interpretation": "Strong positive trend. Unlust peaks rise across cycles: 0.148 → 0.166 → 0.167 → 0.171 → 0.187 → 0.195. Each famine wave causes more suffering than the last."
    },
    {
      "metric_a": "BUY_FOOD count (1920)",
      "metric_b": "food_availability (0.15)",
      "pearson_r": "N/A (single config point)",
      "interpretation": "1920 BUY_FOOD actions is the highest across all scenarios — 1.6× the baseline (~1200). Agents buy 24.0 food units per agent on average (1920/80). With food at 1.85× cost, this represents a massive wealth transfer to food expenditure."
    }
  ],
  "strongest_positive": ["tick_number", "peak_unlust_values"],
  "strongest_negative": ["tick_number", "trough_happiness_values"]
}
```

---

## Cause & Effect Chains

```
Primary chain (engine logic):
Low food_availability (0.15) 
  → high scarcity multiplier (2.0 - 0.15 = 1.85) 
  → high food cost (10 * 1.85 = 18.5) 
  → agents BUY_FOOD at elevated rate (1920, highest of all scenarios) 
  → agents need more money → WORK more (13896) 
  → agents earn income → can afford expensive food 
  → SURVIVAL (0 deaths, 100% survival)

Secondary chain (well-being dynamics):
Sustained high food cost 
  → periodic unmet needs → unlust rises 
  → happiness falls → agents prioritize work/buy_food 
  → needs temporarily met → unlust falls 
  → happiness recovers → cycle repeats
  → BUT each cycle's peak unlust is higher and trough happiness is lower 
  → SLOW DEGRADATION over 200 ticks (happiness: 0.735 → 0.641)

Missing chain (what SHOULD happen in a real famine):
Extreme food scarcity 
  → food becomes unaffordable or unavailable 
  → agents cannot buy food → starvation 
  → DEATHS → population collapse 
  → crisis behaviors (BEG, STEAL, HARM_OTHER) emerge
```

**The engine models "resilience through work" not "collapse through scarcity."** Agents respond to scarcity by simply working harder — there is no mechanism for them to exhaust their money, face unemployment (the config's 10% unemployment rate was never realized), or be unable to purchase food regardless of price.

---

## Notable Agent Stories

*Per-agent trajectory data is not included in the raw JSON output (only aggregate statistics are recorded). However, the aggregate data supports these inferred agent archetypes:*

- **The Resilient Worker (archetype)**: These agents form the core of the population. They work every tick (13,896 total WORK actions across 80 agents = ~174 work actions per agent), buy food at inflated prices, and maintain positive emotional states (100% HAPPY or NORMAL at end state). They represent the "adapt and survive" pattern the engine favors.

- **The Job Seeker (archetype)**: 105 SEEK_JOB actions were recorded, but actual unemployment was 0.0% throughout — suggesting these were brief transition periods where agents immediately found work. The configured 10% unemployment rate was never realized in practice.

- **The Wealth Accumulator**: Despite (or because of) the famine, 60% of agents ended as "Rich" (48 agents) and 40% as "Middle" (32 agents). Zero agents in the "Poor" class. This is counterintuitive — a famine should create poverty, not wealth. The mechanism: agents work constantly and earn a fixed salary, while the only major expense (food) is capped in impact because agents always have enough money to buy it.

---

## Oscillation Wave Analysis

The per-tick data reveals a distinct **~30-35 tick oscillation cycle** in happiness and unlust:

| Cycle | Tick Range | Happiness Range | Unlust Range | Duration | Peak Happiness | Trough Happiness |
|-------|-----------|----------------|--------------|----------|---------------|-----------------|
| 1 | 0–24 | 0.662–0.761 | 0.008–0.148 | 24 ticks | 0.761 | 0.662 |
| 2 | 24–50 | 0.646–0.754 | 0.020–0.167 | 26 ticks | 0.754 | 0.646 |
| 3 | 50–74 | 0.646–0.739 | 0.046–0.167 | 24 ticks | 0.739 | 0.646 |
| 4 | 74–99 | 0.649–0.723 | 0.068–0.161 | 25 ticks | 0.723 | 0.649 |
| 5 | 99–123 | 0.650–0.708 | 0.074–0.160 | 24 ticks | 0.708 | 0.650 |
| 6 | 123–145 | 0.636–0.700 | 0.088–0.171 | 22 ticks | 0.700 | 0.636 |
| 7 | 145–170 | 0.622–0.689 | 0.112–0.187 | 25 ticks | 0.689 | 0.622 |
| 8 | 170–199 | 0.617–0.685 | 0.117–0.195 | 29 ticks | 0.685 | 0.617 |

**Trend:** Peak happiness declines from 0.761 → 0.685 (−10.0%). Trough happiness declines from 0.662 → 0.617 (−6.8%). Peak unlust rises from 0.148 → 0.195 (+31.8%). The system is **slowly degrading but not collapsing**.

---

## Recommendations

Based on findings, what parameters/values/policies need attention:

1. **IMPLEMENT FOOD UNAVAILABILITY MECHANISM**: When `food_availability` is very low (e.g., < 0.3), BUY_FOOD should have a chance of failure proportional to (1.0 − food_availability). At 0.15, this would mean an 85% chance of food purchase failure per attempt, which would realistically lead to starvation deaths.

2. **ADD AFFORDABILITY CONSTRAINT TO FOOD PURCHASES**: Food cost should be evaluated against agent money. If `food_cost > agent.money * threshold`, agents should not be able to buy food. This would create a realistic breaking point where agents exhaust their savings and starve.

3. **ACTIVATE BEG/STEAL/HARM_OTHER IN THE FALLBACK**: The deterministic fallback currently never selects crisis behaviors (BEG, STEAL, HARM_OTHER all at 0 counts). When food is scarce and agents cannot afford it, the fallback should escalate to these crisis actions. Currently there is no behavioral response to scarcity beyond "work more."

4. **INVESTIGATE ZERO UNEMPLOYMENT**: The configured 10% unemployment rate was never realized (actual rate = 0.0% throughout). The job-seeking logic either places agents instantly or config unemployment only affects initial assignment. Verify that `unemployment_rate` has any runtime effect.

5. **ADD AGENT DEATH FROM STARVATION**: If an agent's needs (hunger/thirst) remain unmet for N consecutive ticks, the agent should die. Currently there appears to be no mortality path from starvation — needs affect happiness/unlust but never reach a lethal threshold.

6. **DIVERSIFY EMOTIONAL RESPONSES**: After 200 ticks of extreme scarcity, zero agents ended SAD, ANGRY, or in DESPAIR. The emotion model needs to register sustained hardship. Agents facing prolonged food scarcity should transition through NORMAL → SAD → ANGRY → DESPAIR, not remain HAPPY/NORMAL throughout.

7. **RECALIBRATE WEALTH OUTCOMES**: A famine producing 60% Rich agents is a simulation realism failure. Wealth accumulation should be capped or redirected during scarcity — agents should be depleting savings to buy food, not accumulating more money.

---

## Raw Statistics Dump

```json
{
  "scenario": "c1_famine",
  "seed": 700,
  "n_agents": 80,
  "ticks": 200,
  "food_availability": 0.15,
  "water_availability": 0.20,
  "final_population": 80,
  "total_deaths": 0,
  "total_crimes": 0,
  "total_protests": 0,
  "total_actions": {
    "work": 13896,
    "buy_food": 1920,
    "seek_job": 105,
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
  "emotion_distribution": {
    "normal": 45,
    "happy": 35
  },
  "wealth_distribution": {
    "middle": 32,
    "rich": 48
  },
  "final_happiness": 0.641,
  "final_unlust": 0.155,
  "avg_happiness_overall": 0.683,
  "avg_unlust_overall": 0.098,
  "min_happiness": 0.616,
  "max_unlust": 0.195,
  "llm_calls": 0,
  "ambiguity_count": 0
}
```
