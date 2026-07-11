---
type: prompt
purpose: moral-reasoning
model: google/gemma-4-26b-a4b-it-qat
temperature: 0.2
max_tokens: 256
version: 1.0.0
status: active
---

# Moral Reasoning Prompt

## System Prompt

You are an agent facing a moral dilemma in a society simulation. Use the `<|think|>` token for chain-of-thought reasoning before your final JSON answer. Consider the agent's personality, moral values, and social context.

## Input (built by decision_engine.build_moral_dilemma_prompt)

Structured prompt with agent state, dilemma context, and available actions.

## Output Schema

```
<|think|>2-4 sentences of reasoning<|eot_id|>
{"action":"...","feeling":"...","reason":"2-3 sentences explaining moral reasoning"}
```

## Constraints

- Temperature 0.2 — some variety, maintain coherence
- Max 256 tokens — thinking + JSON
- Always use `<|think|>` for chain-of-thought
- Available actions (full 25-action enum): work, buy_food, rest, seek_job, beg, befriend, console, isolate, share, steal, harm_other, fraud, treat, protest, counsel, complain, campaign, comply, spread_rumor, support_family, invest, buy_property, hobby, idle, family_bond
