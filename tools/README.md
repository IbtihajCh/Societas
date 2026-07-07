# Tools — Developer Tooling Configuration

**Owner:** Technical Lead / Infrastructure

Shared configuration for development tools used across the project. These configurations ensure consistent code quality, formatting, and behavior across all six team members.

## Configuration Files

| File | Tool | Purpose |
|------|------|---------|
| `pyproject.toml` | Python tooling | ruff, mypy, pytest configuration |
| `package.json` | Node tooling | npm workspace config, lint scripts |
| `.pre-commit-config.yaml` | pre-commit | Git hook configuration |
| `.editorconfig` | EditorConfig | Cross-editor formatting settings |

## Pre-commit Hooks

The project uses pre-commit to enforce code quality before commits reach CI:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

## Related

- [Coding Standards](../docs/guides/coding-standards.md)
- [CI Workflows](../.github/workflows/)
- [CONTRIBUTING](../CONTRIBUTING.md)
