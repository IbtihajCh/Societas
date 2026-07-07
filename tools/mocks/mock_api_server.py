"""
Mock FastAPI Server
====================

Standalone mock API server for frontend development.
Implements all SOCIETAS API endpoints with realistic fake data.
Run independently of the real backend.

Usage:
    uvicorn tools.mocks.mock_api_server:app --port 8000
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import json
from datetime import datetime


app = FastAPI(title="SOCIETAS Mock API", version="0.1.0-mock")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---

@app.get("/api/v1/health")
async def health() -> Dict[str, Any]:
    """Mock health check."""
    return {
        "status": "healthy",
        "version": "0.1.0-mock",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/v1/ready")
async def ready() -> Dict[str, Any]:
    """Mock readiness check."""
    return {"ready": True}


# --- Simulation ---

@app.get("/api/v1/simulation/status")
async def get_simulation_status() -> Dict[str, Any]:
    """Mock simulation status."""
    # TODO: Return realistic mock status
    return {
        "isRunning": False,
        "currentTick": 0,
        "population": 1000,
        "startedAt": None,
    }


@app.post("/api/v1/simulation/start")
async def start_simulation(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Mock start simulation."""
    # TODO: Implement mock start
    return {
        "isRunning": True,
        "currentTick": 0,
        "population": config.get("populationSize", 1000) if config else 1000,
        "startedAt": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/api/v1/simulation/stop")
async def stop_simulation() -> Dict[str, Any]:
    """Mock stop simulation."""
    # TODO: Implement mock stop
    return {
        "isRunning": False,
        "currentTick": 100,
        "population": 1000,
        "startedAt": None,
    }


@app.post("/api/v1/simulation/tick")
async def advance_tick() -> Dict[str, Any]:
    """Mock advance tick."""
    # TODO: Implement mock tick with realistic state changes
    return {
        "tick": 1,
        "agentsActed": 950,
        "events": [],
        "newState": {},
    }


@app.get("/api/v1/simulation/state")
async def get_simulation_state() -> Dict[str, Any]:
    """Mock simulation state."""
    # TODO: Return realistic mock state from contracts/examples/
    return {
        "tick": 0,
        "economy": {"gdp": 5000000.0, "unemployment_rate": 0.08, "inflation_rate": 0.02, "wealth_distribution": []},
        "crime": {"crime_rate": 0.05, "enforcement_effectiveness": 0.75, "crime_types": {}},
        "needs": {"average_needs": {}, "fulfillment_rates": {}},
        "psychology": {"average_morality": 0.72, "average_happiness": 0.65, "average_stress": 0.35, "emotional_distribution": {}},
    }


@app.post("/api/v1/simulation/reset")
async def reset_simulation() -> Dict[str, Any]:
    """Mock reset simulation."""
    # TODO: Implement mock reset
    return {
        "isRunning": False,
        "currentTick": 0,
        "population": 1000,
        "startedAt": None,
    }


# --- Policies ---

@app.get("/api/v1/policies")
async def list_policies(active_only: bool = True) -> Dict[str, Any]:
    """Mock list policies."""
    # TODO: Return mock policies from contracts/examples/
    return {"policies": [], "total": 0}


@app.post("/api/v1/policies")
async def create_policy(policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock create policy."""
    # TODO: Implement mock create
    return {
        "id": "policy-mock-001",
        "name": policy_data.get("name", "Mock Policy"),
        "description": policy_data.get("description", ""),
        "category": policy_data.get("category", "ECONOMIC"),
        "weights": {},
        "enactedAt": datetime.utcnow().isoformat() + "Z",
        "isActive": True,
    }


@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id: str) -> Dict[str, Any]:
    """Mock get policy."""
    # TODO: Implement mock get
    return {
        "id": policy_id,
        "name": "Mock Policy",
        "description": "A mock policy for testing",
        "category": "ECONOMIC",
        "weights": {},
        "enactedAt": datetime.utcnow().isoformat() + "Z",
        "isActive": True,
    }


@app.delete("/api/v1/policies/{policy_id}")
async def revoke_policy(policy_id: str) -> Dict[str, Any]:
    """Mock revoke policy."""
    # TODO: Implement mock revoke
    return {
        "id": policy_id,
        "name": "Mock Policy",
        "description": "A mock policy for testing",
        "category": "ECONOMIC",
        "weights": {},
        "enactedAt": datetime.utcnow().isoformat() + "Z",
        "isActive": False,
    }


# --- Metrics ---

@app.get("/api/v1/metrics")
async def get_metrics(tick_from: int | None = None, tick_to: int | None = None) -> Dict[str, Any]:
    """Mock get metrics."""
    # TODO: Return realistic mock metrics
    return {
        "metrics": [],
        "tickRange": {"from": tick_from or 0, "to": tick_to or 0},
    }


@app.get("/api/v1/metrics/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """Mock get dashboard data."""
    # TODO: Return realistic mock dashboard data
    return {
        "currentTick": 0,
        "population": 1000,
        "metrics": {},
        "recentEvents": [],
    }


# --- Agents ---

@app.get("/api/v1/agents")
async def list_agents(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """Mock list agents."""
    # TODO: Return mock agents from contracts/examples/
    return {"agents": [], "total": 0}


@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Mock get agent."""
    # TODO: Return realistic mock agent
    return {
        "id": agent_id,
        "persona": "A mock agent persona",
        "traits": {},
        "wealth": 1000.0,
        "employmentStatus": "EMPLOYED",
        "happiness": 0.65,
        "health": 0.80,
        "lastActionTick": 0,
        "recentActions": [],
    }


@app.get("/api/v1/agents/{agent_id}/history")
async def get_agent_history(agent_id: str) -> List[Dict[str, Any]]:
    """Mock get agent history."""
    # TODO: Return realistic mock history
    return []


# --- WebSocket ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Mock WebSocket endpoint."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: Implement mock WebSocket message handling
            await websocket.send_json({"type": "mock", "data": {}})
    except Exception:
        await websocket.close()
