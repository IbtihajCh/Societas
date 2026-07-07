"""
Enumeration Types for SOCIETAS
================================

Defines all enumeration types used throughout the simulation.
"""

from enum import Enum, auto


class ActionType(Enum):
    """Possible actions an agent can take."""
    
    WORK = auto()
    """Agent chooses to work/seek employment."""
    
    LEISURE = auto()
    """Agent chooses leisure activities."""
    
    SOCIALIZE = auto()
    """Agent chooses to socialize with others."""
    
    CONSUME = auto()
    """Agent chooses to consume goods/services."""
    
    SAVE = auto()
    """Agent chooses to save money."""
    
    INVEST = auto()
    """Agent chooses to invest resources."""
    
    EDUCATE = auto()
    """Agent chooses to pursue education."""
    
    REST = auto()
    """Agent chooses to rest/recover."""
    
    MIGRATE = auto()
    """Agent chooses to migrate to another area."""
    
    PROTEST = auto()
    """Agent chooses to protest policies."""
    
    COMMIT_CRIME = auto()
    """Agent chooses to commit a crime."""
    
    VOLUNTEER = auto()
    """Agent chooses to volunteer/help others."""
    
    IDLE = auto()
    """Agent has no clear action."""


class NeedType(Enum):
    """Types of needs that agents experience."""
    
    FOOD = auto()
    """Need for food/nutrition."""
    
    SHELTER = auto()
    """Need for shelter/housing."""
    
    SAFETY = auto()
    """Need for safety/security."""
    
    SOCIAL = auto()
    """Need for social connection."""
    ESTEEM = auto()
    """Need for esteem/recognition."""
    
    SELF_ACTUALIZATION = auto()
    """Need for self-actualization."""
    
    HEALTH = auto()
    """Need for health/medical care."""
    
    EDUCATION = auto()
    """Need for education/learning."""
    
    ENTERTAINMENT = auto()
    """Need for entertainment/recreation."""


class EmotionType(Enum):
    """Emotional states that agents can experience."""
    
    HAPPY = auto()
    """Positive emotional state."""
    
    SAD = auto()
    """Negative emotional state - sadness."""
    
    ANGRY = auto()
    """Negative emotional state - anger."""
    
    FEARFUL = auto()
    """Negative emotional state - fear."""
    
    SURPRISED = auto()
    """Neutral emotional state - surprise."""
    
    DISGUSTED = auto()
    """Negative emotional state - disgust."""
    
    CONTENT = auto()
    """Positive emotional state - contentment."""
    
    ANXIOUS = auto()
    """Negative emotional state - anxiety."""
    
    HOPEFUL = auto()
    """Positive emotional state - hope."""
    
    DESPAIRING = auto()
    """Negative emotional state - despair."""


class WealthClass(Enum):
    """Wealth classification for agents."""
    
    POOR = auto()
    """Low wealth, struggling financially."""
    
    WORKING = auto()
    """Moderate wealth, working class."""
    
    MIDDLE = auto()
    """Average wealth, middle class."""
    
    UPPER_MIDDLE = auto()
    """Above average wealth."""
    
    WEALTHY = auto()
    """High wealth."""
    
    ELITE = auto()
    """Very high wealth, top tier."""


class PolicyCategory(Enum):
    """Categories of government policies."""
    
    ECONOMIC = auto()
    """Economic/fiscal policies."""
    
    SOCIAL = auto()
    """Social welfare policies."""
    
    ENVIRONMENTAL = auto()
    """Environmental protection policies."""
    
    PUBLIC_ORDER = auto()
    """Law enforcement/public order policies."""
    
    EDUCATION = auto()
    """Education policies."""
    
    HEALTHCARE = auto()
    """Healthcare policies."""
    
    INFRASTRUCTURE = auto()
    """Infrastructure development policies."""
    
    CULTURAL = auto()
    """Cultural preservation policies."""


class CrimeType(Enum):
    """Types of crimes that can occur."""
    
    THEFT = auto()
    """Property theft."""
    
    VIOLENCE = auto()
    """Violent crime."""
    
    FRAUD = auto()
    """Financial fraud."""
    
    VANDALISM = auto()
    """Property damage."""
    
    DRUG_OFFENSE = auto()
    """Drug-related crime."""
    
    TAX_EVASION = auto()
    """Tax evasion."""
    
    CORRUPTION = auto()
    """Corruption/bribery."""


class EmploymentStatus(Enum):
    """Employment status of agents."""
    
    EMPLOYED = auto()
    """Currently employed."""
    
    UNEMPLOYED = auto()
    """Currently unemployed, seeking work."""
    
    STUDENT = auto()
    """Currently in education."""
    
    RETIRED = auto()
    """Retired from work."""
    
    UNABLE_TO_WORK = auto()
    """Unable to work (disability/illness)."""
