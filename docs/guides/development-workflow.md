# Development Workflow

Every feature in SOCIETAS follows this mandatory pipeline. No step may be skipped. This applies to both human developers and AI coding agents.

---

## The Pipeline

```
Research → Specification → Architecture → Planning → Implementation → Testing → Documentation → Review → Merge
```

### 1. Research

Understand the problem space before writing code.

- Read relevant ADRs and existing documentation
- Review the Master Context for architectural alignment
- Check the vault for related research notes
- Identify dependencies on other subsystems

**Output:** Research notes in `vault/050-Research/`

### 2. Specification

Define precisely what needs to be built.

- Write a feature specification using the [template](../templates/feature-spec.md)
- Define acceptance criteria (must be testable)
- Define interfaces (inputs, outputs, error states)
- Get technical lead approval for cross-subsystem changes

**Output:** Feature spec in `vault/060-Features/`

### 3. Architecture

Determine how the feature fits into the system.

- Create or update an ADR if the decision has architectural impact
- Document interfaces between subsystems
- Define data flow and state transitions
- Consider determinism and explainability

**Output:** ADR in `docs/adr/` (if needed)

### 4. Planning

Break the work into implementable units.

- Create tasks in the sprint tracking system
- Estimate effort per task
- Identify dependencies and coordination points
- Assign ownership

**Output:** Sprint plan in `vault/030-Sprints/`

### 5. Implementation

Write the code.

- Follow the [branching strategy](branching-strategy.md)
- Follow [coding standards](coding-standards.md)
- Commit frequently with conventional commit messages
- Push early to get CI feedback

### 6. Testing

Verify correctness.

- Write tests before or alongside implementation
- Run the full test suite locally
- Ensure coverage meets minimums
- For simulation: verify determinism (same seed = same result)
- For AI: validate prompt schemas

### 7. Documentation

Document what was built.

- Update `CHANGELOG.md`
- Update subsystem README if interfaces changed
- Update vault notes
- Create or update ADR if architecture was affected

### 8. Review

Open a PR and request review.

- Follow the [PR template](../../.github/PULL_REQUEST_TEMPLATE.md)
- Ensure CI passes
- Address review feedback
- Squash-merge into `main`

### 9. Merge

Complete the cycle.

- Delete the feature branch
- Verify deployment (if applicable)
- Update sprint tracking

---

## Exceptions

The Technical Lead may grant exceptions for:

- **Critical bug fixes** — Skip research/spec/architecture; still require testing and documentation
- **Trivial changes** — Typos, formatting, minor refactoring; still require review
- **AI agent limitations** — An agent may skip a step they cannot perform (e.g., attending a meeting), but must document their work thoroughly

---

## AI Agent Workflow

AI coding agents must:

1. Read this document before making any changes
2. Read [AI Agent Rules](ai-agent-rules.md)
3. Load all relevant ADRs
4. Load subsystem README and coding standards
5. Execute the pipeline steps they can perform autonomously
6. Flag decisions that need human review
7. Never merge their own PRs

---

## Related

- [AI Agent Rules](ai-agent-rules.md)
- [Branching Strategy](branching-strategy.md)
- [Coding Standards](coding-standards.md)
- [Feature Spec Template](../templates/feature-spec.md)
- [CONTRIBUTING](../../CONTRIBUTING.md)
