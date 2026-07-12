"""
Enumeration Types for SOCIETAS
================================

Defines all enumeration types used throughout the simulation.
Aligned with the Project Guide v1.0 and ADR-005.
"""

import sys
from enum import Enum, IntEnum, auto

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        """Backport of Python 3.11's StrEnum for compatibility."""


class ActionType(StrEnum):
    """Actions available to agents (15 values per Project Guide)."""

    WORK = "work"
    BUY_FOOD = "buy_food"
    REST = "rest"
    SEEK_JOB = "seek_job"
    BEG = "beg"
    BEFRIEND = "befriend"
    CONSOLE = "console"
    ISOLATE = "isolate"
    SHARE = "share"
    STEAL = "steal"
    HARM_OTHER = "harm_other"
    FRAUD = "fraud"
    TREAT = "treat"
    PROTEST = "protest"
    COUNSEL = "counsel"
    COMPLAIN = "complain"
    CAMPAIGN = "campaign"
    COMPLY = "comply"
    SPREAD_RUMOR = "spread_rumor"
    SUPPORT_FAMILY = "support_family"
    INVEST = "invest"
    BUY_PROPERTY = "buy_property"
    HOBBY = "hobby"
    IDLE = "idle"


class NeedType(StrEnum):
    """Maslow hierarchy of needs — 13 needs across 5 layers."""

    # Layer 1: Physiological
    FOOD = "food"
    WATER = "water"
    SLEEP = "sleep"
    SEXUAL_TENSION = "sexual_tension"
    # Layer 2: Safety
    SAFETY = "safety"
    FINANCIAL_SECURITY = "financial_security"
    SHELTER = "shelter"
    # Layer 3: Love/Belonging
    SOCIAL_CONNECTION = "social_connection"
    FAMILY_BOND = "family_bond"
    ROMANTIC_BOND = "romantic_bond"
    # Layer 4: Esteem
    SELF_ESTEEM = "self_esteem"
    REPUTATION = "reputation"
    INFERIORITY_GAP = "inferiority_gap"


class EmotionType(StrEnum):
    """Five emotional states with timers per Project Guide."""

    HAPPY = "happy"
    NORMAL = "normal"
    SAD = "sad"
    ANGRY = "angry"
    DESPAIR = "despair"


class WealthClass(StrEnum):
    """Wealth classes per Project Guide."""

    POOR = "poor"
    MIDDLE = "middle"
    RICH = "rich"


class Gender(StrEnum):
    """Agent gender identity."""

    MALE = "male"
    FEMALE = "female"


class Culture(StrEnum):
    """Agent cultural background (A, B, or C)."""

    A = "A"
    B = "B"
    C = "C"


class EducationLevel(IntEnum):
    """Education level achieved by an agent."""

    NONE = 0
    PRIMARY = 1
    SECONDARY = 2
    HIGHER = 3


class JobType(StrEnum):
    """Job types available in the economy (11 jobs + unemployed)."""

    ENGINEER = "engineer"
    COMPUTER_SCIENTIST = "computer_scientist"
    PILOT = "pilot"
    DOCTOR = "doctor"
    THERAPIST = "therapist"
    MECHANIC = "mechanic"
    ELECTRICIAN = "electrician"
    CONSTRUCTION_PLANNER = "construction_planner"
    CONSTRUCTION_WORKER = "construction_worker"
    CLEANER = "cleaner"
    TAXI_DRIVER = "taxi_driver"
    ARTIST = "artist"
    WRITER = "writer"
    MUSICIAN = "musician"
    COMMUNITY_LEADER = "community_leader"
    UNEMPLOYED = "unemployed"


class PolicyCategory(StrEnum):
    """Categories of government policies."""

    ECONOMIC = "economic"
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    PUBLIC_ORDER = "public_order"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    INFRASTRUCTURE = "infrastructure"
    CULTURAL = "cultural"


class CrisisType(StrEnum):
    """Predefined crisis types for demo injection."""

    NATURAL_DISASTER = "natural_disaster"
    ECONOMIC_CRASH = "economic_crash"
    CRIME_WAVE = "crime_wave"
    PLAGUE = "plague"


class PolicyPreset(StrEnum):
    """Predefined policy presets for quick application."""

    UNIVERSAL_BASIC_INCOME = "universal_basic_income"
    POLICE_STATE = "police_state"
    MARKET_DEREGULATION = "market_deregulation"


class CrimeType(Enum):
    """Types of crimes that can occur."""

    THEFT = auto()
    VIOLENCE = auto()
    FRAUD = auto()
    VANDALISM = auto()
    DRUG_OFFENSE = auto()
    TAX_EVASION = auto()
    CORRUPTION = auto()


class EmploymentStatus(StrEnum):
    """Employment status of agents."""

    UNEMPLOYED = "unemployed"
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    STUDENT = "student"
    RETIRED = "retired"
