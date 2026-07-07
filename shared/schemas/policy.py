"""
Policy Schema
=============

Defines policy and government policy schemas for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from shared.types.aliases import PolicyId
from shared.types.enums import PolicyCategory


@dataclass
class PolicyWeights:
    """
    Utility weight modifiers applied by a policy.
    
    These weights modify agent decision-making by adjusting
    the utility scores for different dimensions.
    
    Attributes:
        economic_freedom: Effect on economic freedom (-1.0 to 1.0)
        social_welfare: Effect on social welfare (-1.0 to 1.0)
        environmental_protection: Effect on environmental protection (-1.0 to 1.0)
        public_order: Effect on public order (-1.0 to 1.0)
        innovation: Effect on innovation (-1.0 to 1.0)
        cultural_preservation: Effect on cultural preservation (-1.0 to 1.0)
    """
    
    economic_freedom: float = 0.0
    social_welfare: float = 0.0
    environmental_protection: float = 0.0
    public_order: float = 0.0
    innovation: float = 0.0
    cultural_preservation: float = 0.0


@dataclass
class Policy:
    """
    A government policy definition.
    
    Represents a configurable policy that affects the simulation.
    Policies modify agent behavior through utility weight adjustments.
    
    Attributes:
        id: Unique policy identifier
        name: Human-readable policy name
        description: Detailed policy description
        category: Policy category classification
        weights: Utility weight modifiers
        is_active: Whether the policy is currently active
        enactment_tick: Tick when the policy was enacted
        metadata: Additional policy metadata
    """
    
    id: PolicyId
    name: str = ""
    description: str = ""
    category: PolicyCategory = PolicyCategory.ECONOMIC
    weights: PolicyWeights = field(default_factory=PolicyWeights)
    is_active: bool = True
    enactment_tick: int = 0
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class GovernmentPolicy:
    """
    An active government policy with runtime state.
    
    Extends the base Policy with runtime state tracking
    and effect application status.
    
    Attributes:
        policy: The underlying policy definition
        applied_effects: Dictionary of applied effects
        affected_agents: Number of agents affected
        total_cost: Total cost of policy implementation
        effectiveness: Measured effectiveness (0.0 to 1.0)
    """
    
    policy: Policy = field(default_factory=lambda: Policy(id=PolicyId("")))
    applied_effects: Dict[str, float] = field(default_factory=dict)
    affected_agents: int = 0
    total_cost: float = 0.0
    effectiveness: float = 0.0
