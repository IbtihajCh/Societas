---
type: prompt
purpose: tie-break
model: google/gemma-4-31b-it-qat
temperature: 0.2
max_tokens: 196
version: 2.0.0
status: active
---

# Tie-Break Decision

## System Prompt

You are the final arbiter in a governance simulation. Two or more policy options have been scored as equally viable by the deterministic engine. Analyze the context and break the tie. Output only valid JSON.

## Input Schema

```json
{
  "id": "string — unique decision identifier",
  "state": "string — current world state summary",
  "unlust": "float — systemic dissatisfaction metric",
  "morality": "float — aggregate ethical alignment score [-1.0, 1.0]",
  "options": [
    {
      "label": "string — option label matching DecisionOption.label",
      "action": "string — ActionType enum value",
      "utility_scores": {
        "economic": "float",
        "social": "float",
        "environmental": "float"
      }
    }
  ]
}
```

## Output Schema

```json
{
  "action": "string — the label or ActionType from the chosen option",
  "confidence": 0.0..1.0,
  "reason": "string — concise justification (1 sentence)"
}
```

## Constraints

- Must output valid JSON only — no additional text
- Confidence < 0.5 should be treated as a system alert (decision still accepted)
- Reason must reference specific simulation metrics (state, unlust, morality), not abstract principles

## Determinism Guarantee

- `temperature=0.2` ensures near-deterministic output for identical inputs
- If confidence is low, the simulation logs the event for manual review but does not halt
- The RuleEngine retains ownership of the final execution — Gemma contributes the decision weight, the engine applies it
