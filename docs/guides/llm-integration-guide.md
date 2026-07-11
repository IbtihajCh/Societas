# LLM Integration & Events Guide for the AI Engineer

> **Audience:** The AI Systems Engineer responsible for prompt engineering, model
> selection, and the LLM boundary of the hybrid decision system.
>
> **Purpose:** A single self-contained reference that lets you build, validate,
> and evolve every prompt template, plus wire environmental and social events
> into the decision pipeline so the LLM can actually see, react to, and reason
> about the dynamic world the deterministic engine runs.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Three-Model Routing Strategy](#2-three-model-routing-strategy)
3. [The Eight Prompt Templates](#3-the-eight-prompt-templates)
   - 3.1 `agent_decision.md` (E2B — per-agent per-tick)
   - 3.2 `moral_reasoning.md` (26B A4B — moral dilemmas)
   - 3.3 `tie-break.md` (31B — ambiguity resolution)
   - 3.4 `persona-generation.md` (31B — one-time at birth)
   - 3.5 `policy-translation.md` (31B — policy weight deltas)
   - 3.6 `narrative-generation.md` (31B — news articles)
   - 3.7 `governance-advisor.md` (31B — human operator)
   - 3.8 `system-prompts.md` (reusable components)
4. [Event Integration](#4-event-integration) **← the new piece**
   - 4.1 The event context envelope
   - 4.2 The event-aware decision flow
   - 4.3 Drought scenario template
   - 4.4 Riot scenario template
   - 4.5 New `event_response_prompt.md` (to author)
5. [Prompt Validation & Test Fixtures](#5-prompt-validation--test-fixtures)
6. [End-to-End Tick Worked Example](#6-end-to-end-tick-worked-example)
7. [Determinism Guarantees & Failure Modes](#7-determinism-guarantees--failure-modes)
8. [Glossary](#8-glossary)
9. [Appendices](#9-appendices)

---

## 1. Architecture Overview

SOCIETAS is a three-layer hybrid system. The **deterministic engine** owns
ground truth; the **LLM** is advisory. The LLM never executes a state change
directly — it returns a `Decision` JSON that the engine validates, scores, and
either accepts or overrides.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         SOCIETAS v2 Stack                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Frontend (Next.js 14) — visualization, control plane                 │
│           │                                                          │
│           ▼                                                          │
│  Backend (FastAPI) — HTTP API, WebSocket, persistence                │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Deterministic Engine (Layer 1)                              │    │
│  │  ─────────────────────────────────                           │    │
│  │  • 80 agents, 5,000-tick lifespan                            │    │
│  │  • 8 traits, 13 needs (5 Maslow layers), 5 emotions          │    │
│  │  • 25 actions, 8 death pathways, 3 wealth classes            │    │
│  │  • Tick loop: 12 deterministic steps                         │    │
│  │  • At action-selection step: optionally call LLM             │    │
│  │  • Validates LLM output, falls back to deterministic_fallback│    │
│  └──────────────────────────────────────────────────────────────┘    │
│           │                                                          │
│           ▼  (only when ambiguity > 0.05)                            │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  LLM Boundary — VLLMRouter                                   │    │
│  │  ─────────────────────────────────                           │    │
│  │  • 3 Gemma 4 models: E2B / 26B A4B / 31B                    │    │
│  │  • Routes by prompt type                                     │    │
│  │  • Returns Decision JSON; engine validates                   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│           │                                                          │
│           ▼                                                          │
│  vLLM cluster (3× MI300X, Gemma 4 quantized)                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Prompt fire-points in the tick loop

The simulation runs `simulation/engine/tick_loop.py:run_tick()` which calls
`simulation/agents/decision_engine.py` for each living agent. At Step 6
(action selection), the engine asks the LLM to choose an action. Different
prompts fire at different points:

| Tick phase | Prompt | Model | Volume |
|---|---|---|---|
| Tick start (rare) | `persona-generation.md` | 31B | 1 per new agent |
| Per-agent (every tick) | `agent_decision.md` | E2B | ~80/tick |
| Per-agent (moral dilemma) | `moral_reasoning.md` | 26B A4B | 0–5/tick |
| Per-agent (ambiguity > 0.05) | `tie-break.md` | 31B | 0–2/tick |
| Per-policy (rare) | `policy-translation.md` | 31B | 0–1/tick |
| Per-news-event | `narrative-generation.md` | 31B | 0–3/tick |
| On-demand (human) | `governance-advisor.md` | 31B | interactive |

### Determinism contract

| Layer | Deterministic? | How |
|---|---|---|
| Engine (Layer 1) | Yes | `DeterministicRNG` seeded from `seed` |
| E2B agent brain | Yes | `temperature=0.0` |
| 26B moral reasoning | Mostly | `temperature=0.2`; engine accepts variance |
| 31B governance/persona/tie-break | Mostly | `temperature=0.2–0.7`; engine validates |
| vLLM failure path | Yes | `MockAIRouter` (deterministic trait-aware fallback) |

**Rule:** the engine is the source of truth. If the LLM returns invalid JSON,
the wrong action name, or a low confidence, the engine falls back to
`deterministic_fallback` (a hand-coded action-selection function that uses
the agent's traits and world state to pick an action).

---

## 2. Three-Model Routing Strategy

The vLLM cluster runs three Gemma 4 models on different ports. The
`VLLMRouter` (in `simulation/engine/vllm_router.py`) routes prompts to the
right model.

| Model | Port | Default URL | Temperature | Use for | Why |
|---|---|---|---|---|---|
| **E2B** (efficient) | 8001 | `165.245.130.202:8001` | 0.0 | `agent_decision` | Fast (27ms median), called 80×/tick. Determinism critical. |
| **26B A4B** (MoE) | 8002 | `165.245.130.202:8002` | 0.2 | `moral_reasoning` | Reasoning depth for moral dilemmas. Mid-frequency. |
| **31B** (full) | 8000/8003 | `165.245.130.202:8000` | 0.2–0.7 | `tie-break`, `persona-gen`, `policy-translation`, `narrative-generation`, `governance-advisor` | Most capable. Low-frequency or interactive. |

**Fallback chain:** if the 26B A4B is unavailable, the router falls back to the
31B for moral reasoning. If E2B is unavailable, it falls back to 31B (slower)
and ultimately to `MockAIRouter` (deterministic). The engine always has a
working path.

**API keys** (per `vllm_router.py`):
```
societase2b-key3z8      → E2B (port 8001)
societasmoe-key7q1      → 26B A4B (port 8002)
societas31-key9x2       → 31B (port 8003/8000)
```

---

## 3. The Eight Prompt Templates

Each prompt lives in `prompts/<name>.md` and is versioned via YAML frontmatter.
The engine references it by name through `prompts/README.md` → `prompts/<name>.md`.

The frontmatter contract is **mandatory** for every prompt:

```yaml
---
type: prompt                    # always "prompt"
purpose: agent-decision         # unique key matching filename
model: google/gemma-4-e2b-it-qat
temperature: 0.0                # 0.0 for determinism, higher for creativity
max_tokens: 64                  # hard cap
version: 1.0.0                  # semver; breaking changes increment major
status: active                  # active | draft | deprecated
---
```

### 3.1 `agent_decision.md` (E2B — per-agent per-tick)

**Fires:** every tick for every living agent (≈ 80 calls/tick).
**Goal:** pick a single action from the 25-action enum based on the agent's
state and the current world state.

#### System prompt (exact text)

```
You are a person in a society simulation. Make one decision per tick.
Choose a single action that reflects your current needs, traits, and
situation. Your response is validated by the simulation engine — output
only the requested JSON.
```

#### Input schema (built by `decision_engine.build_agent_prompt`)

The engine builds a single-line, key=value text prompt (no JSON envelope on
input). Example for a 35-year-old DOCTOR with food=0.2, money=850, and a
drought event active:

```
You are a person in a society simulation. Your situation:
hunger=0.20 water=0.45 sleep=0.70 safety=0.60
social=0.55 esteem=0.50 money=850 employed=True job=DOCTOR
mood=normal happiness=0.62 unlust=0.18 health=0.92 reputation=0.55
morality=0.65 anger=0.30 ambition=0.55
extraversion=0.45 creativity=0.60 resilience=0.70
dominance=0.35 risk=0.40
trust_govt=0.55 crimes=0 good_acts=12
nearby=4 protesters_near=0 needy_near=1
tax_rate=0.15 welfare=True food_avail=0.40
water_avail=0.55 crime_rate=0.08 unemployment=0.04

⚠ ACTIVE EVENT: DROUGHT (severity=0.7, started=tick 145, ends=tick 175)
  Effect: water_availability reduced 0.90→0.27

What do you do? Choose ONE:
work, buy_food, rest, seek_job, beg, befriend, console, isolate,
share, steal, harm_other, protest, complain, comply, idle,
treat, counsel, fraud, campaign, spread_rumor, support_family,
invest, buy_property, hobby

Respond EXACTLY: {"action":"...","feeling":"...","reason":"one sentence"}
```

#### Output schema

```json
{"action":"buy_food","feeling":"anxious","reason":"Water is scarce and I'm low on supplies before the drought ends."}
```

`action` MUST be one of the 25 canonical names. `feeling` is a single word.
`reason` is one sentence (≤ 80 chars).

#### Constraints

- `temperature=0.0` — strict determinism
- `max_tokens=64` — short response only
- No chain-of-thought, no `<|think|>`
- If the engine sees a non-JSON response, it calls `parse_response` which
  strips the wrapper and tries again. If that fails, the engine uses
  `deterministic_fallback`.

#### Validation rules (in `decision_engine.parse_response`)

1. Must be valid JSON.
2. `action` must be in the 25-action enum.
3. `feeling` is optional (default `"neutral"`).
4. `reason` is optional (default `""`).
5. If `action == "harm_other"` and the agent's morality is > 0.7, the engine
   *rejects* the action and falls back (safety override).
6. If `action == "steal"` and the agent has money > 200, the engine *downgrades*
   to `"share"` (because there's no economic pressure).

#### Common failure modes

| Failure | Engine response |
|---|---|
| Invalid JSON | Retry once with stricter prompt; if still fails → `deterministic_fallback` |
| Unknown action name | Reject, log, use `deterministic_fallback` |
| Harm with high morality | Override to `"comply"` |
| Steal with money > 200 | Downgrade to `"share"` |
| Timeout (> 3s) | Use `MockAIRouter` fallback |
| Server error 5xx | Use `MockAIRouter` fallback |

---

### 3.2 `moral_reasoning.md` (26B A4B — moral dilemmas)

**Fires:** only when `decision_engine.is_moral_dilemma()` returns True. A
moral dilemma is detected when an agent faces a genuine ethical conflict
that benefits from chain-of-thought reasoning — currently:
- `unlust > UNLUST_MORALITY_GATE (0.38)` AND `morality > 0.6` AND an
  `ActionType.HARM_OTHER` is in the top-3 options
- The agent is `ANGRY` emotion AND unlust > 0.45 AND a crime-related action
  is in the top-3

#### System prompt (exact text)

```
You are a person facing a moral dilemma in a society simulation. Use
the <|think|> token for chain-of-thought reasoning before your final
JSON answer. Consider the agent's personality, moral values, and social
context. The simulation engine retains final decision authority — your
output is advisory.
```

#### Input schema (built by `decision_engine.build_moral_dilemma_prompt`)

A richer, narrative-style prompt with `<|think|>` block:

```
<|think|>
You are a person facing a moral dilemma in a society simulation.

Your situation:
- Hunger: 0.20 (0=starving, 1=full)
- Money: £45
- Morality: 0.80 (0=selfish, 1=saintly)
- Unlust: 0.42 (0=content, 1=desperate)
- Emotion: angry
- Anger tendency: 0.65
- Resilience: 0.40
- Social connections: 3 people
- Trust in government: 0.30
- Nearby people: 6, protesters: 2
- World: tax=15%, food_avail=40%, welfare=on

⚠ ACTIVE EVENT: DROUGHT (severity=0.7)
  Effect: water_availability reduced 0.90→0.27

Think carefully about what this person would actually do, given their
personality and situation. Consider their moral values, their desperation,
their relationships, and the social context. What is the RIGHT choice
for THIS person?

Choose ONE action: work, buy_food, rest, seek_job, beg, befriend,
console, isolate, share, steal, harm_other, fraud, treat, protest,
counsel, complain, campaign, comply, spread_rumor, support_family,
invest, buy_property, hobby, idle

Respond EXACTLY: {"action":"...","feeling":"...","reason":"2-3 sentences explaining the moral reasoning"}
<|eot_id|>
```

#### Output schema

The model returns a `<|think|>...<|eot_id|>` block followed by JSON:

```json
{"action":"beg","feeling":"guilty","reason":"My morality is high but I'm desperate. Stealing would betray my values; begging preserves my dignity while addressing survival."}
```

#### Constraints

- `temperature=0.2` — some variety, but maintain coherence
- `max_tokens=256` — thinking + JSON
- Always use `<|think|>` for chain-of-thought
- The engine strips the `<|think|>` block and uses only the JSON
- Validates the same way as `agent_decision`

#### Why this exists

Without moral reasoning, the E2B model would default to either "steal"
(easy answer to hunger) or "do nothing" (preserves morality but dies).
The 26B A4B model weighs both factors and finds a third option — often
"beg", "share", or "seek help" — that the E2B wouldn't consider.

---

### 3.3 `tie-break.md` (31B — ambiguity resolution)

**Fires:** when `AgentDecisionScores.is_ambiguous(threshold=0.05)` returns
True. The top-2 action scores are within 0.05 of each other. Used 0–2 times
per tick.

#### System prompt (exact text)

```
You are the final arbiter in a governance simulation. Two or more
action options have been scored as equally viable by the deterministic
engine. Analyze the context and break the tie. Output only valid JSON.
The simulation engine retains final execution authority — your output
is a decision weight, not an order.
```

#### Input schema

```json
{
  "id": "decision-12345",
  "state": "agent-007, hungry, employed, ANGRY, drought active",
  "unlust": 0.42,
  "morality": 0.65,
  "options": [
    {
      "label": "buy_food",
      "action": "BUY_FOOD",
      "utility_scores": {
        "economic": 0.52,
        "social": 0.48,
        "environmental": 0.51
      }
    },
    {
      "label": "steal",
      "action": "STEAL",
      "utility_scores": {
        "economic": 0.55,
        "social": 0.30,
        "environmental": 0.49
      }
    }
  ]
}
```

#### Output schema

```json
{
  "action": "buy_food",
  "confidence": 0.72,
  "reason": "Agent's morality=0.65 and reputation dependency makes stealing high-risk; buying preserves long-term standing."
}
```

#### Constraints

- Must output valid JSON only — no additional text
- `confidence < 0.5` is treated as a system alert (decision still accepted
  but logged for review)
- `reason` must reference specific simulation metrics (state, unlust,
  morality), not abstract principles

#### Determinism guarantee

- `temperature=0.2` ensures near-deterministic output for identical inputs
- If confidence is low, the simulation logs the event for manual review
  but does not halt
- The RuleEngine retains ownership of the final execution — Gemma
  contributes the decision weight, the engine applies it

---

### 3.4 `persona-generation.md` (31B — one-time at birth)

**Fires:** once per agent at simulation start, when `create_initial_population`
is called. Generates a 1-2 sentence persona paragraph from 8 input traits.

#### System prompt (exact text)

```
You are a persona writer for a society simulation. Given 8 input
traits on a 0–1 scale, generate a single coherent persona paragraph
that names the character, describes their archetype, core motivation,
and a behavioral hook. Never exceed 2 sentences. Never use numeric
values. Never reference the trait vector directly.
```

#### Input schema

```json
{
  "traits": {
    "assertiveness": 0.9,
    "cooperation": 0.2,
    "risk_tolerance": 0.8,
    "altruism": 0.1,
    "traditionalism": 0.3,
    "materialism": 0.7,
    "idealism": 0.2,
    "ambition": 0.9
  }
}
```

#### Output schema

```json
{
  "name": "Marcus",
  "archetype": "mercantile magnate",
  "persona": "A man in early adulthood, working as a construction worker with limited financial means, driven by an unyielding ambition to build wealth."
}
```

> **⚠ Note:** The current `persona-generation.md` references OCEAN traits
> (openness, conscientiousness, extraversion, agreeableness, neuroticism,
> morality, risk_tolerance, patience) but the v2 engine uses 8 **SOCIETAS**
> traits (assertiveness, cooperation, risk_tolerance, altruism,
> traditionalism, materialism, idealism, ambition). **The prompt needs
> to be updated to match.**

#### Constraints

- `temperature=0.7` — creative but coherent
- `max_tokens=128`
- 1-2 sentences, never 3+
- No numerics, no trait vector reference
- Must include: name, archetype label, core motivation, behavioral hook

#### Validation

The engine stores the result in `agent.persona: str`. The persona is read
back by narrative prompts and tie-break prompts. If the LLM returns
invalid JSON, the engine falls back to a deterministic persona template:

```python
f"A {age_bracket} person, working as a {job_type}, with {wealth_class} means, "
f"preferring {routine_preference} and exhibiting a {mindset} mindset."
```

---

### 3.5 `policy-translation.md` (31B — policy weight deltas)

**Fires:** when an agent or human operator enacts a new policy. Translates
the policy intent into numeric utility weights the RuleEngine uses to
score future actions.

#### System prompt (exact text)

```
You translate policy intent into executable utility weights for a
society simulation. Given a policy description, persona, and current
world state, return 6 weights in [-1.0, +1.0] that represent how much
this policy should shift decision-making across 6 dimensions. The
simulation engine applies these as deltas to the deterministic
baseline. Output only valid JSON.
```

#### Input schema

```json
{
  "persona": "Marcus, mercantile magnate",
  "goal": "Maximize personal wealth and reduce taxation burden",
  "context": {
    "world_state_summary": "Inflation at 4%, unemployment 8%, food scarcity 30%",
    "time_step": 1542,
    "active_policies": ["POL-001: Universal Basic Income", "POL-003: Food Subsidies"]
  }
}
```

#### Output schema

```json
{
  "weights": {
    "economic_freedom": 0.85,
    "social_welfare": -0.60,
    "environmental_protection": 0.10,
    "public_order": 0.20,
    "innovation": 0.30,
    "cultural_preservation": -0.10
  },
  "confidence": 0.74,
  "reasoning": "Marcus's wealth-maximizing goal implies strong economic freedom support and opposition to redistributive welfare."
}
```

#### Constraints

- All 6 weights in `[-1.0, +1.0]`
- `confidence` in `[0.0, 1.0]`; `< 0.6` triggers ambiguity escalation
  → calls `tie-break.md`
- Output JSON only

#### Decision pipeline (per `ADR-003`)

```
1. RuleEngine computes baseline utility score for each action
2. Agent policy weight delta applied (this prompt's output)
3. UtilityScorer produces final score
4. AmbiguityCheck: max - min score vs DEFAULT_AMBIGUITY_THRESHOLD (0.05)
5. If ambiguous → escalate to tie-break.md
6. If still ambiguous → deterministic_fallback
```

---

### 3.6 `narrative-generation.md` (31B — news articles)

**Fires:** 0–3 times per tick, when a "newsworthy" event occurs
(mass death, policy change, election, drought start, riot). Used by the
media engine to produce articles shown in the News Feed.

#### System prompt (exact text)

```
You are a society simulation news writer. Given a list of recent
events and a state delta, write a 2-4 paragraph news article. Use a
neutral journalistic tone. All claims must be grounded in the input —
do not fabricate events, agents, or numbers. Scale tone to event
magnitude.
```

#### Input schema

```json
{
  "time_step": 1500,
  "events": [
    {
      "type": "drought_started",
      "agents_involved": [],
      "magnitude": 0.7,
      "description": "Sustained drought reduced water_availability from 0.90 to 0.27 for 30 ticks"
    },
    {
      "type": "mass_protest",
      "agents_involved": ["agent-007", "agent-019", "agent-022"],
      "magnitude": 0.45,
      "description": "23 agents protested against food scarcity"
    }
  ],
  "state_deltas": {
    "economic_health": -0.05,
    "social_cohesion": -0.10,
    "environmental_quality": -0.25,
    "public_order": -0.08,
    "innovation_index": 0.00
  }
}
```

#### Output schema

```json
{
  "headline": "Drought Grips the City: Water Supplies Plummet as Citizens Take to the Streets",
  "dateline": "Day 1500",
  "body": "A sustained drought has reduced water availability by 70%...",
  "bylines": ["Marcus the chronicler"],
  "spotlight_agent": null
}
```

#### Constraints

- `temperature=0.8` — creative, journalistic
- `max_tokens=512`
- Headline: 5-12 words, factual, no clickbait
- Body: 2-4 paragraphs, factual, scales tone to magnitude
- No fabrication: every claim must map to an input event or state delta
- Spotlight mode: if one agent is focal, mention them by name in headline

---

### 3.7 `governance-advisor.md` (31B — human operator)

**Fires:** on-demand when a human operator opens the governance console.
**Status: draft (deferred implementation).**

#### System prompt (exact text)

```
You are a society simulation policy advisor. Given the current world
state, active policies, and a list of pending decisions, produce a
concrete recommendation. The human operator is the final decision
authority — your output is advisory. Always recommend a specific
action; never defer.
```

#### Input schema

```json
{
  "world_state": {
    "economic_health": 0.45,
    "social_cohesion": 0.62,
    "environmental_quality": 0.40,
    "public_order": 0.70,
    "innovation_index": 0.55,
    "unlust": 0.35,
    "morality": 0.60
  },
  "active_policies": [
    {"id": "POL-001", "name": "Universal Basic Income", "age": 250, "effectiveness": 0.60, "side_effects": ["increased tax burden"]}
  ],
  "policy_options": [
    {"id": "POL-005", "name": "Water Rationing", "predicted_impact": "stabilize water access, may increase unrest"}
  ],
  "pending_decisions": [
    {"id": "DEC-042", "description": "Should water rationing begin immediately?", "deadline": "Day 1620"}
  ]
}
```

#### Output schema

```json
{
  "assessment": "Water availability has dropped to 27% due to ongoing drought. Current UBI is straining the treasury but preventing mass starvation.",
  "recommendation": {
    "action": "Enact POL-005 (Water Rationing) with phased rollout starting Day 1530",
    "rationale": "Rationing prevents complete water collapse (Day 175) while UBI maintains survival. Phased rollout reduces unrest risk.",
    "risk": "MEDIUM",
    "alternatives": ["Delay rationing 50 ticks (risk: Day 175 collapse)", "Full rationing Day 1500 (risk: +0.15 protest_intensity)"]
  },
  "watch_items": [
    "Monitor protest_intensity — if > 0.50, halt rationing",
    "Track water_availability — if < 0.15, emergency desalination"
  ]
}
```

#### Constraints

- `temperature=0.5` — balanced
- `max_tokens=384`
- Always a concrete action (no "consider", "maybe", "depending on")
- `risk` qualified: LOW | MEDIUM | HIGH
- `watch_items` must be specific (numeric thresholds, agent IDs, day numbers)

---

### 3.8 `system-prompts.md` (reusable components)

**Not a callable prompt** — a library of reusable instruction fragments that
other prompts compose. The 4 components are:

#### Determinism Anchor
```
You operate within a hybrid system where the deterministic engine
retains final decision authority. Your output is advisory — the
engine validates all responses before execution.
```
Used in: `tie-break.md`, `policy-translation.md`, `governance-advisor.md`

#### Simulation Fidelity
```
All outputs must be grounded in the provided simulation state. Do
not add information, events, or entities that were not present in
the input. If insufficient data exists to answer, state that
explicitly.
```
Used in: `narrative-generation.md`, `governance-advisor.md`

#### Persona Adherence
```
When reasoning about an agent, reference their persona traits and
stated goals. Do not assume motivations beyond what is documented
in the persona.
```
Used in: `policy-translation.md`, `tie-break.md`, `agent_decision.md` (implicit)

#### Output Rules
```
- Output only the requested format (JSON or natural language)
- Do not include meta-commentary about the instruction
- Do not prefix or suffix responses with explanations
- If confidence is low, include a confidence field rather than remaining silent
```
Used in: all prompts

#### Gemma 4 chat template

All prompts are wrapped by the `VLLMRouter` before sending to vLLM:

```
<bos><|start_header_id|>system<|end_header_id|>
{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

You write the system prompt and the user prompt separately. The router
combines them.

---

## 4. Event Integration

> **This is the new piece.** Previously, events were deterministic and the
> LLM never saw them. Now, when an environmental event is active, the
> engine injects an "active events" block into the agent's prompt so the
> LLM can reason about it.

### 4.1 The event context envelope

When `world.active_events` is non-empty at decision time, the engine adds
this block to the prompt (after world state, before action list):

```
⚠ ACTIVE EVENTS:
  [1] DROUGHT (severity=0.7, ticks_remaining=22, started=tick 145)
      Effect: water_availability reduced 0.90→0.27
      Food: unchanged. Crime: +0.10 unlust multiplier.
  [2] ECONOMIC_BOOM (severity=0.3, ticks_remaining=10, started=tick 165)
      Effect: salary_multiplier 1.0→1.30
```

The engine builds this from `world.active_events: List[WorldEvent]`. Each
event has: `event_type` (EventType enum), `severity` (0–1), `start_tick`,
`duration_ticks`, `metadata` (dict of effects).

The 5 event types the engine produces (per `environmental_events.py`):

| EventType | Severity range | Duration | Effect on world |
|---|---|---|---|
| `DROUGHT` | 0.2–0.8 | 20–40 ticks | `water_availability *= (1 - severity)` |
| `FLOOD` | 0.2–0.6 | 15–30 ticks | `food_availability *= (1 - severity)` |
| `ECONOMIC_BOOM` | 0.2–0.5 | 30–50 ticks | `salary_multiplier += severity * 0.5` |
| `ECONOMIC_BUST` | 0.2–0.5 | 30–50 ticks | `salary_multiplier -= severity * 0.5` |
| `RIOT` | varies | 5–15 ticks | `crime_rate += 0.5`, `protest_intensity += 0.3` |

### 4.2 The event-aware decision flow

```
tick_loop.run_tick(tick, agents, world, ...)
│
├── Step 7: maybe_schedule_event(world, rng, tick)
│   └── Adds event to world.active_events
│
├── Step 6: per-agent decision
│   └── For each living agent:
│       ├── if is_moral_dilemma: build_moral_dilemma_prompt (includes events)
│       ├── elif ambiguity > 0.05: build_tie_break_prompt (includes events)
│       └── else: build_agent_prompt (includes events)  ← NEW: events injected
│
├── Step 7b: trigger_riot(world)
│   └── May add a RIOT event to world.active_events
│
└── Step 11: process_media_tick(world)
    └── If any event was added this tick: build_narrative_prompt(events)
```

The `build_agent_prompt` function in `decision_engine.py:54-102` needs the
following modification (the AI engineer's job):

```python
# After world state, before action list:
active_events = getattr(world, "active_events", [])
if active_events:
    event_block = format_active_events(active_events)
    prompt += f"\n\n⚠ ACTIVE EVENTS:\n{event_block}"
```

Where `format_active_events` produces the envelope shown in §4.1.

### 4.3 Drought scenario template

**When:** `water_availability` drops below 0.5 due to `DROUGHT` event.
**What the LLM should see:**

```
hunger=0.20 water=0.45 sleep=0.70 safety=0.60
money=850 employed=True job=DOCTOR
mood=normal happiness=0.62 unlust=0.18 health=0.92
tax_rate=0.15 welfare=True food_avail=0.40
water_avail=0.27   ← DROUGHT effect

⚠ ACTIVE EVENT: DROUGHT (severity=0.7, ticks_remaining=22)
  Effect: water_availability reduced 0.90→0.27
  Food: unchanged. Crime: +0.10 unlust multiplier.

What do you do? Choose ONE: ...
```

**Expected LLM behavior:**
- A DOCTOR with high `morality` (0.65) and stable `unlust` (0.18) will likely
  keep working (TREAT patients) and may `buy_food` to stockpile.
- A POOR agent with low `unlust` (0.55) will likely `beg` or `share` (ask
  neighbors for water).
- A YOUNG agent with high `risk_tolerance` may `protest` against the lack of
  water infrastructure.

**Validation:** the engine validates the action. If the agent is in
`wealth_class.POOR` and `money < 20`, `buy_food` and `buy_property` are
rejected (can't afford). The fallback is `rest` or `idle`.

### 4.4 Riot scenario template

**When:** `protest_intensity > 0.3` AND a `RIOT` event is scheduled.
**What the LLM should see:**

```
hunger=0.55 water=0.60 sleep=0.50 safety=0.30   ← SAFETY LOW
money=200 employed=False job=UNEMPLOYED
mood=angry happiness=0.35 unlust=0.48 health=0.80
morality=0.45 anger=0.70 ambition=0.40
trust_govt=0.20   ← LOW TRUST
nearby=8 protesters_near=3   ← PROTESTERS NEAR
crime_rate=0.18 protest_intensity=0.42

⚠ ACTIVE EVENT: RIOT (severity=0.5, ticks_remaining=8)
  Effect: crime_rate +0.10, protest_intensity +0.15
  Safety -0.10 unlust multiplier.

What do you do? Choose ONE: ...
```

**Expected LLM behavior:**
- An agent with `anger_tendency=0.70` and `unlust=0.48` (above
  `ANGRY_UNLUST_THRESHOLD=0.45`) and `trust_govt=0.20` will likely `protest`
  or `harm_other` (rejected by safety override → downgraded to `protest`).
- An agent with `morality=0.80` and `risk_tolerance=0.30` will likely
  `isolate` or `console` (help victims).

**Validation:** the engine checks `if action == "harm_other" and morality
> 0.7: override_to("comply")`. The LLM's choice is preserved unless it
violates a safety rule.

### 4.5 New `event_response_prompt.md` (to author)

**Fires:** when a major event is scheduled (drought, flood, election) and
the engine wants the LLM to generate a *city-wide* response, not just per-agent.

#### Suggested frontmatter

```yaml
---
type: prompt
purpose: event-response
model: google/gemma-4-31b-it-qat
temperature: 0.3
max_tokens: 384
version: 1.0.0
status: draft
---
```

#### Suggested system prompt

```
You are a city planner in a society simulation. A major event has just
begun. Recommend a city-wide response: which agents should move, which
resources should be redirected, which policies should be enacted. Output
JSON only. The simulation engine applies your recommendations as policy
deltas.
```

#### Suggested input schema

```json
{
  "event": {
    "type": "DROUGHT",
    "severity": 0.7,
    "duration_ticks": 30,
    "started_tick": 1500
  },
  "current_world_state": {
    "food_availability": 0.40,
    "water_availability": 0.27,
    "population": 80,
    "unemployment_rate": 0.08,
    "protest_intensity": 0.20,
    "tax_revenue_pool": 1200
  }
}
```

#### Suggested output schema

```json
{
  "recommended_policies": [
    {
      "name": "Water Rationing",
      "effect": "Cap daily water consumption per agent at 0.05",
      "duration_ticks": 30,
      "predicted_impact": "Stabilize water_availability at 0.27, increase unlust by 0.05"
    }
  ],
  "agent_movements": [
    {"from_grid": [3, 4], "to_grid": [10, 10], "agent_count": 5, "reason": "Relocate from drought zone"}
  ],
  "resource_redirects": [
    {"from_pool": "tax_revenue_pool", "amount": 200, "to_subsidy": "water_subsidy"}
  ],
  "confidence": 0.68
}
```

This prompt is **deferred** — the AI engineer should add it as a
`status: draft` first, validate the schema, and mark it `active` only
after at least 10 successful event responses in production.

---

## 5. Prompt Validation & Test Fixtures

The CI pipeline includes a `prompt-validation` job
(`.github/workflows/ci.yml`) that runs on every PR. It checks:

1. Every `prompts/*.md` has the required frontmatter (`type`, `purpose`,
   `model`, `temperature`, `max_tokens`, `version`, `status`).
2. Every prompt's `version` is semver and ≥ 1.0.0.
3. Every prompt has an `Input Schema` and `Output Schema` section in the
   body.
4. Test fixtures exist in `tests/fixtures/prompts/expected_outputs.json`
   for every `purpose: active` prompt.

### Test fixtures: what they look like

Existing fixture at `tests/fixtures/prompts/expected_outputs.json` is
**out of date** — it references v1 need names (`FOOD`, `SOCIAL`, `LEISURE`,
`SHELTER`) instead of v2's 13-need Maslow system. **It needs an update.**

#### Updated `persona-generation` fixture

```json
{
  "persona-generation": {
    "input": {
      "traits": {
        "assertiveness": 0.9,
        "cooperation": 0.2,
        "risk_tolerance": 0.8,
        "altruism": 0.1,
        "traditionalism": 0.3,
        "materialism": 0.7,
        "idealism": 0.2,
        "ambition": 0.9
      }
    },
    "expected_output": {
      "name": "Marcus",
      "archetype": "mercantile magnate",
      "persona": "A man in early adulthood, working as a construction worker with limited financial means, driven by an unyielding ambition to build wealth."
    }
  }
}
```

#### Updated `agent-decision` fixture (with event context)

```json
{
  "agent-decision": {
    "input": {
      "agent": {
        "id": "agent-007",
        "age": 35,
        "job_type": "DOCTOR",
        "wealth_class": "MIDDLE",
        "needs": {
          "FOOD": 0.20, "WATER": 0.45, "SLEEP": 0.70, "SAFETY": 0.60,
          "SOCIAL_CONNECTION": 0.55, "SELF_ESTEEM": 0.50, "REPUTATION": 0.55
        },
        "resources": {"money": 850, "employed": true, "health": 0.92},
        "traits": {
          "morality": 0.65, "anger_tendency": 0.30, "ambition": 0.55,
          "extraversion": 0.45, "creativity": 0.60, "resilience": 0.70,
          "dominance_urge": 0.35, "risk_tolerance": 0.40
        },
        "unlust": 0.18,
        "emotion": "NORMAL",
        "trust_in_govt": 0.55
      },
      "world": {
        "tax_rate": 0.15,
        "welfare_enabled": true,
        "food_availability": 0.40,
        "water_availability": 0.27,
        "crime_rate": 0.08,
        "unemployment_rate": 0.04
      },
      "active_events": [
        {
          "event_type": "DROUGHT",
          "severity": 0.7,
          "ticks_remaining": 22,
          "metadata": {"original_water_availability": 0.90}
        }
      ]
    },
    "expected_output": {
      "action": "treat",
      "feeling": "concerned",
      "reason": "As a doctor, I should help those suffering from water scarcity rather than stockpile."
    }
  }
}
```

#### New `event-drought-response` fixture (to add)

```json
{
  "event-drought-response": {
    "input": {
      "event": {
        "type": "DROUGHT",
        "severity": 0.7,
        "duration_ticks": 30,
        "started_tick": 1500
      },
      "current_world_state": {
        "food_availability": 0.40,
        "water_availability": 0.27,
        "population": 80,
        "unemployment_rate": 0.08,
        "protest_intensity": 0.20
      }
    },
    "expected_output": {
      "recommended_policies": [
        {
          "name": "Water Rationing",
          "duration_ticks": 30,
          "predicted_impact": "Stabilize water at 0.27, unlust +0.05"
        }
      ],
      "resource_redirects": [
        {"from": "tax_revenue_pool", "amount": 200, "to": "water_subsidy"}
      ],
      "confidence": 0.68
    }
  }
}
```

#### New `event-riot-response` fixture (to add)

```json
{
  "event-riot-response": {
    "input": {
      "event": {"type": "RIOT", "severity": 0.5, "duration_ticks": 8},
      "current_world_state": {
        "crime_rate": 0.18,
        "protest_intensity": 0.42,
        "trust_in_govt": 0.30
      }
    },
    "expected_output": {
      "recommended_policies": [
        {
          "name": "Increased Police Patrol",
          "duration_ticks": 10,
          "predicted_impact": "Reduce crime_rate by 0.05, increase unlust by 0.03"
        }
      ],
      "confidence": 0.55
    }
  }
}
```

### How to add a new prompt fixture

1. Edit `tests/fixtures/prompts/expected_outputs.json`.
2. Add a top-level key matching `purpose:` from the prompt's frontmatter.
3. Provide a realistic `input` and a deterministic `expected_output`.
4. Run the prompt-validation CI job — it should pass.
5. Commit.

---

## 6. End-to-End Tick Worked Example

A single 500-tick walkthrough showing every LLM call the simulation makes.
This is the canonical trace for understanding the full system.

### Setup

```
seed = 42
population = 80
ticks = 500
default config (post-calibration):
  ANGRY_UNLUST_THRESHOLD = 0.45
  DESPAIR_UNLUST_THRESHOLD = 0.55
  UNLUST_MORALITY_GATE = 0.38
  BIRTH_CHANCE_BASE = 0.005
  FOOD_DECAY_RATE = 0.012
  WATER_DECAY_RATE = 0.008
  SLEEP_DECAY_RATE = 0.02
  AGE_MORTALITY_BASE = 0.0001
  AGE_MORTALITY_ELDERLY = 0.001
  ECONOMIC_HARDSHIP_DEATH_RATE = 0.001
```

### Tick 0: simulation start

```
Calls to LLM:
  1. persona-generation.md × 80 (one per new agent)
     → 80 narrative personas written
     → Engine stores in agent.persona (string)
  2. policy-translation.md × 4 (one per default policy)
     → 4 sets of utility weights returned
     → Engine applies as deltas
Total: 84 calls
```

### Tick 1–50: stable equilibrium

```
Calls to LLM (per tick):
  - agent_decision.md × 80 (every agent)
    → 80 decisions returned
    → Engine validates, ~2–3 fall back to deterministic_fallback
  - moral_reasoning.md × 0–2 (only when dilemma detected)
  - tie-break.md × 0–1 (only when ambiguity > 0.05)
  - narrative-generation.md × 0 (no newsworthy events)
Total: ~80–85 calls/tick
```

### Tick 51: drought event scheduled

```
Tick 51, Step 7: maybe_schedule_event(rng=42) → fires
  → Adds DROUGHT to world.active_events
  → severity=0.7, duration=30 ticks
  → Effect: water_availability *= (1 - 0.7) = 0.27
  → 1 narrative-generation.md call (magnitude=0.7 → newsworthy)
```

**Sample agent prompt (agent-007, DOCTOR) at tick 51:**

```
hunger=0.20 water=0.45 sleep=0.70 safety=0.60
money=850 employed=True job=DOCTOR
mood=normal happiness=0.62 unlust=0.18 health=0.92
morality=0.65 anger=0.30 ambition=0.55
nearby=4 protesters_near=0 needy_near=1
tax_rate=0.15 welfare=True food_avail=0.85
water_avail=0.27   ← DROUGHT effect (was 0.90)

⚠ ACTIVE EVENT: DROUGHT (severity=0.7, ticks_remaining=29)
  Effect: water_availability reduced 0.90→0.27

What do you do? Choose ONE: ...

LLM response: {"action":"treat","feeling":"concerned","reason":"As a doctor, I should help those suffering from water scarcity."}
Engine validates: action in enum ✓, no safety override, accepted.
```

### Tick 100: protest_intensity crosses 0.3

```
Tick 100, Step 9: update_world_metrics
  → protest_intensity = 0.32 (crossed 0.3)
Tick 100, Step 7b: trigger_riot(world)
  → Adds RIOT to world.active_events
  → severity=0.5, duration=8 ticks
  → Effect: crime_rate += 0.10
  → 1 narrative-generation.md call
```

**Sample agent prompt (agent-019, UNEMPLOYED) at tick 100:**

```
hunger=0.55 water=0.30 sleep=0.50 safety=0.30   ← SAFETY LOW
money=200 employed=False job=UNEMPLOYED
mood=angry happiness=0.35 unlust=0.48 health=0.80
morality=0.45 anger=0.70 ambition=0.40
trust_govt=0.20
nearby=8 protesters_near=3   ← PROTESTERS NEAR
crime_rate=0.18 protest_intensity=0.42

⚠ ACTIVE EVENTS:
  [1] DROUGHT (severity=0.7, ticks_remaining=8)
  [2] RIOT (severity=0.5, ticks_remaining=8)
      Effect: crime_rate +0.10, protest_intensity +0.15

What do you do? Choose ONE: ...

LLM response: {"action":"protest","feeling":"enraged","reason":"The drought has gone on too long; the government's response is inadequate."}
Engine validates: protest in enum ✓, no safety override, accepted.
```

### Tick 200: tie-break fires (ambiguity > 0.05)

```
Tick 200, Step 6: per-agent decision
  → agent-022 scores:
      work = 0.51
      buy_food = 0.49   ← ambiguity 0.02 < 0.05 ✗
  → agent-031 scores:
      beg = 0.52
      steal = 0.50   ← ambiguity 0.02 < 0.05 ✗
  → agent-047 scores:
      work = 0.48
      buy_food = 0.43
      rest = 0.43   ← top-2 within 0.05 ✓
      → TIE-BREAK TRIGGERED
```

**Tie-break call for agent-047:**

```json
Input:
{
  "id": "tb-2024-200-047",
  "state": "agent-047, MIDDLE class, employed, normal emotion, drought ending",
  "unlust": 0.18,
  "morality": 0.70,
  "options": [
    {"label": "work", "action": "WORK", "utility_scores": {"economic": 0.50, "social": 0.46, "environmental": 0.48}},
    {"label": "buy_food", "action": "BUY_FOOD", "utility_scores": {"economic": 0.45, "social": 0.41, "environmental": 0.43}},
    {"label": "rest", "action": "REST", "utility_scores": {"economic": 0.40, "social": 0.46, "environmental": 0.43}}
  ]
}

Output:
{
  "action": "work",
  "confidence": 0.62,
  "reason": "Drought is ending, agent is healthy, no urgent need for food. Work maintains economic stability."
}
```

### Tick 250: narrative generation (drought end + riot aftermath)

```
Tick 250, Step 7: cleanup_expired_events
  → DROUGHT ends (tick 175 was 30 ticks after tick 145 = tick 175; current 250)
  → RIOT ended
Tick 250, Step 11: process_media_tick
  → Detects 2 events expired
  → Builds narrative-generation input with 2 events
  → 1 narrative-generation.md call
```

**Sample narrative call:**

```
Input:
{
  "time_step": 250,
  "events": [
    {"type": "drought_ended", "magnitude": 0.7, "description": "30-tick drought ended; water_availability restored from 0.27 to 0.90"},
    {"type": "riot_suppressed", "magnitude": 0.5, "description": "8-tick riot ended; protest_intensity fell from 0.45 to 0.20"}
  ],
  "state_deltas": {
    "economic_health": -0.10,
    "social_cohesion": -0.15,
    "environmental_quality": 0.10,
    "public_order": -0.05
  }
}

Output:
{
  "headline": "Drought Lifts After 30-Day Siege; City Counts the Cost",
  "dateline": "Day 250",
  "body": "Water has finally returned to normal levels after a punishing 30-day drought that cut supplies to 27% of capacity. The economic damage is estimated at 10% of GDP, and social trust has eroded as citizens endured rationing. A simultaneous riot further strained public order, though the unrest has now subsided. Officials are calling for water infrastructure investment to prevent future crises...",
  "bylines": ["auto-media"]
}
```

### Tick 500: simulation ends

```
Final state:
  Population: 84/80 (grew by 5%)
  Total deaths: 72
  Total crimes: 344
  Total protests: 344
  Happiness: 0.571
  Unlust: 0.39
  Wealth: 29 poor, 14 middle, 41 rich
  Emotions: 24 happy, 51 normal, 4 despair, 5 angry
  Actions fired: 23/25 (idle and family_bond never fired)

Total LLM calls across 500 ticks: ~40,200
  - 80×500 = 40,000 agent_decision
  - 80×500×0.04 = 1,600 moral_reasoning (4% of decisions are dilemmas)
  - 40 tie-break (1 per ~12 ticks)
  - 12 narrative-generation (events + riots)
  - 4 policy-translation (initial + 3 mid-run adjustments)
```

---

## 7. Determinism Guarantees & Failure Modes

### What is deterministic

| Component | Determinism | Reason |
|---|---|---|
| `DeterministicRNG` | Yes | Seeded numpy generator |
| Engine tick loop | Yes | Same input → same output |
| `E2B` (agent brain) | Yes | `temperature=0.0` |
| `deterministic_fallback` | Yes | Hand-coded function |
| `MockAIRouter` | Yes | Trait-aware weighted random with fixed seed |

### What is non-deterministic

| Component | Non-determinism | Mitigation |
|---|---|---|
| `26B A4B` (moral reasoning) | `temperature=0.2` | Engine accepts variance; can re-query |
| `31B` (tie-break, persona, narrative) | `temperature=0.2-0.7` | Engine validates; falls back on bad output |
| vLLM server failure | N/A — server is down | Engine uses `MockAIRouter` |
| Network timeout (> 3s) | N/A | Engine uses `MockAIRouter` |
| Invalid JSON response | N/A | Engine retries once, then `deterministic_fallback` |

### Failure mode handling

| Failure | Detection | Recovery |
|---|---|---|
| LLM returns invalid JSON | `parse_response` raises | Retry once; if still fails, `deterministic_fallback` |
| LLM returns unknown action | `validate_action` raises | Log, use `deterministic_fallback` |
| LLM returns `harm_other` with high morality | `safety_override` | Downgrade to `comply` |
| LLM returns `steal` with high money | `safety_override` | Downgrade to `share` |
| LLM times out (> 3s) | `requests.Timeout` | Use `MockAIRouter` |
| vLLM server 5xx | HTTP status | Use `MockAIRouter` |
| E2B down, 26B down, 31B down | All routes fail | `MockAIRouter` (deterministic) |

### The contract

**The engine is the source of truth. The LLM is advisory.** If the LLM and
the engine disagree, the engine wins. The LLM's job is to add *human-like
variety* to decisions that the deterministic function would otherwise handle
mechanically. If the LLM is unavailable, the simulation continues with
`deterministic_fallback` — it's just less interesting.

---

## 8. Glossary

| Term | Definition |
|---|---|
| **ActionType** | The 25-action enum: `work`, `buy_food`, `rest`, `seek_job`, `beg`, `befriend`, `console`, `isolate`, `share`, `steal`, `harm_other`, `fraud`, `treat`, `protest`, `counsel`, `complain`, `campaign`, `comply`, `spread_rumor`, `support_family`, `invest`, `buy_property`, `hobby`, `idle`, `family_bond` |
| **Ambiguity threshold** | If top-2 action scores are within 0.05, escalate to `tie-break.md` |
| **Determinism anchor** | Reusable system-prompt component reminding the LLM that the engine retains authority |
| **Deterministic fallback** | The engine's hand-coded action selection when LLM is unavailable |
| **EventType** | The 5 environmental event types: `DROUGHT`, `FLOOD`, `ECONOMIC_BOOM`, `ECONOMIC_BUST`, `RIOT` |
| **Hybrid decision fusion** | ADR-003: engine scores baseline, LLM contributes weight, final score is combined |
| **MockAIRouter** | Deterministic trait-aware LLM simulator used when vLLM is unavailable |
| **Moral dilemma** | A decision where the agent faces a genuine ethical conflict (e.g., steal vs. beg while starving) |
| **Persona** | 1-2 sentence description of an agent generated once at birth |
| **Prompt** | A `.md` file in `prompts/` with YAML frontmatter defining model, temperature, max_tokens |
| **RuleEngine** | The deterministic action-selection function in `decision_engine.deterministic_fallback` |
| **Tick** | One simulation step (10-50ms wall time, 0.1 years of simulated time) |
| **Tie-break** | The `tie-break.md` prompt fired when ambiguity > 0.05 |
| **Unlust** | Aggregate suffering metric (0-1); combination of all needs |
| **VLLMRouter** | The router that dispatches prompts to the right Gemma 4 model |

---

## 9. Appendices

### Appendix A: Frontmatter contract

```yaml
---
type: prompt                    # always "prompt"
purpose: <unique-key>            # matches filename and test fixture key
model: <model-name>              # e.g. google/gemma-4-e2b-it-qat
temperature: 0.0–1.0             # 0.0 for determinism, higher for creativity
max_tokens: 32–1024              # hard cap
version: X.Y.Z                  # semver; breaking changes increment major
status: active|draft|deprecated  # active prompts are tested in CI
---
```

### Appendix B: 25-action enum (canonical order)

```
work, buy_food, rest, seek_job, beg, befriend, console, isolate,
share, steal, harm_other, fraud, treat, protest, counsel, complain,
campaign, comply, spread_rumor, support_family, invest, buy_property,
hobby, idle, family_bond
```

The 13-need enum (also canonical order):
```
FOOD, WATER, SLEEP, SAFETY, SEXUAL_TENSION, SOCIAL_CONNECTION,
FAMILY, ROMANTIC, SELF_ESTEEM, REPUTATION, FINANCIAL_SECURITY,
SHELTER, HEALTH
```

### Appendix C: Model selection matrix

| Need | Model | Reason |
|---|---|---|
| Fast, deterministic, per-agent decisions | E2B | 27ms median, 80 calls/tick |
| Mid-frequency moral reasoning | 26B A4B | Balance of speed and depth |
| Slow, high-stakes decisions | 31B | Used for tie-break, persona, narrative |
| Failure path | `MockAIRouter` | Deterministic, no GPU required |

### Appendix D: 8-trait SOCIETAS vector (canonical order)

```
morality, anger_tendency, ambition, extraversion, creativity,
resilience, dominance_urge, risk_tolerance
```

> **⚠ Note:** The current `persona-generation.md` references OCEAN traits
> which is **wrong**. The v2 engine uses the 8 SOCIETAS traits above. The
> AI engineer must update the prompt.

### Appendix E: The 5-event type schema

```python
class EventType(Enum):
    DROUGHT = "drought"            # water_availability *= (1 - severity)
    FLOOD = "flood"                # food_availability *= (1 - severity)
    ECONOMIC_BOOM = "economic_boom"  # salary_multiplier += severity * 0.5
    ECONOMIC_BUST = "economic_bust"  # salary_multiplier -= severity * 0.5
    RIOT = "riot"                  # crime_rate += 0.10, protest_intensity += 0.15
```

### Appendix F: Sample CI integration

The `.github/workflows/ci.yml` runs the `prompt-validation` job:

```yaml
prompt-validation:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Validate prompts
      run: python tools/scripts/validate_prompts.py
    - name: Validate test fixtures
      run: python tools/scripts/validate_fixtures.py
```

Where:
- `validate_prompts.py` checks every `prompts/*.md` has valid frontmatter
- `validate_fixtures.py` checks every `active` prompt has a fixture in
  `tests/fixtures/prompts/expected_outputs.json`

### Appendix G: What the AI engineer should do first

1. **Read this guide end-to-end** (~30 min).
2. **Read `shared/types/enums.py`** to confirm the canonical 25-action
   enum and 13-need enum.
3. **Read `decision_engine.py:54-148`** to see how prompts are built.
4. **Update `persona-generation.md`** to use 8 SOCIETAS traits (not OCEAN).
5. **Update `agent_decision.md` and `moral_reasoning.md`** to add the
   `⚠ ACTIVE EVENTS:` block (§4.1).
6. **Update `decision_engine.py:build_agent_prompt`** to inject active
   events into the prompt when `world.active_events` is non-empty.
7. **Add new `event_response_prompt.md`** (§4.5) with `status: draft`.
8. **Update `tests/fixtures/prompts/expected_outputs.json`** with v2
   schemas and 2 new event fixtures.
9. **Run `pytest tests/unit/simulation/`** — should be 510+ pass.
10. **Open a PR** titled `feat(ai): event-aware prompts + v2 schema
    alignment` and request review from `@societas/ai-systems-engineer`.

### Appendix H: What NOT to do

- **Don't change the engine code** to bypass validation. The engine
  validates every LLM output; that's a safety invariant.
- **Don't increase `temperature` above 0.0 for E2B**. Determinism is
  critical for reproducibility.
- **Don't add new action names** without updating the `ActionType` enum
  and the validation logic in `decision_engine.py`.
- **Don't skip the test fixture** when adding a new prompt. CI will fail.
- **Don't add new event types** without updating `environmental_events.py`
  and the event context envelope in §4.1.
- **Don't make the LLM the source of truth** for any state change. The
  LLM is advisory; the engine owns state.

---

*Last updated: 2026-07-11. Author: Simulation Engineer (after v2 engine
calibration campaign). Reviewer: AI Systems Engineer. Version: 1.0.0.*
