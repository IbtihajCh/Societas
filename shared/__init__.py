"""
SOCIETAS Shared Module
======================

This module contains all shared types, schemas, interfaces, and utilities
used across the SOCIETAS simulation platform.

All subsystems (simulation, backend, frontend, AI) import from this module
to ensure consistency and avoid duplication.

Modules:
    - schemas: Data schemas for agents, simulation state, policies, etc.
    - dto: Data Transfer Objects for API communication
    - events: Event definitions for the event bus system
    - types: Type definitions, enums, and aliases
    - constants: Configuration constants and thresholds
    - interfaces: Abstract interfaces for subsystem contracts
    - utilities: Shared utility functions
"""

from shared.types.enums import ActionType, NeedType, EmotionType, WealthClass
from shared.types.aliases import AgentId, TickNumber, PolicyId, EventId

__version__ = "0.1.0"
__all__ = [
    "ActionType",
    "NeedType",
    "EmotionType",
    "WealthClass",
    "AgentId",
    "TickNumber",
    "PolicyId",
    "EventId",
]
