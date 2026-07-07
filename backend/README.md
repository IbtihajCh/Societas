# Backend API Module

**Owner:** Backend Engineer

## Purpose

FastAPI-based REST API for SOCIETAS simulation. Provides the interface between the frontend dashboard and the simulation/AI modules.

## Responsibilities

- REST API endpoints for simulation control
- WebSocket connections for real-time updates
- Policy CRUD operations
- Metrics and dashboard data aggregation
- Agent query and management
- Request validation and error handling

## Dependencies

- `shared/` - Shared schemas, DTOs, and interfaces
- `simulation/` - Simulation engine
- `models/` - AI router
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `websockets` - WebSocket support

## API Endpoints

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

### Simulation
- `GET /api/v1/simulation/status` - Get simulation status
- `POST /api/v1/simulation/start` - Start simulation
- `POST /api/v1/simulation/stop` - Stop simulation
- `POST /api/v1/simulation/tick` - Advance one tick
- `GET /api/v1/simulation/state` - Get current state
- `POST /api/v1/simulation/reset` - Reset simulation

### Policies
- `GET /api/v1/policies/` - List policies
- `POST /api/v1/policies/` - Create policy
- `GET /api/v1/policies/{id}` - Get policy
- `DELETE /api/v1/policies/{id}` - Revoke policy

### Metrics
- `GET /api/v1/metrics/` - Get metrics
- `GET /api/v1/metrics/dashboard` - Get dashboard data

### Agents
- `GET /api/v1/agents/` - List agents
- `GET /api/v1/agents/{id}` - Get agent
- `GET /api/v1/agents/{id}/history` - Get agent history

### WebSocket
- `WS /ws` - Real-time simulation updates

## Future Work

- Implement all endpoint handlers
- Add service layer for business logic
- Add repository layer for data persistence
- Implement WebSocket event streaming
- Add authentication and authorization
- Add rate limiting
- Implement caching layer
- Add comprehensive error handling
