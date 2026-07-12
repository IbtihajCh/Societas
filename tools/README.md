# Developer Tooling

Shared configuration for code quality, formatting, and pre-commit enforcement across the project.

## Key Files

- `pyproject.toml` — ruff, mypy, pytest settings
- `package.json` — npm workspace and lint scripts
- `.pre-commit-config.yaml` — Git hook definitions
- `.editorconfig` — Cross-editor formatting rules

## How to Run

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Dependencies

- pre-commit, ruff, mypy
- EditorConfig plugin (IDE)
