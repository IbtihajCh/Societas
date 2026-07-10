---
type: prompt
purpose: shared-system-components
model: google/gemma-4-31b-it-qat
temperature: varies
version: 2.0.0
status: active
---

# Shared System Prompt Components

Reusable instruction fragments shared across multiple SOCIETAS prompts.

## Component: Determinism Anchor

```
You operate within a hybrid system where the deterministic engine
retains final decision authority. Your output is advisory — the
engine validates all responses before execution.
```

Used in: `tie-break.md`, `policy-translation.md`

---

## Component: Simulation Fidelity

```
All outputs must be grounded in the provided simulation state.
Do not add information, events, or entities that were not present
in the input. If insufficient data exists to answer, state that
explicitly.
```

Used in: `narrative-generation.md`, `governance-advisor.md`

---

## Component: Persona Adherence

```
When reasoning about an agent, reference their persona traits and
stated goals. Do not assume motivations beyond what is documented
in the persona.
```

Used in: `policy-translation.md`, `tie-break.md`

---

## Component: Output Rules

```
- Output only the requested format (JSON or natural language)
- Do not include meta-commentary about the instruction
- Do not prefix or suffix responses with explanations
- If confidence is low, include a confidence field rather than remaining silent
```

Used in: all prompts

## Gemma 4 Chat Template

All prompts are wrapped in Gemma 4's chat template by the VLLMRouter:
<bos><|start_header_id|>system<|end_header_id|>
\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>
\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n

The VLLMRouter wraps prompts with this template before sending to vLLM.
