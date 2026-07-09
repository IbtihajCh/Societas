"""
Type Aliases for SOCIETAS
==========================

Provides type aliases for improved code readability and consistency.
"""

from typing import NewType

AgentId = NewType("AgentId", str)
"""Unique identifier for an agent."""

TickNumber = NewType("TickNumber", int)
"""Simulation tick number (monotonically increasing)."""

PolicyId = NewType("PolicyId", str)
"""Unique identifier for a policy."""

EventId = NewType("EventId", str)
"""Unique identifier for an event."""

NeedValue = NewType("NeedValue", float)
"""Value representing a need level (0.0 to 1.0)."""

UtilityScore = NewType("UtilityScore", float)
"""Utility score for decision making (-1.0 to 1.0)."""

ConfidenceScore = NewType("ConfidenceScore", float)
"""Confidence score for AI outputs (0.0 to 1.0)."""

PopulationCount = NewType("PopulationCount", int)
"""Count of population members."""

Percentage = NewType("Percentage", float)
"""Percentage value (0.0 to 100.0)."""

GridCoordinate = NewType("GridCoordinate", int)
"""Grid coordinate (0 to GRID_SIZE-1)."""

GridCoordinate = NewType("GridCoordinate", int)
"""Grid coordinate value (0 to GRID_SIZE-1) for the toroidal grid."""
