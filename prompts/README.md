# Prompts

Canonical source of truth for all AI prompts used by the SOCIETAS simulation.

## Purpose Categories

| Prompt | Type | Model | Temperature | Context |
|--------|------|-------|-------------|---------|
| `persona-generation.md` | One-time | Gemma 2 9B IT | 0.7 | Creates agent personas from 8 input traits |
| `policy-translation.md` | Recurring | Gemma 2 9B IT | 0.3 | Translates agent goals to utility weights |
| `tie-break.md` | On-demand | Gemma 2 9B IT | 0.2 | Resolves high-ambiguity decisions |
| `narrative-generation.md` | Recurring | Gemma 2 9B IT | 0.8 | Generates news and narrative summaries |
| `governance-advisor.md` | Interactive | Gemma 2 9B IT | 0.5 | Policy advice for human operators |

## Engineering Principles

- **Deterministic output** for tie-break: `temperature=0.2`, JSON schema enforced
- **Creative output** for narrative: `temperature=0.8`, no schema
- **Versioning**: All prompts have a `version` field in frontmatter; breaking changes increment major
- **Testing**: Each prompt has expected-output examples in `tests/fixtures/prompts/`

## Workflow

1. Draft in `vault/070-Prompts/` (working copy with iteration history)
2. Freeze and copy to this directory (source of truth)
3. Reference by path in code — never embed prompt strings directly
4. Tag prompt versions in Git for reproducibility

## Related

- `vault/070-Prompts/` — [Prompt working drafts and iteration history](../vault/070-Prompts/README.md)
- `docs/guides/ai-agent-rules.md` — [AI agent prompt governance and versioning](../docs/guides/ai-agent-rules.md)
- `docs/references/architecture-overview.md` — [Cognitive reasoning layer context](../docs/references/architecture-overview.md)
