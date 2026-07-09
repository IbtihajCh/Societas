# Docker — Container Definitions & Orchestration

**Owner:** Infrastructure / DevOps Engineer

Contains Dockerfiles and docker-compose configuration for the entire SOCIETAS stack. Enables consistent development environments and reproducible builds.

## Services

| Service | Dockerfile | Port | Dependencies |
|---------|-----------|------|-------------|
| `backend` | `backend.Dockerfile` | 8000 | simulation, vllm |
| `simulation` | `simulation.Dockerfile` | — | — |
| `frontend` | `frontend.Dockerfile` | 3000 | backend |
| `vllm` | `vllm-rocm.Dockerfile` | 8001 | — (ROCm / AMD GPU) |

## Quick Start

```bash
docker compose -f docker/docker-compose.yml up -d
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp docker/.env.example docker/.env
```

## Related

- [Setup Guide](../docs/guides/setup.md)
- [CI Workflows](../.github/workflows/)
- [Scripts](../scripts/README.md)
