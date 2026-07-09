"""Grid system — 20×20 toroidal grid for agent spatial interactions.

All coordinates wrap toroidally (going off one edge appears on the opposite edge).
The grid tracks agent positions and supports spatial queries for nearby agents.

Uses shared.types.aliases.GridCoordinate for grid positions.
"""


from shared.constants.defaults import GRID_SIZE, INTERACTION_RADIUS
from shared.types.aliases import AgentId, GridCoordinate


class GridSystem:
    """Manages agent positions on a N×N toroidal grid.

    Attributes:
        _positions: Maps agent IDs to their (x, y) grid coordinates.
        _reverse: Maps grid coordinates to lists of agent IDs at that position.
    """

    def __init__(self) -> None:
        self._positions: dict[AgentId, tuple[GridCoordinate, GridCoordinate]] = {}
        self._reverse: dict[tuple[int, int], list[AgentId]] = {}

    def place_agent(self, agent_id: AgentId, x: int, y: int) -> None:
        """Place an agent at (x, y). Wraps coordinates to grid bounds.

        Args:
            agent_id: The agent to place.
            x: X coordinate (wrapped to [0, GRID_SIZE-1]).
            y: Y coordinate (wrapped to [0, GRID_SIZE-1]).
        """
        x = x % GRID_SIZE
        y = y % GRID_SIZE
        self._positions[agent_id] = (GridCoordinate(x), GridCoordinate(y))
        key = (x, y)
        if key not in self._reverse:
            self._reverse[key] = []
        if agent_id not in self._reverse[key]:
            self._reverse[key].append(agent_id)

    def move_agent(self, agent_id: AgentId, dx: int, dy: int) -> tuple[int, int]:
        """Move agent by delta (dx, dy). Returns new (x, y) after toroidal wrapping.

        Args:
            agent_id: The agent to move.
            dx: X delta (positive = right, wraps toroidally).
            dy: Y delta (positive = down, wraps toroidally).

        Returns:
            The new (x, y) position after movement.

        Raises:
            KeyError: If the agent is not on the grid.
        """
        if agent_id not in self._positions:
            raise KeyError(f"Agent {agent_id} not on grid")
        old_x, old_y = self._positions[agent_id]
        new_x = (int(old_x) + dx) % GRID_SIZE
        new_y = (int(old_y) + dy) % GRID_SIZE
        # Remove from old position
        old_key = (int(old_x), int(old_y))
        if old_key in self._reverse and agent_id in self._reverse[old_key]:
            self._reverse[old_key].remove(agent_id)
            if not self._reverse[old_key]:
                del self._reverse[old_key]
        # Place at new position
        self._positions[agent_id] = (GridCoordinate(new_x), GridCoordinate(new_y))
        new_key = (new_x, new_y)
        if new_key not in self._reverse:
            self._reverse[new_key] = []
        self._reverse[new_key].append(agent_id)
        return (new_x, new_y)

    def get_position(self, agent_id: AgentId) -> tuple[int, int]:
        """Get agent's current (x, y) position.

        Returns:
            Tuple of (x, y) as integers.

        Raises:
            KeyError: If the agent is not on the grid.
        """
        if agent_id not in self._positions:
            raise KeyError(f"Agent {agent_id} not on grid")
        return (int(self._positions[agent_id][0]), int(self._positions[agent_id][1]))

    def toroidal_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Compute shortest Euclidean distance between two points on toroidal grid.

        The toroidal distance considers the wrap-around paths (going off one
        edge and appearing on the opposite edge).

        Args:
            x1: X coordinate of first point.
            y1: Y coordinate of first point.
            x2: X coordinate of second point.
            y2: Y coordinate of second point.

        Returns:
            The shortest Euclidean distance.
        """
        dx = min(abs(x1 - x2), GRID_SIZE - abs(x1 - x2))
        dy = min(abs(y1 - y2), GRID_SIZE - abs(y1 - y2))
        return (dx ** 2 + dy ** 2) ** 0.5

    def get_nearby_agents(self, agent_id: AgentId) -> list[AgentId]:
        """Get all agents within INTERACTION_RADIUS of this agent.

        Scans all cells within the interaction radius and checks exact
        toroidal distance for each potential neighbor.

        Args:
            agent_id: The agent to find neighbors for.

        Returns:
            List of agent IDs within interaction radius (excludes self).
        """
        if agent_id not in self._positions:
            return []
        x, y = self.get_position(agent_id)
        nearby: list[AgentId] = []
        x_int = int(x)
        y_int = int(y)
        for dx in range(-INTERACTION_RADIUS, INTERACTION_RADIUS + 1):
            for dy in range(-INTERACTION_RADIUS, INTERACTION_RADIUS + 1):
                nx = (x_int + dx) % GRID_SIZE
                ny = (y_int + dy) % GRID_SIZE
                key = (nx, ny)
                if key in self._reverse:
                    for other_id in self._reverse[key]:
                        if other_id != agent_id:
                            ox, oy = self.get_position(other_id)
                            if self.toroidal_distance(x_int, y_int, ox, oy) <= INTERACTION_RADIUS:
                                nearby.append(other_id)
        return nearby

    def get_agents_at(self, x: int, y: int) -> list[AgentId]:
        """Get all agents at a specific grid position.

        Args:
            x: X coordinate (wrapped to grid bounds).
            y: Y coordinate (wrapped to grid bounds).

        Returns:
            List of agent IDs at that position (may be empty).
        """
        key = (x % GRID_SIZE, y % GRID_SIZE)
        return list(self._reverse.get(key, []))

    def remove_agent(self, agent_id: AgentId) -> None:
        """Remove an agent from the grid (e.g., on death).

        Args:
            agent_id: The agent to remove.
        """
        if agent_id in self._positions:
            x, y = self._positions[agent_id]
            key = (int(x), int(y))
            if key in self._reverse and agent_id in self._reverse[key]:
                self._reverse[key].remove(agent_id)
                if not self._reverse[key]:
                    del self._reverse[key]
            del self._positions[agent_id]

    def get_all_positions(self) -> dict[AgentId, tuple[int, int]]:
        """Get all current agent positions.

        Returns:
            Dict mapping agent IDs to (x, y) positions.
        """
        return {aid: (int(x), int(y)) for aid, (x, y) in self._positions.items()}

    def __len__(self) -> int:
        return len(self._positions)
