"""
Policy DTO
==========

Data Transfer Objects for policy-related API communication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.types.aliases import PolicyId
from shared.types.enums import CrisisType, PolicyCategory, PolicyPreset


@dataclass
class PolicyCreateRequestDTO:
    """
    DTO for policy creation request.
    
    Attributes:
        name: Policy name
        description: Policy description
        category: Policy category
        weights: Policy weight modifiers
        policy_text: Natural language policy text for LLM translation
    """
    
    name: str = ""
    description: str = ""
    category: PolicyCategory = PolicyCategory.ECONOMIC
    weights: Dict[str, float] = field(default_factory=dict)
    policy_text: Optional[str] = None


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
        impact_deltas: Impact deltas per wealth class (maps wealth class name
            to dict of ImpactDelta fields)
    """
    
    id: PolicyId
    name: str = ""
    description: str = ""
    category: PolicyCategory = PolicyCategory.ECONOMIC
    weights: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True
    enactment_tick: int = 0
    impact_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)


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


@dataclass
class CrisisInjectRequestDTO:
    crisis_type: CrisisType = CrisisType.NATURAL_DISASTER


@dataclass
class CrisisResultDTO:
    crisis_type: str
    description: str
    changes: Dict[str, float]


@dataclass
class PresetApplyRequestDTO:
    preset_name: PolicyPreset = PolicyPreset.UNIVERSAL_BASIC_INCOME


@dataclass
class PresetResultDTO:
    preset_name: str
    description: str
    policy_id: str
    changes: Dict[str, object]
