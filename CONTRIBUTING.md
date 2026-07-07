# Contributing to SOCIETAS

Thank you for contributing. This project follows strict engineering practices to ensure quality, explainability, and parallel development safety.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Workflow](#development-workflow)
- [Getting Started](#getting-started)
- [Branching Strategy](#branching-strategy)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [AI Agent Rules](#ai-agent-rules)
- [Code Review Standards](#code-review-standards)

---

## Code of Conduct

All contributors must adhere to the [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, constructive, and professional.

---

## Development Workflow

Every feature follows this mandatory pipeline:

```
Research → Specification → Architecture → Planning → Implementation → Testing → Documentation → Review → Merge
```

No step may be skipped. For minor bugfixes, the Technical Lead may grant exceptions.

See [docs/guides/development-workflow.md](docs/guides/development-workflow.md) for details.

---

## Getting Started

1. Read the [Master Context](docs/SOCIETAS_Master_Context.md) document
2. Review open [Architecture Decision Records](docs/adr/)
3. Set up your environment per [setup guide](docs/guides/setup.md)
4. Identify your subsystem ownership in [CODEOWNERS](.github/CODEOWNERS)

---

## Branching Strategy

We follow a subsystem-prefixed branching model:

```
main          # Production-ready code
sim/feature   # Simulation subsystem changes
ai/feature    # AI/Gemma subsystem changes
be/feature    # Backend API changes
fe/feature    # Frontend changes
infra/feature # Infrastructure/DevOps changes
docs/feature  # Documentation changes
```

See [docs/guides/branching-strategy.md](docs/guides/branching-strategy.md) for the full strategy.

---

## Commit Guidelines

- Use conventional commits: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`
- Scopes: `sim`, `ai`, `be`, `fe`, `infra`, `docs`, `vault`
- Keep commits atomic — one logical change per commit
- Reference issues and ADRs in commit messages

```
feat(sim): implement needs-based decision scoring
Refs: #42, ADR-005
```

---

## Pull Request Process

1. Create a branch following the naming convention above
2. Implement your changes following the development workflow
3. Ensure all tests pass locally
4. Update documentation — every behavioral change requires a doc update
5. Update `CHANGELOG.md` under the `[Unreleased]` section
6. Create a pull request using the [PR template](.github/PULL_REQUEST_TEMPLATE.md)
7. Request review from the relevant subsystem owner (see CODEOWNERS)
8. Address review feedback
9. Squash-merge into `main`

AI agents must never merge their own PRs without human review.

---

## Testing Requirements

- All new code must have tests
- Simulation code requires >90% branch coverage
- Backend API requires integration tests
- Frontend requires component tests
- AI prompts require validation tests
- Run the full test suite before opening a PR: `./scripts/test.sh` (or `.\scripts\test.ps1`)

See [docs/guides/coding-standards.md](docs/guides/coding-standards.md#testing) for detailed requirements.

---

## Documentation Requirements

Every change that affects behavior must update:

1. **`CHANGELOG.md`** — add entry under `[Unreleased]`
2. **Related ADR** — update status if decision changes
3. **Subsystem README** — update if interfaces change
4. **Vault notes** — update Obsidian vault if architecture changes

AI agents must document their reasoning when making architectural decisions.

---

## AI Agent Rules

If you are an AI coding agent working on this repository:

1. Read this entire document before making any changes
2. Read the [AI Agent Rules](docs/guides/ai-agent-rules.md) document
3. Load all relevant ADRs for your subsystem
4. Never skip the development workflow
5. Never modify files outside your ownership without explicit approval
6. Document every architectural decision in the appropriate ADR
7. Verify tests pass before marking work complete

---

## Code Review Standards

Reviewers evaluate:

- **Correctness**: Does the code do what it claims?
- **Explainability**: Is the reasoning clear?
- **Determinism**: Does the simulation remain deterministic?
- **Test coverage**: Are edge cases covered?
- **Documentation**: Are changes reflected in docs?
- **Cross-references**: Are related documents linked?
- **Performance**: Are there obvious bottlenecks?

No PR may be merged without at least one approval from the relevant subsystem owner.
