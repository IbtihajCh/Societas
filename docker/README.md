# Docker — Container Definitions & Orchestration

**Owner:** Infrastructure / DevOps Engineer

Contains Dockerfiles and docker-compose configuration for the entire SOCIETAS stack. Enables consistent development environments and reproducible builds.

## Quick Start (No Docker - Recommended for AMD Act 2 Demo)

```bash
# Windows
start.bat

# Linux/Mac
bash start.sh
```

Or directly:
```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server runs on **http://localhost:8000** with API docs at **http://localhost:8000/docs**.

Configuration via `.env` file (copy from `docker/.env.example`):
```bash
cp docker/.env.example .env
```

## Services (Docker)

| Service | Dockerfile | Port | Dependencies |
|---------|-----------|------|-------------|
| `backend` | `backend.Dockerfile` | 8000 | — |
| `frontend` | `frontend.Dockerfile` | 3000 | backend |
| `vllm` | `vllm-rocm.Dockerfile` | 8001 | — (ROCm / AMD GPU) |

## Docker Deploy

```bash
docker compose -f docker/docker-compose.yml up -d
```

Set API keys in `docker/.env`:
```bash
cp docker/.env.example docker/.env
# Edit docker/.env with your AMD Developer Console API keys
```
