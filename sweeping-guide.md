# Sweeping Guide

The complete operating manual for parameter sweeping, scenario testing, and edge-case discovery in the SOCIETAS deterministic simulation engine.

This guide is self-contained. Any agent — subagent dispatched to do sweeping, future Simulation Engineer session, or human contributor — can read this and know exactly how to run, analyze, and report on a sweep.

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Background: The Simulation Engine](#2-background-the-simulation-engine)
3. [The Sweep Runner Architecture](#3-the-sweep-runner-architecture)
4. [Sweep Categories](#4-sweep-categories)
5. [Running a Sweep](#5-running-a-sweep)
6. [Output Format](#6-output-format)
7. [Analysis Methodology](#7-analysis-methodology)
8. [Report Format](#8-report-format)
9. [Delegation to Subagents](#9-delegation-to-subagents)
10. [Worked Examples](#10-worked-examples)
11. [Pitfalls & Best Practices](#11-pitfalls--best-practices)
12. [Glossary](#12-glossary)

---

## 1. Purpose & Scope

### 1.1 What is "sweeping"?

A **parameter sweep** is a systematic, automated test that runs the same simulation many times with one parameter varied and all others held constant. The output is a table of `(parameter_value → outcome_metrics)` pairs that lets you see how a parameter affects the world.

Sweeping answers questions like:
- "What does `FOOD_DECAY_RATE=0.05` do differently from `0.01`?"
- "At what value of `ANGRY_UNLUST_THRESHOLD` do protests start firing?"
- "Is `tax_rate=0.5` sustainable, or does it cause collapse?"
- "Does `GRID_SIZE=80` produce different outcomes from `GRID_SIZE=10`?"

### 1.2 What sweeping is for

| Use case | What it tells you |
|---|---|
| **Bug detection** | A parameter is "dead" if all values produce identical output (no measurable effect) |
| **Threshold finding** | At what value does a behavior cliff appear (e.g., protests start at unlust < 0.4)? |
| **Tuning** | What value of a parameter gives the most interesting/realistic behavior? |
| **Robustness** | Does the simulation behave sensibly across the full parameter range? |
| **Sensitivity** | How much does outcome change per unit of parameter change? |
| **Equilibrium detection** | Is there an attractor the simulation converges to regardless of starting state? |

### 1.3 What sweeping is NOT for

- **Performance testing** — use `pytest-benchmark` or `tests/performance/`
- **LLM behavior testing** — that is the AI subsystem, not Layer 1
- **Backend API testing** — use `tests/unit/backend/`
- **One-off experiments** — if you only need to try one value, just run the simulation

### 1.4 The cardinal rule

**A parameter sweep is only as good as its coverage of the parameter's full range.** If you sweep `food_availability` from 0.0 to 1.0 in 0.1 steps, you might miss the death cliff at 0.05. Always think about what range matters and choose values that span the behaviorally interesting range.

---

## 2. Background: The Simulation Engine

### 2.1 The deterministic engine contract

The simulation engine has these guarantees:

1. **Determinism** — same `seed` + same config = identical output (bit-for-bit, given identical Python version)
2. **No LLM in Layer 1** — the simulation runs entirely without external model calls; ambiguity is *flagged* but not resolved
3. **All randomness is seeded** — every `random.*` or `numpy.random` call goes through `shared.utilities.deterministic_rng.DeterministicRNG`

This means a sweep is **reproducible**. If `sweep_2024_01_15.json` shows `FOOD_DECAY_RATE=0.036 → 80 dead`, you can re-run the same configuration and get the same result. This is the foundation of all sweeping.

### 2.2 Where parameters live

All tunable constants live in `shared/constants/defaults.py` (and a secondary file `shared/constants/simulation_constants.py` for structural maps like `SALARY_RANGES` and `WEALTH_CLASS_DISTRIBUTION`).

Each constant looks like:
```python
FOOD_DECAY_RATE: float = 0.018
HAPPY_THRESHOLD: float = 0.65
GRID_SIZE: int = 20
```

The complete catalog of ~93 scalar constants in `defaults.py` covers:
- **Emotion thresholds** (HAPPY_THRESHOLD, SAD_THRESHOLD, ANGRY_UNLUST_THRESHOLD, DESPAIR_UNLUST_THRESHOLD, etc.)
- **Unlust weights** (UNLUST_FOOD_WEIGHT, UNLUST_WATER_WEIGHT, etc.)
- **Need decay rates** (FOOD_DECAY_RATE, SOCIAL_DECAY_RATE, SLEEP_DECAY_RATE, etc.)
- **Death parameters** (DESPAIR_MORTALITY_RATE, FOOD_DEATH_THRESHOLD, JOB_LOSS_RATE, etc.)
- **Economy** (BASE_FOOD_COST, SALARY_MULTIPLIER_*, FOOD_COST_MULTIPLIER_*, etc.)
- **World availability** (FOOD_AVAILABILITY_DEFAULT, WATER_AVAILABILITY_DEFAULT, SCARCITY_BASE)
- **Happiness weights** (HAPPINESS_FOOD_WEIGHT, HAPPINESS_WATER_WEIGHT, etc.)
- **Adler psychology** (ADLER_GAP_THRESHOLD, ADLER_*_PER_GAP, etc.)
- **Action parameters** (SEEK_JOB_BASE_CHANCE, BEG_MAX_AMOUNT, STEAL_*, SHARE_*, etc.)
- **Grid/spatial** (GRID_SIZE, INTERACTION_RADIUS)
- **Decision** (DECISION_STAGGER_INTERVAL, MORAL_DILEMMA_*_THRESHOLD)

Plus ~50 additional sweepable fields in dataclass schemas (`shared/schemas/*.py`) and ~20 policy-fallback values in `simulation/policies/policy_fallback.py`.

### 2.3 The critical pitfall: module-level imports

This is the **most important fact** for any agent doing sweeping. When code does:

```python
# In simulation/agents/unlust_engine.py
from shared.constants.defaults import UNLUST_FOOD_WEIGHT, UNLUST_MORALITY_GATE
```

The `UNLUST_FOOD_WEIGHT` symbol is bound in `unlust_engine`'s namespace **at import time**. If you change `defaults.UNLUST_FOOD_WEIGHT` later, `unlust_engine.UNLUST_FOOD_WEIGHT` still points to the old value. The two are now **decoupled references**.

This means: **You cannot override a constant by editing `defaults.py` after import.** You must patch the constant in every module that imported it.

### 2.4 The patch table (the solution)

The sweep runner solves this with a manual table:

```python
_PATCH_MODULES: dict[str, list[str]] = {
    "UNLUST_FOOD_WEIGHT": ["simulation.agents.unlust_engine"],
    "ANGRY_UNLUST_THRESHOLD": [
        "simulation.agents.emotion_engine",
        "simulation.agents.decision_engine",
        "simulation.agents.unlust_engine",
    ],
    # ... ~80 more entries
}
```

For each constant, the table lists every module that has imported it. The `_patch_constant()` function uses `importlib.import_module()` to get each module, then `setattr()` to update the bound name.

**This is fragile and must be maintained.** When you add a new `from shared.constants.defaults import X` to any simulation module, you MUST add `X` (and your module path) to `_PATCH_MODULES` in `sweep_runner.py`. A missing entry means the parameter won't actually change during the sweep.

### 2.5 The "comfortable equilibrium"

The default config has been tuned to produce a stable "comfortable middle-class society" attractor:
- avg_happiness ≈ 0.685
- avg_unlust ≈ 0.215
- 0 deaths, 0 crimes, 0 protests
- 1/80 unemployed
- 0 poor, 58 middle, 22 rich (all agents are middle or rich)

Most parameters do nothing in this attractor because:
- Need is well above death thresholds (so no deaths)
- Unlust is well below emotion thresholds (so no anger/despair)
- Unlust is well below the morality gate (so no crime)
- Morality is well above crime gates (so no theft)
- Social needs are satisfied (so no isolation)

**A "DEAD" parameter result is often because the default config never enters the state where the parameter matters.** This is not necessarily a bug — it may be a parameter that activates only under stress. To verify, sweep the parameter **combined with a stress condition** (e.g., low food, high unlust).

---

## 3. The Sweep Runner Architecture

### 3.1 File location

```
simulation/test_reports/sweep_runner.py
```

This is the canonical tool. It is ~400 lines of Python. Do not reinvent this.

### 3.2 Public API

| Function | Purpose |
|---|---|
| `run_simulation(param_name, param_value, config)` | Run a single simulation with the given param override; return metrics dict |
| `run_sweep(param_names, config)` | Run a sweep over multiple params; return `{param: {value: metrics}}` |
| `build_world(**overrides)` | Construct a `SimulationState` with the given config; used internally |
| `DEFAULT_CONFIG` | The baseline config (n_agents=80, ticks=200, seed=42, food=0.85, etc.) |
| `PARAMETER_OVERRIDES` | The list of values to try for each parameter |
| `SWEEP_GROUPS` | Predefined groups of parameters (`world`, `unlust`, `needs`, `emotion`, `economy`, `death`, `actions`, `adler_grid`, `scale`) |
| `METRICS` | The list of metrics captured per run |

### 3.3 The metrics

Each simulation run produces a metrics dict with these keys:

| Metric | Type | What it measures |
|---|---|---|
| `param` | str | The parameter name that was swept (echo) |
| `value` | float/int | The value used in this run (echo) |
| `avg_happiness` | float | Mean happiness across all (living) agents, averaged over all ticks |
| `avg_unlust` | float | Mean unlust across all (living) agents, averaged over all ticks |
| `final_dead` | int | Number of agents dead at end |
| `crimes_total` | int | Sum of `crimes_committed` across all agents |
| `protests_total` | int | Sum of `protest_count` across all agents |
| `unique_actions` | int | Number of distinct `ActionType` values that fired at least once |
| `emotion_states` | int | Number of distinct `EmotionType` values observed |
| `wealth_classes` | int | Number of distinct `WealthClass` values present among living agents |
| `final_unemployment` | float | Fraction of living agents who are unemployed (0.0 to 1.0) |
| `wealth_gini` | float | Gini coefficient of wealth distribution (0.0 = perfect equality) |
| `happiness_variance` | float | Variance of happiness across all agent-tick samples |
| `action_counts` | dict[str, int] | Top 10 actions by frequency (e.g., `{"work": 9713, "rest": 2595, ...}`) |
| `final_alive` | int | Number of agents alive at end |
| `final_wealth` | dict[str, int] | Count of agents in each wealth class (`{"poor": 0, "middle": 58, "rich": 22}`) |
| `final_emotions` | dict[str, int] | Count of agents in each emotion (`{"happy": 67, "normal": 13}`) |

### 3.4 The PATCH_MODULES table — maintenance contract

When you add code that imports from `shared.constants.defaults`:

1. **Add your module path** to `_PATCH_MODULES` in `sweep_runner.py`
2. **Add values to sweep** to `PARAMETER_OVERRIDES` if appropriate
3. **Add your parameter** to the relevant `SWEEP_GROUPS` group (or create a new group)
4. **Test the sweep** runs without errors
5. **Document** in the relevant sweep report

If a parameter is missing from `_PATCH_MODULES`, the sweep will silently show "DEAD" results because the patched value never reaches the consuming module. This is the most common cause of false negatives.

### 3.5 The reset mechanism

`_reset_all_constants()` is called at the start of every `_patch_constant()` call. This ensures:
- A parameter changed in run N does not leak into run N+1
- All constants are reset to their original `defaults.py` values before the next patch

This is critical because some modules cache the values at function definition time (e.g., default argument values), and without reset, stale values would persist.

---

## 4. Sweep Categories

There are 5 distinct types of sweeping. Choose the right one for the question you're asking.

### 4.1 Parameter sweep (the default)

**Question:** "How does parameter X affect outcomes?"

**Method:** Vary one parameter across a range, hold all others at default. Compare metrics.

**Example:** Sweep `FOOD_DECAY_RATE` from 0.0 to 0.072 → see when mass death starts.

**Output:** `{FOOD_DECAY_RATE: {"0.0": {...}, "0.009": {...}, "0.018": {...}, ...}}`

**Time per run:** 5-15 seconds for 200-tick 80-agent simulation.

### 4.2 Scenario sweep (curated conditions)

**Question:** "What happens under a specific scenario?"

**Method:** Set a specific combination of parameters (not a range), run for many ticks, report the trajectory.

**Example:** "Total famine" scenario: `food_availability=0.0, water_availability=0.0, tax_rate=0.5, welfare_amount=0` → see how fast society collapses.

**Output:** A single run's metrics, plus a time-series of metrics per tick.

**Time per run:** 30-60 seconds for 1000-tick scenario.

### 4.3 Edge case sweep (boundary conditions)

**Question:** "Does the simulation break at the extremes?"

**Method:** Run with parameters pushed to their limits (0, 1, infinity, very small populations, very large populations).

**Example:** 1 agent for 200 ticks, 1000 agents for 50 ticks, 200 ticks with 0 food, 200 ticks with 0 money.

**Output:** Behavior at boundaries, often reveals bugs.

**Time per run:** Varies wildly (1-agent runs are 0.1s; 1000-agent runs are 30s+).

### 4.4 Scale sweep

**Question:** "How does the simulation scale?"

**Method:** Vary `n_agents` or `ticks` while holding parameters constant.

**Example:** Sweep `n_agents` from 10 to 1000 → see if behavior is stable across scales.

**Output:** Performance and outcome metrics vs scale.

**Time per run:** 1s (10 agents) to 60s+ (1000 agents).

### 4.5 Regression sweep

**Question:** "Did a code change break previously-working behavior?"

**Method:** Re-run a known-good sweep and compare to the saved JSON. Look for changes.

**Example:** After fixing a bug, re-run `world` sweep, compare to `sweep_world2.json`.

**Output:** Diff between current and saved results.

**Time per run:** Same as the original sweep.

---

## 5. Running a Sweep

### 5.1 Step-by-step

```bash
# 1. From repo root, activate the virtual env
.\venv\Scripts\python.exe -m venv  # only first time

# 2. Run a single sweep group
.\venv\Scripts\python.exe simulation/test_reports/sweep_runner.py world > simulation/test_reports/sweep_world3.json 2> simulation/test_reports/sweep_world3.log

# 3. Verify the JSON is valid
.\venv\Scripts\python.exe -c "import json; d=json.load(open('simulation/test_reports/sweep_world3.json',encoding='utf-8-sig')); print(f'OK: {len(d)} params swept')"

# 4. Quick check: any values produce non-zero crimes?
.\venv\Scripts\python.exe -c "
import json
d = json.load(open('simulation/test_reports/sweep_world3.json', encoding='utf-8-sig'))
for p, results in d.items():
    for v, r in results.items():
        if r.get('crimes_total', 0) > 0:
            print(f'{p}={v}: crimes={r[\"crimes_total\"]}')
"
```

### 5.2 The default config

```python
DEFAULT_CONFIG = {
    "n_agents": 80,
    "ticks": 200,
    "seed": 42,
    "tax_rate": 0.15,
    "welfare_enabled": True,
    "welfare_amount": 8.0,
    "food_availability": 0.85,
    "water_availability": 0.90,
    "unemployment_rate": 0.10,
    "crime_rate": 0.05,
}
```

If you change `n_agents` or `ticks`, the simulation runs more slowly. `seed=42` is the canonical seed for determinism.

### 5.3 Running a custom sweep (not in SWEEP_GROUPS)

```python
# In a new file: simulation/test_reports/my_sweep.py
import sys
sys.path.insert(0, r"D:\.projects\Societas\Societas")
from simulation.test_reports.sweep_runner import run_sweep, DEFAULT_CONFIG

# Define a custom group
my_params = ["HAPPY_THRESHOLD", "SAD_THRESHOLD", "ANGRY_UNLUST_THRESHOLD"]
results = run_sweep(my_params, DEFAULT_CONFIG)

import json
with open("simulation/test_reports/my_sweep.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
```

### 5.4 Running a scenario (not a parameter sweep)

```python
# In a new file: simulation/test_reports/scenario_famine.py
import sys
sys.path.insert(0, r"D:\.projects\Societas\Societas")
from simulation.test_reports.sweep_runner import run_simulation, DEFAULT_CONFIG
import json

scenario_config = {**DEFAULT_CONFIG, "food_availability": 0.0, "water_availability": 0.0, "ticks": 500}
result = run_simulation("food_availability", 0.0, scenario_config)

with open("simulation/test_reports/scenario_famine.json", "w", encoding="utf-8") as f:
    json.dump({"famine_scenario": result}, f, indent=2, default=str)

print(json.dumps(result, indent=2, default=str))
```

### 5.5 Time budget

| Sweep size | Estimated time |
|---|---|
| 1 parameter × 5 values (default 200 ticks, 80 agents) | 30-60 seconds |
| 1 sweep group (~6 params × 5 values) | 5-10 minutes |
| All 9 groups (~50 params × 5 values) | 30-60 minutes |
| Full coverage (165 params × 7 values) | 4-8 hours |
| Scenario (1000-tick run) | 30-60 seconds |

Run sweeps overnight or in parallel via subagents. Use a larger machine if available.

### 5.6 Output encoding gotcha

On Windows PowerShell, `python -c "print(json.dumps(...))"` defaults to UTF-16 which corrupts the JSON. Always use:
- `sweep_runner.py` writes via `sys.stdout.buffer.write(...)` to avoid this — OK
- When reading JSON in PowerShell, use `encoding='utf-8-sig'` to handle BOMs

---

## 6. Output Format

### 6.1 JSON schema

```json
{
    "PARAM_NAME": {
        "value_as_string": {
            "param": "PARAM_NAME",
            "value": <value>,
            "avg_happiness": 0.685,
            "avg_unlust": 0.215,
            "final_dead": 0,
            "crimes_total": 0,
            "protests_total": 0,
            "unique_actions": 7,
            "emotion_states": 2,
            "wealth_classes": 2,
            "final_unemployment": 0.0125,
            "wealth_gini": 0.577,
            "happiness_variance": 0.002,
            "action_counts": {"work": 9713, "rest": 2595, "befriend": 1301, ...},
            "final_alive": 80,
            "final_wealth": {"poor": 0, "middle": 58, "rich": 22},
            "final_emotions": {"happy": 67, "normal": 13}
        },
        "another_value": { ... }
    },
    "ANOTHER_PARAM": { ... }
}
```

### 6.2 File naming conventions

| Pattern | Use case |
|---|---|
| `sweep_<group>.json` | A complete `SWEEP_GROUPS` group (e.g., `sweep_world.json`) |
| `sweep_<group>v2.json` | Re-run of the same group with a different runner version |
| `round<N>_<topic>.json` | Sweep during a multi-round campaign (e.g., `round3_edge_cases.json`) |
| `scenario_<name>.json` | Single curated scenario (e.g., `scenario_famine.json`) |
| `regression_<date>.json` | Regression check after a code change |

### 6.3 File location

All sweep outputs go to `simulation/test_reports/`. Do not commit large sweep files to git (add to `.gitignore` if they're >1MB). Keep them locally for analysis.

---

## 7. Analysis Methodology

### 7.1 Reading the JSON

Always load with `encoding='utf-8-sig'` to handle Windows BOMs:

```python
import json
with open("simulation/test_reports/sweep_world.json", encoding="utf-8-sig") as f:
    data = json.load(f)
```

### 7.2 Computing "spread" (the most useful single number)

For each metric, compute `max_value - min_value` across all swept values. This tells you how much variation the parameter produces.

```python
spreads = {}
for param, results in data.items():
    for metric in ["avg_happiness", "avg_unlust", "final_dead", "crimes_total", "wealth_gini"]:
        values = [r.get(metric, 0) for r in results.values()]
        if values:
            spreads[(param, metric)] = max(values) - min(values)

# Sort by largest spread to find impactful params
for (p, m), s in sorted(spreads.items(), key=lambda x: -x[1])[:10]:
    print(f"{p} → {m}: spread = {s:.4f}")
```

### 7.3 Categorizing results

Every parameter sweep result falls into one of 5 categories:

| Category | Definition | Example |
|---|---|---|
| **WORKING** | At least one metric has spread > 0.001 AND behavior is sensible | `FOOD_DECAY_RATE`: happiness varies 0.734→0.685, deaths 0→80 |
| **PARTIAL** | Some metrics vary, others don't; effect is weak | `BASE_FOOD_COST`: gini varies 0.572→0.622, but happiness is flat |
| **DEAD** | All metrics have spread < 0.0001; identical output across all values | `water_availability`: all 11 values produce bit-identical results |
| **INVERTED** | The parameter has the opposite effect of what its name suggests | `tax_rate`: increases inequality instead of reducing it |
| **BROKEN** | Sweep throws exceptions, produces NaN, or simulation crashes | (rare; usually caught by initial validation) |

### 7.4 Spotting the unexpected

The most important findings are the **anomalies** — places where a parameter does something surprising:

1. **Non-monotonic relationships** — a parameter increases and then decreases the metric (e.g., `food_availability=0.2` kills 11 agents but `0.3` kills only 2)
2. **Threshold cliffs** — the metric is flat until a specific value, then changes sharply (e.g., `FOOD_DEATH_THRESHOLD=0.05` → 17 dead, but 0.02 → 0 dead)
3. **Saturated responses** — the metric plateaus quickly and stops responding (e.g., `SEEK_JOB_BASE_CHANCE=0.16` already gets 0% unemployment)
4. **Coupled effects** — changing one parameter affects something you didn't expect (e.g., `JOB_LOSS_RATE` doesn't just change unemployment, it also drops happiness)
5. **Bugs** — the output is clearly wrong (gini=0 when all die is correct; gini=0 when half are rich and half poor is wrong)

### 7.5 Statistical sanity checks

For any parameter sweep:

```python
# 1. Check for NaN or infinity
import math
for r in results.values():
    for k, v in r.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            print(f"  NaN/Inf in {k}: {v}")

# 2. Check final_alive is consistent
for v, r in results.items():
    expected = DEFAULT_CONFIG["n_agents"] - r["final_dead"]
    if r["final_alive"] != expected:
        print(f"  Inconsistency at {v}: alive={r['final_alive']} but expected={expected}")

# 3. Check wealth_class sum equals final_alive
for v, r in results.items():
    wealth_sum = sum(r.get("final_wealth", {}).values())
    if wealth_sum != r["final_alive"]:
        print(f"  Wealth sum mismatch at {v}: sum={wealth_sum} alive={r['final_alive']}")
```

---

## 8. Report Format

Every sweep produces a report. The report is the artifact you ship, not the JSON.

### 8.1 Standard report structure

```markdown
# Sweep Report: <group name>

**Date:** YYYY-MM-DD
**Config:** n_agents=X, ticks=Y, seed=Z, ...
**Sweep runner:** simulation/test_reports/sweep_runner.py

## 1. Executive Summary
[1 paragraph: how many params, how many WORKING/DEAD/PARTIAL/INVERTED]

## 2. Per-Parameter Results
### 2.1 <PARAM_NAME> (range MIN-MAX, default X)
| Value | <metric1> | <metric2> | <metric3> |
|---|---|---|---|
| value1 | x | y | z |
| value2 | x | y | z |

**Effect:** [1-2 sentences: does it work? in what direction?]
**Direction:** [increase/decrease/u-shaped/cliff]
**Absurd behavior:** [any non-monotonic or surprising patterns]
**Verdict:** WORKING / DEAD / PARTIAL / INVERTED

## 3. Bugs Found
[Each bug: title, file:line, root cause, suggested fix, severity]

## 4. Recommended Defaults
| Parameter | Current | Proposed | Reason |
|---|---|---|---|

## 5. Edge Cases
[Any boundary behaviors observed]
```

### 8.2 Length guidance

| Report type | Target length |
|---|---|
| Single parameter | 50-100 lines |
| Single group (5-8 params) | 200-400 lines |
| Multi-group campaign round | 500-1000 lines |
| Final synthesis | 1000-3000 lines |

### 8.3 Naming

Save reports to `simulation/test_reports/<descriptive_name>_report.md`. Examples:
- `sweep_world_report.md`
- `sweep_emotion_economy_report.md`
- `round3_edge_cases_report.md`
- `cross_analysis.md`
- `FINAL_REPORT.md`

---

## 9. Delegation to Subagents

Subagents are the right tool for parallel sweeping. They have high throughput, follow instructions precisely, and can code well given a sharp prompt. Their weakness is **shallow reasoning** — they will report the obvious and miss the subtle. Your job as orchestrator is to (a) give them precise prompts, (b) read their reports critically, (c) look between the lines for what they missed.

### 9.1 When to delegate

| Task | Delegate? |
|---|---|
| Running a known sweep group with known param values | **Yes** — pure execution |
| Re-running a sweep with a code change | **Yes** — regression check |
| Running 10+ edge case scenarios in parallel | **Yes** — through put is the win |
| Analyzing results, finding correlations | **Partial** — subagent does the table; you do the insight |
| Deciding what to sweep | **No** — orchestrator decision |
| Setting the golden spot targets | **No** — orchestrator decision |
| Synthesizing across reports | **No** — orchestrator job |

### 9.2 Subagent prompt template

```
You are running parameter sweeps for the SOCIETAS simulation engine.

Working directory: D:\.projects\Societas\Societas

The sweep runner is at simulation/test_reports/sweep_runner.py.
Public API:
  run_simulation(param_name, param_value, config) → metrics dict
  run_sweep(param_names, config) → {param: {value: metrics}}
  DEFAULT_CONFIG, PARAMETER_OVERRIDES, SWEEP_GROUPS defined in that file.

Your task: <SPECIFIC TASK>

Output requirements:
1. Save JSON to: simulation/test_reports/<filename>.json
2. Save a report to: simulation/test_reports/<filename>_report.md
3. The report must include per-parameter tables showing each value's effect on key metrics
4. Categorize each param: WORKING / DEAD / PARTIAL / INVERTED
5. For each DEAD param, give a 1-paragraph root cause analysis (where in the code?)
6. For each INVERTED param, explain what direction the effect runs and why

Quality bar:
- Be specific. Numbers in tables, not handwaving.
- If a metric is unchanged across all values, say so explicitly.
- If you find something surprising (non-monotonic, cliff, saturation), call it out.
- Don't write more than 200 lines unless the data demands it.
- Do NOT include code, just the report.

Verification before reporting done:
- JSON file exists and is valid (loads with json.load)
- Report file exists and has at least one WORKING/DEAD/PARTIAL/INVERTED verdict
- For each DEAD param, you've actually opened the source file and identified the line
```

### 9.3 Common subagent failure modes

| Failure | Why it happens | How to catch it |
|---|---|---|
| "All parameters WORKING" with no analysis | Subagent didn't actually examine the JSON | Check the JSON directly |
| "DEAD" without root cause | Subagent didn't look at source code | Re-dispatch with explicit instruction to grep the codebase |
| Wrong metrics in the table | Subagent confused the JSON schema | Verify the JSON shape yourself |
| Report is just a wall of tables | Subagent skipped the analysis section | Require a 1-paragraph verdict per parameter |
| False confidence — "the simulation is fine" | Subagent didn't run edge cases | Always dispatch edge cases explicitly |
| Skipped the bug hunt | Subagent treated it as data-only | Explicitly request bug findings |

### 9.4 Reading subagent reports critically

Subagents are good at execution but shallow at reasoning. After a subagent reports, look for:

1. **Surprises they missed** — when did a metric change in a way they didn't flag?
2. **Coupled effects** — did a parameter change more than the one metric they were watching?
3. **Inconsistencies** — does the action_counts add up? Does final_wealth sum to final_alive?
4. **The "obvious" bug** — is there a clear mismatch between param name and effect?
5. **The "this should be dead" red flag** — if a parameter has the same name as a system (e.g., `crime_rate` affects the metric `crime_rate`), it BETTER show variation. If it doesn't, the system is broken.

---

## 10. Worked Examples

### 10.1 Example: Diagnosing why `water_availability` is DEAD

**Step 1:** Sweep `water_availability` from 0.0 to 1.0.

```python
# Quick check
results = run_sweep(["water_availability"], DEFAULT_CONFIG)
for v, r in results["water_availability"].items():
    print(f"  {v}: happy={r['avg_happiness']:.4f} unlust={r['avg_unlust']:.4f} dead={r['final_dead']}")
```

**Output:**
```
  0.0: happy=0.6846 unlust=0.2151 dead=0
  0.2: happy=0.6846 unlust=0.2151 dead=0
  0.5: happy=0.6846 unlust=0.2151 dead=0
  0.8: happy=0.6846 unlust=0.2151 dead=0
  1.0: happy=0.6846 unlust=0.2151 dead=0
```

**All values produce bit-identical output → DEAD parameter.**

**Step 2:** Find where `water_availability` is used in code.

```bash
grep -rn "water_availability" simulation/ shared/
```

**Output:**
```
shared/schemas/simulation_state.py:61: water_availability: float = WATER_AVAILABILITY_DEFAULT
shared/schemas/simulation_state.py:  (default value)
simulation/agents/needs_calculator.py:  uses SCARCITY_BASE - world.food_availability  ← BUG!
simulation/world/metrics_calculator.py:  uses world.water_availability only in compute_state_hash
```

**Step 3:** Open `needs_calculator.py` and find the bug.

```python
# In needs_calculator.py, decay_needs():
scarcity = SCARCITY_BASE - world.food_availability  # BUG: only uses food_availability!
food_decay = FOOD_DECAY_RATE * scarcity
water_decay = WATER_DECAY_RATE * scarcity  # Same scarcity as food — water ignored!
```

**Root cause:** `decay_needs()` uses `food_availability` for both food AND water scarcity. `water_availability` is never read by any simulation logic. It only appears in `compute_state_hash()` for the hash string.

**Step 4:** Write the fix.

```python
# In needs_calculator.py, decay_needs():
food_scarcity = SCARCITY_BASE - world.food_availability
water_scarcity = SCARCITY_BASE - world.water_availability  # FIX: use water_availability
food_decay = FOOD_DECAY_RATE * food_scarcity
water_decay = WATER_DECAY_RATE * water_scarcity
```

**Step 5:** Add regression test.

```python
# In tests/unit/simulation/test_needs_calculator.py
def test_water_availability_affects_water_decay():
    world_food_only = SimulationState(food_availability=0.5, water_availability=0.9, ...)
    world_water_only = SimulationState(food_availability=0.9, water_availability=0.5, ...)
    agent = make_test_agent()
    initial_water = agent.needs.get_level(NeedType.WATER)
    decay_needs(agent, world_food_only, rng)
    food_water = agent.needs.get_level(NeedType.WATER)
    # ... reset agent ...
    decay_needs(agent, world_water_only, rng)
    scarcity_water = agent.needs.get_level(NeedType.WATER)
    assert food_water > scarcity_water  # Food-scarcity world leaves more water
```

**Step 6:** Re-run the sweep to verify the fix.

```python
results = run_sweep(["water_availability"], DEFAULT_CONFIG)
# Expected: water=0.0 → water need drops → unlust rises → eventually deaths
```

### 10.2 Example: Finding the protest activation cliff

**Question:** "At what value of `ANGRY_UNLUST_THRESHOLD` do protests start firing?"

**Step 1:** Sweep `ANGRY_UNLUST_THRESHOLD` from 0.3 to 0.85.

**Step 2:** Plot `protests_total` vs value.

| Value | Protests | Unique actions |
|---|---|---|
| 0.3 | 378 | 8 |
| 0.4 | 12 | 7 |
| 0.5 | 0 | 7 |
| 0.58 (default) | 0 | 7 |
| 0.85 | 0 | 7 |

**Step 3:** Identify the cliff: at 0.4-0.5, protests drop from 12 to 0. This is the activation threshold.

**Step 4:** Examine the code to confirm.

```python
# In action_executor.py, action weights for PROTEST:
protest_weight = 0
if unlust > 0.45 and not morality_active(unlust, morality):
    protest_weight = 15
if agent.emotions.primary == EmotionType.ANGRY:
    protest_weight += 20
```

Wait, the activation requires unlust > 0.45, not unlust > ANGRY_UNLUST_THRESHOLD. So the parameter itself doesn't directly gate protests. The ANGRY_UNLUST_THRESHOLD gates when an agent BECOMES ANGRY, and ANGRY agents protest more. So the cliff is at the unlust level where the proportion of ANGRY agents shifts.

**Step 5:** Report finding: "The protest activation cliff is at unlust 0.4-0.5. With default unlust=0.22, no agents become ANGRY (threshold=0.58), so no protests. To activate protests, lower ANGRY_UNLUST_THRESHOLD to 0.40 or stress the simulation with low food."

### 10.3 Example: Golden spot search

**Goal:** Find a config where all 15 action types, all 5 emotions, all 4 death types, and all 3 wealth classes are possible.

**Step 1:** Establish baseline. Default config produces only 7/15 actions, 2/5 emotions, 1/4 death types, 2/3 wealth classes.

**Step 2:** Identify which defaults block which criteria:
- ANGRY_UNLUST_THRESHOLD=0.58 blocks ANGRY emotion and PROTEST/HARM_OTHER/COMPLAIN
- UNLUST_MORALITY_GATE=0.58 blocks STEAL/HARM_OTHER
- DESPAIR_UNLUST_THRESHOLD=0.82 blocks DESPAIR emotion and despair death
- food_availability=0.85 prevents food death
- water_availability bug prevents water death
- health death path not triggered in default
- wealth distribution defaults to middle+rich only (no poor)

**Step 3:** Tweak defaults:
- ANGRY_UNLUST_THRESHOLD: 0.58 → 0.45
- UNLUST_MORALITY_GATE: 0.58 → 0.40
- DESPAIR_UNLUST_THRESHOLD: 0.82 → 0.65
- (with BUG-1 fixed, water stress is now real)

**Step 4:** Run scenario: "perfect default" with new defaults for 200 ticks.

**Step 5:** Measure: 12/15 actions, 4/5 emotions, 2/4 death types, 3/3 wealth classes. Still missing water death, health death, COMPLY.

**Step 6:** Add a stress scenario: 50% of agents get sick (health decay 10x). Now health death triggers.

**Step 7:** Document: "The golden spot is achieved with new defaults. Some criteria (water death, COMPLY) require explicit scenarios, not just default config."

---

## 11. Pitfalls & Best Practices

### 11.1 The cardinal sins

1. **Not patching the consuming module** — `from shared.constants.defaults import X` creates a local binding. If you change `defaults.py` after import, the consumer still uses the old value. **Always update `_PATCH_MODULES` when adding new param usage.**

2. **Sweeping too narrow a range** — if you only sweep `FOOD_DEATH_THRESHOLD` from 0.01 to 0.05, you miss the death cliff at 0.05-0.1. **Sweep at least one decade above and below the default.**

3. **Ignoring the "comfortable equilibrium"** — many parameters appear DEAD in default config because the default never enters the state where the parameter matters. **Sweep with stress conditions to verify.**

4. **Confusing "constant at import time" with "config at runtime"** — the sweep runner patches constants, not the SimulationState. If a constant is read from a SimulationState field, that's a different kind of param.

5. **Committing sweep JSON files to git** — they can be huge. Add to `.gitignore` or store separately.

### 11.2 The cardinal virtues

1. **Always verify determinism** — run the same sweep twice, diff the JSON. If they differ, your patch is leaking.

2. **Always include extreme values** — sweep 0.0, 1.0, very high, very low. Most interesting behavior is at the boundaries.

3. **Always cross-check action_counts** — the sum should approximately equal `n_agents × ticks` (some agents die, so it's a lower bound).

4. **Always compute the spread table** — it shows you the impactful parameters at a glance.

5. **Always read the source code** — when a parameter is DEAD, grep for it. The reason is almost always in the code.

6. **Always document the bug, not just the symptom** — "water_availability is DEAD" is shallow. "water_availability is DEAD because `decay_needs()` uses `food_availability` for both food and water scarcity — see needs_calculator.py:61" is actionable.

7. **Always keep the patch table up to date** — when you add a new `from defaults import X`, add `X: [your.module.path]` to `_PATCH_MODULES`.

### 11.3 When to NOT sweep

- **Single-run experiments** — if you only need to try one configuration, just run the simulation. Sweeping is for systematic exploration.
- **AI subsystem testing** — that's a different layer.
- **Performance testing** — use `pytest-benchmark`.
- **API testing** — backend has its own tests.

### 11.4 When to escalate

- **The simulation crashes** — there's a real bug. File an issue and stop the sweep.
- **The patch table can't be made to work** — there's a deeper architecture issue. Escalate to the Technical Lead.
- **Sweep results are inconsistent across runs** — determinism is broken. This is critical. Stop and fix.
- **A parameter name doesn't match what it actually does** — there's a naming/semantic bug. Document and fix forward.

### 11.5 Token efficiency

When delegating to subagents, ask them to:
- Output to files, not chat
- Use tables, not paragraphs
- Cap reports at 200-400 lines unless the data demands more
- Save JSON with `indent=2` for human readability
- Use `encoding='utf-8-sig'` when reading

When writing your own analysis:
- Don't paste full JSON in chat
- Don't repeat the subagent's findings verbatim
- Synthesize across reports, don't summarize one
- End with a 1-paragraph verdict and a clear next action

---

## 12. Glossary

| Term | Definition |
|---|---|
| **Sweep** | A systematic test that varies one parameter and measures the effect |
| **Sweep group** | A predefined set of related parameters (e.g., "world" = food/water/crime/unemp/tax/welfare) |
| **Default config** | The baseline simulation settings (80 agents, 200 ticks, seed=42, food=0.85, etc.) |
| **Patch table** | `_PATCH_MODULES` — maps each constant to the modules that import it |
| **Constant at import time** | The Python behavior where `from module import X` binds X in the importing module's namespace at import time |
| **Comfortable equilibrium** | The default config's attractor: happiness≈0.69, unlust≈0.22, 0 deaths, 0 crimes, all middle+rich |
| **DEAD parameter** | A parameter that produces identical output across all swept values |
| **PARTIAL parameter** | A parameter that affects some metrics but not others |
| **WORKING parameter** | A parameter that meaningfully affects outcomes in a sensible direction |
| **INVERTED parameter** | A parameter that has the opposite effect of what its name suggests |
| **Spread** | `max_value - min_value` of a metric across all swept values; higher = more impactful |
| **Cliff** | A threshold value where the metric changes abruptly |
| **Saturation** | A parameter value beyond which further changes have no effect |
| **Non-monotonic** | A parameter-metric relationship that is not strictly increasing or decreasing |
| **Stress scenario** | A configuration designed to push the simulation into a state (e.g., low food, high unlust) |
| **Edge case** | A boundary value (0, 1, very high, very low) that often reveals bugs |
| **Golden spot** | A configuration where all simulation systems can be activated and produce diverse outcomes |
| **Regression sweep** | Re-running a known sweep to verify a code change didn't break anything |
| **Determinism** | Same seed + same config = identical output (bit-for-bit) |
| **Hysteresis** | The emotion machine's "stays in state until timer expires" rule that creates persistence |

---

## Appendix A: The Complete Sweep Catalog (as of this writing)

### Already swept (2024-2025)

| Group | Params | Status |
|---|---|---|
| world | food_availability, water_availability, crime_rate, unemployment_rate, tax_rate, welfare_amount | 2 WORKING, 2 DEAD, 1 INVERTED, 1 PARTIAL |
| unlust | UNLUST_FOOD/WATER/SAFETY/SOCIAL/FINANCIAL_WEIGHT, UNLUST_NEED_THRESHOLD, UNLUST_MORALITY_GATE | 3 WORKING, 2 PARTIAL, 1 DEAD, 1 STRONG |
| needs | FOOD_DECAY_RATE, SOCIAL_DECAY_RATE, SLEEP_DECAY_RATE, SELF_ESTEEM_DECAY_RATE, SCARCITY_BASE | 3 WORKING, 1 DEAD, 1 PARTIAL |
| emotion | HAPPY/SAD_THRESHOLD, ANGRY/DESPAIR_UNLUST_THRESHOLD, ANGRY_TENDENCY_THRESHOLD, SAD/ANGRY/DESPAIR_TIMER | 2 WORKING, 6 DEAD |
| economy | SALARY_MULTIPLIER_POOR/RICH, FOOD_COST_MULTIPLIER_POOR/RICH, BASE_FOOD_COST, HAPPINESS_EMPLOYED_BONUS | 1 WORKING, 3 DEAD, 2 PARTIAL |
| death | DESPAIR_MORTALITY_RATE, FOOD_DEATH_THRESHOLD, JOB_LOSS_RATE | 2 WORKING, 1 DEAD |
| actions | SEEK_JOB_BASE_CHANCE, BEG_MAX_AMOUNT, STEAL_*, SHARE_PERCENTAGE, REPUTATION_DECAY_RATE | 2 WORKING, 4 DEAD |
| adler_grid | ADLER_GAP_THRESHOLD, INTERACTION_RADIUS, GRID_SIZE | 1 WORKING, 1 DEAD, 1 PARTIAL |
| scale | n_agents, ticks | 2 WORKING |

### Not yet swept (the next frontier)

| Parameter | Category | Notes |
|---|---|---|
| All 10 HAPPINESS_*_WEIGHT | emotion | Never tested — likely affects default outcomes subtly |
| All 5 ADLER_*_PER_GAP | adler | Likely DEAD in default; need stress scenario |
| SLEEP_REPLENISH_RATE, SLEEP_RESET_THRESHOLD, SLEEP_HALF_TIMER_THRESHOLD | needs | Sleep subsystem not yet validated |
| WATER_DECAY_RATE, SEXUAL_TENSION_GROWTH_RATE, SAFETY_DECAY_RATE, FAMILY_DECAY_RATE, ROMANTIC_DECAY_RATE | needs | 5 decay rates never tested |
| WATER_DEATH_THRESHOLD, HEALTH_DEATH_THRESHOLD | death | Death path never tested |
| SALARY_MULTIPLIER_MIDDLE, FOOD_COST_MULTIPLIER_MIDDLE | economy | Middle class untested |
| DECISION_STAGGER_INTERVAL, MORAL_DILEMMA_*_THRESHOLD | decision | LLM-related, may not matter in deterministic sweep |
| REPUTATION_CHANGE_GOOD, REPUTATION_CHANGE_CRIMINAL, REPUTATION_CHANGE_KILL | actions | Crime reputation never tested |
| UNLUST_FINANCIAL_DIVISOR | unlust | Financial unlust formula parameter |
| DEFAULT_AMBIGUITY_THRESHOLD, DEFAULT_DETERMINISTIC_WEIGHT, DEFAULT_GEMMA_WEIGHT | fusion | Backend fusion layer (out of scope for sim sweep) |

### Edge cases never tested

- 1 agent, 200 ticks
- 1 agent, 2000 ticks
- 1000 agents, 50 ticks
- 1000 agents, 1000 ticks
- 0 food × 0 water × 0 welfare (total collapse)
- 1.0 food × 1.0 water × 100 welfare (perfect world)
- Repeated runs with different seeds (variance check)

### Tweakable scenarios never tested

- Mid-sim policy change (e.g., "introduce tax at tick 100")
- Population shock (e.g., "kill 50% of agents at tick 50")
- Wealth shock (e.g., "redistribute all wealth at tick 100")
- Pandemic (e.g., "health decay 10x for 50 ticks")

---

## Appendix B: Quick reference for the impatient

```bash
# Run all 9 sweep groups
for g in world unlust needs emotion economy death actions adler_grid scale; do
    .\venv\Scripts\python.exe simulation/test_reports/sweep_runner.py $g > simulation/test_reports/sweep_${g}_v3.json 2> simulation/test_reports/sweep_${g}_v3.log
done

# Verify all JSONs are valid
.\venv\Scripts\python.exe -c "
import json, os
for f in os.listdir('simulation/test_reports'):
    if f.startswith('sweep_') and f.endswith('.json'):
        try:
            d = json.load(open(f'simulation/test_reports/{f}', encoding='utf-8-sig'))
            print(f'{f}: OK ({len(d)} params)')
        except Exception as e:
            print(f'{f}: BROKEN ({e})')
"

# Quick check: find DEAD params across all sweeps
.\venv\Scripts\python.exe -c "
import json, os
for f in os.listdir('simulation/test_reports'):
    if f.startswith('sweep_') and f.endswith('.json'):
        d = json.load(open(f'simulation/test_reports/{f}', encoding='utf-8-sig'))
        for p, results in d.items():
            metrics = ['avg_happiness', 'avg_unlust', 'final_dead', 'crimes_total']
            spread = 0
            for m in metrics:
                vals = [r.get(m, 0) for r in results.values() if isinstance(r, dict)]
                if vals:
                    spread = max(spread, max(vals) - min(vals))
            if spread < 0.001:
                print(f'  {f}: {p} is DEAD (max spread = {spread})')
"
```

---

*End of Sweeping Guide. Last updated with simulation/test_reports/sweep_runner.py revision supporting 99+ parameters across 9 groups and 2 scale axes.*
