# Master Test Plan — Simulation Engine v1.0

**Date:** 2026-07-09
**Purpose:** Exhaustive stress-testing, anomaly detection, correlation analysis, and boundary exploration.
Reports stored in `simulation/test_reports/`.

---

## Report Format

Every subagent uses [report-template.md](report-template.md). Reports include:
- Configuration YAML, population stats table across 5 timepoints
- Emotion/wealth/action distributions at end state
- Wealth-stratified breakdown, anomaly checklist, correlation matrix
- Cause-effect chains, notable agent stories, recommendations

## How Subagents Run Tests

Each subagent writes a 10-line runner script using the engine, executes it with the venv Python, collects `SimulationMetricsDTO` and `TickResult` data, then fills the report template. No code modifications — read-only execution.

---

## Test Scenarios (28 total)

### Group A: Baseline & Stability (4 tests)

| # | Scenario | Agents | Ticks | Seed | Key Parameters | Purpose |
|---|---|---|---|---|---|---|
| A1 | Default baseline | 80 | 200 | 42 | all defaults | Verify default config produces stable society |
| A2 | Default extended | 80 | 500 | 42 | all defaults | Will society hold together over time? |
| A3 | Small population | 30 | 500 | 100 | defaults | Fewer interactions = different dynamics? |
| A4 | Large population | 200 | 200 | 200 | defaults, 30x30 grid | Scalability and interaction density |

### Group B: Governance Styles (4 tests)

| # | Scenario | Agents | Ticks | Tax | Welfare | Food | Purpose |
|---|---|---|---|---|---|---|---|
| B1 | Harsh Dictator | 80 | 200 | 0.40 | disabled | 0.70 | High extraction + low freedom |
| B2 | Utopian/Wise | 80 | 200 | 0.15 | £15/tick | 1.0 | Generous welfare, low tax |
| B3 | Laissez-Faire | 80 | 200 | 0.02 | disabled | 0.80 | Minimal state intervention |
| B4 | Balanced Welfare State | 80 | 200 | 0.25 | £12/tick | 0.90 | Scandinavian model |

### Group C: Extreme World Conditions (5 tests)

| # | Scenario | Food | Water | Unemploy | Crime | Purpose |
|---|---|---|---|---|---|---|
| C1 | Famine | 0.15 | 0.20 | 0.12 | 0.05 | Near-zero resources — survival test |
| C2 | Drought + Recession | 0.30 | 0.15 | 0.30 | 0.10 | Compound crisis |
| C3 | Abundance | 1.0 | 1.0 | 0.02 | 0.01 | Perfect world — utopia? |
| C4 | High Crime Baseline | 0.80 | 0.80 | 0.12 | 0.30 | Dangerous society |
| C5 | Unstable World | 0.50 | 0.50 | 0.50 | 0.25 | Everything broken simultaneously |

### Group D: Extreme Agent Configurations (4 tests)

| # | Scenario | Wealth Split | Trait | Purpose |
|---|---|---|---|---|
| D1 | All Poor | 100/0/0 | defaults | Zero wealth — class collapse? |
| D2 | All Rich | 0/0/100 | defaults | Everyone wealthy — boredom? |
| D3 | High Morality Society | 50/35/15 | morality Beta(8,2) | Very moral — no crime? |
| D4 | Low Morality Society | 50/35/15 | morality Beta(2,8) | Criminal society |
| D5 | High Anger | 50/35/15 | anger Beta(8,2) | Volatile population |

### Group E: Bizarre Values (5 tests)

| # | Scenario | Key Change | Purpose |
|---|---|---|---|
| E1 | Zero Tax | tax_rate=0.0 | No revenue — what breaks? |
| E2 | Maximum Welfare | welfare=50 | Everyone gets paid |
| E3 | Gigantic Food Cost | BASE_FOOD_COST=200 | Can anyone afford food? |
| E4 | Huge Grid, Few Agents | 50x50 grid, 50 agents | Sparse — few interactions |
| E5 | Tiny Grid, Many Agents | 5x5 grid, 80 agents | Overcrowded — constant interaction |

### Group F: Policy Dynamics (3 tests)

| # | Scenario | Mid-Sim Change | Purpose |
|---|---|---|---|
| F1 | Tax Cut Midway | Start tax=0.40, at t=100 tax=0.15 | Does tax cut improve happiness? |
| F2 | Welfare Introduction | Start welfare=off, at t=100 welfare=£15 | Does welfare reduce crime/unlust? |
| F3 | Police State Enactment | At t=50 enact strict police policy | Does enforcement help or hurt? |

### Group G: AI-Hybrid (2 tests)

| # | Scenario | Router | Purpose |
|---|---|---|---|
| G1 | With MockAI | MockAIRouter active | Does AI routing change outcomes vs pure? |
| G2 | Identical Seed With/Without | Compare same seed ± MockAI | Quantify AI decision impact |

### Group H: Randomized Fuzzing (1 test)

| # | Scenario | Method | Purpose |
|---|---|---|---|
| H1 | Random World Fuzz | 10 runs with random parameters, compare stats | Find parameter combinations that cause collapse |

---

## Correlation Metrics to Compute

Each subagent computes these metrics per tick and across all agents:

| Independent Variable | Dependent Variables |
|---|---|
| food_availability | avg_unlust, avg_happiness, death_rate, crime_rate |
| tax_rate | avg_money, protest_intensity, unemployment_rate, crime_rate |
| welfare_amount | avg_unlust (poor), crime_rate, unemployment_rate |
| unemployment_rate | crime_rate, avg_unlust, avg_happiness |
| avg_unlust | crime_rate, death_rate, protest_intensity |
| crime_rate | avg_safety_need, protest_intensity, avg_happiness |
| population_density | social_need, crime_rate, anger_rate |
| morality_avg | crime_rate, share_actions, protest_actions |
| wealth_inequality | protest_intensity, crime_rate |

## Expected Findings (Hypotheses to Test)

1. **Unlust → Crime chain**: High unlust → low morality gate → more HARM_OTHER/STEAL → higher crime rate → lower safety → higher unlust (vicious cycle)
2. **Welfare → Stability**: Welfare enabled → poor agents survive longer → less begging/stealing → lower crime → more social stability
3. **Tax → Protest**: High tax → less disposable income → more PROTEST actions → higher protest_intensity
4. **Scarcity → Death**: Low food_availability → high food cost → agents can't afford → starvation → death cascade
5. **Morality → Crime**: High morality_avg → fewer criminal actions → lower crime_rate → higher safety → positive feedback
6. **Overcrowding → Interaction**: Tiny grid → more nearby agents → more BEFRIEND/SHARE but also more STEAL/HARM
7. **AI vs Deterministic**: MockAIRouter should select different actions (sometimes) → slightly different macro outcomes

---

## Subagent Dispatch Order

**Wave 1** (8 parallel): A1, A2, A3, A4, B1, B2, B3, B4
**Wave 2** (8 parallel): C1, C2, C3, C4, C5, D1, D2, D3
**Wave 3** (7 parallel): D4, D5, E1, E2, E3, E4, E5
**Wave 4** (5 parallel): F1, F2, F3, G1, G2
**Wave 5** (1): H1 (random fuzzing — long running)

Wait for each wave to complete and verify reports before launching the next.
