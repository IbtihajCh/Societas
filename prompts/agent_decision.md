---
type: prompt
purpose: agent-decision
model: google/gemma-4-e2b-it-qat
temperature: 0.0
max_tokens: 64
version: 1.0.0
status: active
---

# Agent Decision Prompt

## System Prompt

You are an agent in a society simulation. Your decisions are validated by the simulation engine — output only the requested JSON format. You must choose a single action based on your current state.

## Input (built by decision_engine.build_agent_prompt)

Structured prompt with agent needs, traits, resources, mood, nearby agents, and world state.

## Output Schema

```json
{"action":"work|buy_food|rest|seek_job|beg|befriend|console|isolate|share|steal|harm_other|fraud|treat|protest|counsel|complain|campaign|comply|spread_rumor|support_family|invest|buy_property|hobby|idle|family_bond","feeling":"one-word feeling","reason":"one sentence explaining choice"}
```

## Constraints

- Temperature 0.0 — deterministic, no thinking token
- Max 64 tokens — brief response only
- No chain-of-thought — just the JSON
