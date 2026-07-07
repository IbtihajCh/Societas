# Setup Guide — Local Development Environment

This guide walks through setting up a complete SOCIETAS development environment.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Simulation engine, backend |
| Node.js | 20+ | Frontend |
| Docker | 24+ | Containerized services |
| Git | 2.40+ | Version control |
| Make | Optional | Convenience commands |
| CUDA (optional) | 12.x | Local vLLM / Gemma inference |

---

## Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/societas/societas.git
cd societas
```

### 2. Run the Setup Script

**macOS / Linux:**
```bash
./scripts/setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

The setup script will:
- Create Python virtual environments for `simulation/` and `backend/`
- Install Python dependencies
- Install frontend dependencies
- Install pre-commit hooks
- Create a `.env` file from the template

### 3. Manual Setup (if scripts fail)

#### Simulation

```bash
cd simulation
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for development
```

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Frontend

```bash
cd frontend
npm install
```

#### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

---

## Docker Setup

For running the full stack:

```bash
cp docker/.env.example docker/.env
docker compose -f docker/docker-compose.yml up -d
```

This starts:
- Backend API on port 8000
- Frontend on port 3000
- vLLM router on port 8001 (if GPU available)

---

## Verifying the Setup

```bash
# Run all tests
./scripts/test.sh

# Run all linters
./scripts/lint.sh
```

All tests should pass. If they don't, check:

- Python version: `python --version`
- Node version: `node --version`
- Docker: `docker --version`

---

## Obsidian Vault

The vault at `/vault` is an Obsidian workspace. To use it:

1. Open Obsidian
2. Click "Open folder as vault"
3. Select the `societas/vault` directory

The `.obsidian/` configuration is version-controlled, so all team members share the same plugin settings.

---

## vLLM / Gemma (Optional)

For local LLM inference:

```bash
# Install vLLM (Linux with CUDA)
pip install vllm

# Start the vLLM server with Gemma
python -m vllm.entrypoints.openai.api_server \
    --model google/gemma-2-9b-it \
    --port 8001
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `command not found` | Check prerequisites are installed |
| Port conflicts | Check `docker/.env` for port mappings |
| GPU not detected | Install CUDA toolkit and verify `nvidia-smi` |
| Test failures | Ensure you're in the correct virtual environment |

If issues persist, check [GitHub Issues](https://github.com/societas/societas/issues) or ask in the team chat.

---

## Related

- [Development Workflow](development-workflow.md)
- [Coding Standards](coding-standards.md)
- [Docker Compose](../../docker/docker-compose.yml)
- [CONTRIBUTING](../../CONTRIBUTING.md)
