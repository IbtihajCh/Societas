"""
Pytest Configuration
====================

Shared fixtures and configuration for all tests.
"""

import pytest
from typing import Dict, Any
import json
from pathlib import Path


@pytest.fixture
def sample_agent_traits() -> Dict[str, float]:
    """Sample agent traits for testing."""
    return {
        "openness": 0.7,
        "conscientiousness": 0.6,
        "extraversion": 0.8,
        "agreeableness": 0.5,
        "neuroticism": 0.3,
        "morality": 0.9,
        "risk_tolerance": 0.4,
        "patience": 0.6,
    }


@pytest.fixture
def sample_agent_state(sample_agent_traits) -> Dict[str, Any]:
    """Sample agent state for testing."""
    return {
        "id": "agent-001",
        "traits": sample_agent_traits,
        "needs": {
            "levels": {
                "FOOD": 0.2,
                "SHELTER": 0.1,
                "SAFETY": 0.3,
                "SOCIAL": 0.5,
                "LEISURE": 0.4,
            }
        },
        "emotions": {
            "levels": {
                "HAPPINESS": 0.6,
                "STRESS": 0.3,
                "FEAR": 0.1,
                "ANGER": 0.0,
            }
        },
        "resources": {
            "wealth": 1500.0,
            "health": 0.85,
        },
        "decision_scores": {
            "WORK": 0.7,
            "SOCIALIZE": 0.5,
            "REST": 0.3,
            "COMMIT_CRIME": 0.1,
        },
    }


@pytest.fixture
def sample_simulation_state() -> Dict[str, Any]:
    """Sample simulation state for testing."""
    return {
        "tick": 100,
        "economy": {
            "gdp": 5000000.0,
            "unemployment_rate": 0.08,
            "inflation_rate": 0.02,
            "wealth_distribution": [100, 200, 500, 1000, 2000, 5000],
        },
        "crime": {
            "crime_rate": 0.05,
            "enforcement_effectiveness": 0.75,
            "crime_types": {
                "THEFT": 0.02,
                "FRAUD": 0.01,
                "VIOLENCE": 0.005,
                "DRUGS": 0.015,
            },
        },
        "needs": {
            "average_needs": {
                "FOOD": 0.25,
                "SHELTER": 0.20,
                "SAFETY": 0.30,
                "SOCIAL": 0.45,
                "LEISURE": 0.35,
            },
            "fulfillment_rates": {
                "FOOD": 0.85,
                "SHELTER": 0.90,
                "SAFETY": 0.75,
                "SOCIAL": 0.60,
                "LEISURE": 0.50,
            },
        },
        "psychology": {
            "average_morality": 0.72,
            "average_happiness": 0.65,
            "average_stress": 0.35,
            "emotional_distribution": {
                "HAPPY": 0.45,
                "CONTENT": 0.30,
                "STRESSED": 0.15,
                "UNHAPPY": 0.10,
            },
        },
    }


@pytest.fixture
def sample_policy() -> Dict[str, Any]:
    """Sample policy for testing."""
    return {
        "id": "policy-001",
        "name": "Universal Basic Income",
        "description": "Provides monthly stipend to all citizens",
        "category": "ECONOMIC",
        "weights": {
            "FOOD": 0.3,
            "SHELTER": 0.2,
            "SAFETY": 0.1,
            "SOCIAL": 0.15,
            "LEISURE": 0.1,
        },
        "enacted_at": "2026-07-07T10:00:00Z",
        "is_active": True,
    }


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_data_dir() -> Path:
    """Path to mock data directory."""
    return Path(__file__).parent / "mock_data"


@pytest.fixture
def load_fixture(fixtures_dir):
    """Fixture loader function."""
    def _load(filename: str) -> Dict[str, Any]:
        filepath = fixtures_dir / filename
        with open(filepath, "r") as f:
            return json.load(f)
    return _load


@pytest.fixture
def load_mock_data(mock_data_dir):
    """Mock data loader function."""
    def _load(filename: str) -> Dict[str, Any]:
        filepath = mock_data_dir / filename
        with open(filepath, "r") as f:
            return json.load(f)
    return _load
