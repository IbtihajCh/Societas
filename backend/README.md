# Backend — API Server & Model Router

**Owner:** Backend Engineer

Serves the FastAPI application that connects all system layers. Handles REST API requests, WebSocket connections for real-time simulation data, and routes LLM requests to the vLLM inference server.

## Responsibilities

- REST API for simulation control and querying
- WebSocket server for real-time dashboard updates
- Request routing to vLLM (Gemma 26B / 9B)
- Queue management for batched inference
- Data persistence and storage layer
- API documentation (OpenAPI / Swagger)

## Dependencies

- `simulation/` — imports simulation engine for state queries
- `frontend/` — serves API consumed by the dashboard
- `prompts/` — uses prompt templates for LLM requests

## Conventions

- FastAPI application entry point: `app/main.py`
- Routers in `app/routers/`
- Models in `app/models/`
- Services in `app/services/`
- All API changes require integration tests

## Related

- [Coding Standards](../docs/guides/coding-standards.md)
- [Architecture Overview](../docs/references/architecture-overview.md)
- [ADR Records](../docs/adr/)
