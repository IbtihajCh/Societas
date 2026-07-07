"""
Shared Types Module
===================

Provides type definitions, enumerations, and aliases for SOCIETAS.
"""

from shared.types.enums import (
    ActionType,
    NeedType,
    EmotionType,
    WealthClass,
    PolicyCategory,
    CrimeType,
    EmploymentStatus,
)
from shared.types.aliases import (
    AgentId,
    TickNumber,
    PolicyId,
    EventId,
    NeedValue,
    UtilityScore,
    ConfidenceScore,
    PopulationCount,
    Percentage,
)

__all__ = [
    "ActionType",
    "NeedType",
    "EmotionType",
    "WealthClass",
    "PolicyCategory",
    "CrimeType",
    "EmploymentStatus",
    "AgentId",
    "TickNumber",
    "PolicyId",
    "EventId",
    "NeedValue",
    "UtilityScore",
    "ConfidenceScore",
    "PopulationCount",
    "Percentage",
]
