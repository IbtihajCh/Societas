from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient

from shared.dto.policy_dto import PolicyCreateRequestDTO
from shared.interfaces.i_simulation_engine import ISimulationEngine
from shared.schemas.agent_state import AgentState, AgentTraits, AgentNeeds, AgentEmotions, AgentResources
from shared.schemas.metrics import SimulationMetrics
from shared.schemas.policy import Policy, PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import TickResult
from shared.types.aliases import AgentId, PolicyId, TickNumber
from shared.types.enums import EmploymentStatus, PolicyCategory, WealthClass

from backend.app.database.connection import close_db, init_db
from backend.app.dependencies import set_engine
from backend.app.main import app


@pytest.fixture
def mock_engine():
    engine = create_autospec(ISimulationEngine, instance=True)
    engine.get_current_tick.return_value = TickNumber(42)
    engine.is_running.return_value = True
    engine.get_agents.return_value = []
    engine.get_state.return_value = SimulationState(
        time_step=TickNumber(42),
        population=100,
        economic_health=0.75,
        social_cohesion=0.6,
        environmental_quality=0.5,
        public_order=0.8,
        innovation_index=0.6,
        unlust=0.1,
        morality=0.7,
    )
    engine.get_metrics.return_value = SimulationMetrics()
    return engine


@pytest.fixture(autouse=True)
def setup_db():
    import asyncio
    import os
    from backend.app.database.connection import init_db, close_db
    from backend.app.config import get_settings
    db_path = get_settings().database_path
    asyncio.run(init_db())
    yield
    asyncio.run(close_db())
    if os.path.exists(db_path):
        os.remove(db_path)
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"
    if os.path.exists(wal_path):
        os.remove(wal_path)
    if os.path.exists(shm_path):
        os.remove(shm_path)


@pytest.fixture(autouse=True)
def setup_engine(mock_engine):
    set_engine(mock_engine)
    yield
    set_engine(None)


def make_agent_state(agent_id="agent-001"):
    return AgentState(
        id=AgentId(agent_id),
        persona="A test agent",
        traits=AgentTraits(morality=0.7, creativity=0.5),
        employment_status=EmploymentStatus.EMPLOYED,
        wealth_class=WealthClass.MIDDLE,
        age=30,
        is_alive=True,
        location="default",
    )


@pytest.fixture(autouse=True)
def mock_agent_get(mock_engine):
    mock_engine.get_agent.side_effect = lambda agent_id: make_agent_state(agent_id) if agent_id == "agent-001" else None


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_policy():
    return Policy(
        id=PolicyId("policy-001"),
        name="Universal Basic Income",
        description="Monthly stipend for all citizens",
        category=PolicyCategory.ECONOMIC,
        weights=PolicyWeights(economic_freedom=0.3, social_welfare=0.8),
        is_active=True,
        enactment_tick=0,
    )


@pytest.fixture
def sample_policy_request():
    return PolicyCreateRequestDTO(
        name="Test Policy",
        description="A test policy",
        category=PolicyCategory.ECONOMIC,
        weights={"economic_freedom": 0.5, "innovation": 0.3},
    )
