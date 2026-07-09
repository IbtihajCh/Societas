"""Tests for the GridSystem."""

import pytest
from shared.types.aliases import AgentId
from simulation.world.grid import GridSystem


class TestGridSystem:
    def test_place_agent(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("a1"), 5, 10)
        assert grid.get_position(AgentId("a1")) == (5, 10)
        assert len(grid) == 1

    def test_place_agent_wraps(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("a1"), 25, -5)
        assert grid.get_position(AgentId("a1")) == (5, 15)

    def test_move_agent_basic(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("a1"), 5, 5)
        pos = grid.move_agent(AgentId("a1"), 3, -2)
        assert pos == (8, 3)

    def test_move_agent_wraps(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("a1"), 18, 18)
        pos = grid.move_agent(AgentId("a1"), 5, 5)
        assert pos == (3, 3)

    def test_move_agent_not_on_grid(self) -> None:
        grid = GridSystem()
        with pytest.raises(KeyError):
            grid.move_agent(AgentId("a1"), 1, 1)

    def test_toroidal_distance_normal(self) -> None:
        grid = GridSystem()
        d = grid.toroidal_distance(5, 5, 8, 9)
        assert d == pytest.approx(5.0, rel=0.1)

    def test_toroidal_distance_wrap(self) -> None:
        grid = GridSystem()
        d = grid.toroidal_distance(0, 0, 19, 19)
        assert d == pytest.approx(1.414, rel=0.1)

    def test_toroidal_distance_self(self) -> None:
        grid = GridSystem()
        d = grid.toroidal_distance(5, 5, 5, 5)
        assert d == 0.0

    def test_get_nearby_agents(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("center"), 0, 0)
        grid.place_agent(AgentId("near"), 1, 1)
        grid.place_agent(AgentId("far"), 10, 10)
        grid.place_agent(AgentId("wrap_near"), 19, 19)
        nearby = grid.get_nearby_agents(AgentId("center"))
        assert AgentId("near") in nearby
        assert AgentId("far") not in nearby
        assert AgentId("wrap_near") in nearby

    def test_remove_agent(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("a1"), 5, 5)
        grid.remove_agent(AgentId("a1"))
        assert len(grid) == 0
        with pytest.raises(KeyError):
            grid.get_position(AgentId("a1"))

    def test_get_all_positions(self) -> None:
        grid = GridSystem()
        grid.place_agent(AgentId("a1"), 0, 0)
        grid.place_agent(AgentId("a2"), 1, 1)
        all_pos = grid.get_all_positions()
        assert len(all_pos) == 2
        assert AgentId("a1") in all_pos
