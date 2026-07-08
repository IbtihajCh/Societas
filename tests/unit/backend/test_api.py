import pytest
from fastapi import status

from shared.dto.metrics_dto import MetricsResponseDTO
from shared.dto.simulation_dto import SimulationStateResponseDTO, SimulationStatusDTO
from shared.types.aliases import TickNumber
from shared.types.enums import PolicyCategory

from backend.app.dependencies import set_engine


class TestHealthEndpoints:
    def test_health_endpoint(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "societas-backend"

    def test_ready_endpoint(self, client):
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestSimulationEndpoints:
    def test_get_status(self, client):
        response = client.get("/api/v1/simulation/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["tick"] == 42

    def test_start_simulation(self, client):
        response = client.post("/api/v1/simulation/start", json={
            "population_size": 100,
            "seed": None,
            "speed": 1.0,
            "config": {},
        })
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "tick" in data

    def test_stop_simulation(self, client):
        response = client.post("/api/v1/simulation/stop")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "tick" in data

    def test_advance_tick_when_not_started(self, client):
        set_engine(None)
        response = client.post("/api/v1/simulation/tick")
        assert response.status_code == 400

    def test_get_state(self, client):
        response = client.get("/api/v1/simulation/state")
        assert response.status_code == 200
        data = response.json()
        assert data["tick"] == 42

    def test_reset_simulation(self, client):
        response = client.post("/api/v1/simulation/reset")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "tick" in data


class TestPolicyEndpoints:
    def test_list_policies_empty(self, client, mock_engine):
        from backend.app.repositories.policy_repository import PolicyRepository
        repo = PolicyRepository()
        import asyncio
        async def load_all():
            return []
        repo.load_all = load_all
        response = client.get("/api/v1/policies/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_create_policy(self, client, sample_policy_request):
        response = client.post("/api/v1/policies/", json={
            "name": sample_policy_request.name,
            "description": sample_policy_request.description,
            "category": 1,
            "weights": {"economic_freedom": 0.5, "innovation": 0.3},
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Policy"
        assert data["is_active"] is True

    def test_get_policy_not_found(self, client):
        response = client.get("/api/v1/policies/nonexistent")
        assert response.status_code == 404

    def test_revoke_policy_not_found(self, client):
        response = client.delete("/api/v1/policies/nonexistent")
        assert response.status_code == 404


class TestMetricsEndpoints:
    def test_get_metrics(self, client):
        response = client.get("/api/v1/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert "current_tick" in data

    def test_get_dashboard_data(self, client):
        response = client.get("/api/v1/metrics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAgentEndpoints:
    def test_list_agents_empty(self, client):
        response = client.get("/api/v1/agents/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_get_agent_not_found(self, client):
        response = client.get("/api/v1/agents/nonexistent")
        assert response.status_code == 404

    def test_get_agent_history(self, client):
        response = client.get("/api/v1/agents/agent-001/history")
        assert response.status_code == 200
