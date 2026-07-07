# Prompt Library Index

Maps prompts in the vault to their canonical versions in `prompts/`.

| Prompt | Vault Note | Source |
|--------|-----------|--------|
| Persona Generation | `persona-generation.md` | `prompts/persona-generation.md` |
| Policy Translation | `policy-translation.md` | `prompts/policy-translation.md` |
| Tie-Break Decision | `tie-break.md` | `prompts/tie-break.md` |
| Narrative Generation | `narrative-generation.md` | `prompts/narrative-generation.md` |
| Governance Advisor | `governance-advisor.md` | `prompts/governance-advisor.md` |
| System Prompts | `system-prompts.md` | `prompts/system-prompts.md` |

## Conventions

- Vault notes are the **working draft** space (experiments, versions, test results)
- `prompts/*.md` is the **source of truth** — copy from vault when finalized
- Each prompt has YAML frontmatter: `type: prompt`, `model: gemma-2-9b-it`, `temperature: 0.X`
- Version history in prompt frontmatter

## Related

- `prompts/` — [Canonical prompt files](../../prompts/README.md)
- `docs/guides/ai-agent-rules.md` — [AI agent prompt governance](../../docs/guides/ai-agent-rules.md)
