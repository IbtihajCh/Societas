# SOCIETAS Obsidian Vault

The team's central knowledge base. Every design decision, sprint note, meeting record, research finding, and feature specification lives here.

## Vault Structure

| Folder | Purpose | Owner |
|--------|---------|-------|
| `000-Index/` | Map of Content (MOC) — entry point for navigation | All |
| `010-Architecture/` | System architecture notes, diagrams, models | Technical Lead |
| `020-Decisions/` | ADR mirror — linked from `docs/adr/` | Technical Lead |
| `030-Sprints/` | Sprint planning, retrospectives, velocity tracking | All |
| `040-Meetings/` | Meeting notes organized by date | All |
| `050-Research/` | External research, papers, benchmarks | AI Systems Engineer |
| `060-Features/` | Feature specifications (one note per feature) | All |
| `070-Prompts/` | Prompt library — source of truth for prompts | AI Systems Engineer |
| `080-Infrastructure/` | Infrastructure notes, deployment records | DevOps Engineer |
| `090-Reference/` | External references, templates, attachments | All |
| `095-Roles/` | Personal role guides (gitignored — each member creates their own) | Individual |
| `100-Mastermind/` | Project context, engineering rules, skeleton spec, audit | All |

## Conventions

- **Naming:** `YYYY-MM-DD-title.md` for dated notes, `kebab-case-title.md` for evergreen notes
- **Links:** Use `[[wikilinks]]` within vault, `[label](path)` for repo cross-references
- **Properties:** Every note has YAML frontmatter with `type`, `status`, `tags`
- **Graph:** Folder prefixes enforce consistent ordering in the graph view

## Related

- `docs/adr/` — [Architecture Decision Records](../docs/adr/README.md)
- `docs/templates/meeting-notes.md` — [Meeting note template](../docs/templates/meeting-notes.md)
- `docs/templates/feature-spec.md` — [Feature specification template](../docs/templates/feature-spec.md)
- `docs/templates/sprint-plan.md` — [Sprint planning template](../docs/templates/sprint-plan.md)
