# Docker & Orchestration

Container definitions and compose configuration for consistent, reproducible SOCIETAS deployments.

## Key Files

- `backend.Dockerfile` — FastAPI backend image
- `frontend.Dockerfile` — Next.js frontend image
- `vllm-rocm.Dockerfile` — vLLM serving on AMD MI300X (ROCm)
- `docker-compose.yml` — Full stack orchestration
- `.env.example` — Environment variable template

## How to Run

**Native (recommended for demo):**
```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
docker compose -f docker/docker-compose.yml up -d
```

## Dependencies

- Docker, Docker Compose
- AMD ROCm (for vLLM service)
