# AI Prompts

Canonical prompt templates for the 3× Gemma 4 model cluster driving agent cognition and governance.

## Key Files

- `persona-generation.md` — Agent persona from 8 traits (Gemma 4, temp 0.7)
- `policy-translation.md` — Goal-to-utility weight translation (temp 0.3)
- `tie-break.md` — High-ambiguity decision resolution (temp 0.2)
- `narrative-generation.md` — News and narrative summaries (temp 0.8)
- `governance-advisor.md` — Interactive policy advice for operators (temp 0.5)

## How to Use

Reference by file path in code — never embed prompt strings directly. Tag prompt versions in Git for reproducibility.

## Dependencies

- Referenced by `models/` and `simulation/` at runtime
