"""
Policy DTO
==========

Data Transfer Objects for policy-related API communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import PolicyId
from shared.types.enums import PolicyCategory


@dataclass
class PolicyCreateRequestDTO:
    """
    DTO for policy creation request.
    
    Attributes:
        name: Policy name
        description: Policy description
        category: Policy category
        weights: Policy weight modifiers
    """
    
    name: str = ""
    description: str = ""
    category: PolicyCategory = PolicyCategory.ECONOMIC
    weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class PolicyResponseDTO:
    """
    DTO for policy response.
    
    Attributes:
        id: Policy identifier
        name: Policy name
        description: Policy description
        category: Policy category
        weights: Policy weight modifiers
        is_active: Whether policy is active
        enactment_tick: Tick when enacted
    """
    
    id: PolicyId
    name: str = ""
    description: str = ""
    category: PolicyCategory = PolicyCategory.ECONOMIC
    weights: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True
    enactment_tick: int = 0


@dataclass
class PolicyListResponseDTO:
    """
    DTO for policy list response.
    
    Attributes:
        policies: List of policy responses
        total: Total number of policies
    """
    
    policies: List[PolicyResponseDTO] = field(default_factory=list)
    total: int = 0
