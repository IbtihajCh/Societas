# Build & Deploy Scripts

Idempotent automation scripts for development, testing, and deployment.

## Key Files

- `setup.sh` / `setup.ps1` — One-command environment bootstrap
- `test.sh` / `test.ps1` — Full test suite runner
- `lint.sh` / `lint.ps1` — Cross-project linting
- `clean.sh` / `clean.ps1` — Build artifact cleanup

## How to Run

```bash
# macOS / Linux
./scripts/setup.sh

# Windows
./scripts/setup.ps1
```

## Dependencies

- Bash or PowerShell
- Python 3.11+, Node.js 18+
