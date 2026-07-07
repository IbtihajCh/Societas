# Scripts — Build, Deploy & Utility Scripts

**Owner:** Infrastructure / DevOps Engineer

Contains scripts for local development, testing, building, and deployment. All scripts are provided in both PowerShell (Windows) and Bash (macOS/Linux).

## Available Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` / `setup.ps1` | One-command development environment bootstrap |
| `lint.sh` / `lint.ps1` | Run all linters across the project |
| `test.sh` / `test.ps1` | Run the full test suite |
| `clean.sh` / `clean.ps1` | Clean build artifacts and caches |

## Conventions

- All scripts are idempotent (safe to run multiple times)
- PowerShell scripts use `.ps1` extension
- Bash scripts use `.sh` extension
- Scripts print clear error messages on failure
- No script requires interactive input

## Related

- [Setup Guide](../docs/guides/setup.md)
- [Docker Compose](../docker/docker-compose.yml)
- [CI Workflows](../.github/workflows/)
