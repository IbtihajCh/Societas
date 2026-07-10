"""
Simulation-Specific Constants
=============================

Salary ranges, wealth class configuration, job configs, and Beta distribution
parameters for the SOCIETAS simulation. Aligned with Project Guide v1.0.
"""

from shared.types.aliases import Percentage
from shared.types.enums import EducationLevel, JobType, WealthClass

# === SALARY RANGES (annual, in pounds) ===
SALARY_RANGES: dict[JobType, tuple[float, float]] = {
    JobType.ENGINEER: (80000.0, 130000.0),
    JobType.COMPUTER_SCIENTIST: (90000.0, 130000.0),
    JobType.PILOT: (80000.0, 120000.0),
    JobType.DOCTOR: (80000.0, 130000.0),
    JobType.THERAPIST: (40000.0, 70000.0),
    JobType.MECHANIC: (30000.0, 50000.0),
    JobType.ELECTRICIAN: (35000.0, 55000.0),
    JobType.CONSTRUCTION_PLANNER: (40000.0, 60000.0),
    JobType.CONSTRUCTION_WORKER: (25000.0, 40000.0),
    JobType.CLEANER: (18000.0, 30000.0),
    JobType.TAXI_DRIVER: (20000.0, 35000.0),
    JobType.ARTIST: (25000.0, 65000.0),
    JobType.WRITER: (30000.0, 80000.0),
    JobType.MUSICIAN: (20000.0, 60000.0),
    JobType.COMMUNITY_LEADER: (40000.0, 100000.0),
    JobType.UNEMPLOYED: (0.0, 0.0),
}

# === JOB CATEGORIES ===
TECHNICAL_JOBS: list[JobType] = [JobType.ENGINEER, JobType.COMPUTER_SCIENTIST]
MID_TIER_JOBS: list[JobType] = [
    JobType.PILOT,
    JobType.DOCTOR,
    JobType.THERAPIST,
    JobType.MECHANIC,
    JobType.ELECTRICIAN,
    JobType.CONSTRUCTION_PLANNER,
]
MANUAL_JOBS: list[JobType] = [
    JobType.CONSTRUCTION_WORKER,
    JobType.CLEANER,
    JobType.TAXI_DRIVER,
]

JOB_CATEGORY_DISTRIBUTION: dict[str, Percentage] = {
    "technical": Percentage(15.0),
    "mid_tier": Percentage(35.0),
    "manual": Percentage(50.0),
}

# Education requirements per job
JOB_EDUCATION_REQUIREMENTS: dict[JobType, EducationLevel] = {
    JobType.ENGINEER: EducationLevel.HIGHER,
    JobType.COMPUTER_SCIENTIST: EducationLevel.HIGHER,
    JobType.PILOT: EducationLevel.SECONDARY,
    JobType.DOCTOR: EducationLevel.HIGHER,
    JobType.THERAPIST: EducationLevel.HIGHER,
    JobType.MECHANIC: EducationLevel.SECONDARY,
    JobType.ELECTRICIAN: EducationLevel.SECONDARY,
    JobType.CONSTRUCTION_PLANNER: EducationLevel.SECONDARY,
    JobType.CONSTRUCTION_WORKER: EducationLevel.PRIMARY,
    JobType.CLEANER: EducationLevel.PRIMARY,
    JobType.TAXI_DRIVER: EducationLevel.PRIMARY,
    JobType.UNEMPLOYED: EducationLevel.NONE,
}

# Jobs available per education level
JOBS_BY_EDUCATION: dict[EducationLevel, list[JobType]] = {
    EducationLevel.NONE: [JobType.UNEMPLOYED],
    EducationLevel.PRIMARY: [
        JobType.CONSTRUCTION_WORKER,
        JobType.CLEANER,
        JobType.TAXI_DRIVER,
    ],
    EducationLevel.SECONDARY: [
        JobType.PILOT,
        JobType.MECHANIC,
        JobType.ELECTRICIAN,
        JobType.CONSTRUCTION_PLANNER,
        JobType.CONSTRUCTION_WORKER,
        JobType.CLEANER,
        JobType.TAXI_DRIVER,
        JobType.ARTIST,
        JobType.WRITER,
        JobType.MUSICIAN,
    ],
    EducationLevel.HIGHER: [
        JobType.ENGINEER,
        JobType.COMPUTER_SCIENTIST,
        JobType.PILOT,
        JobType.DOCTOR,
        JobType.THERAPIST,
        JobType.MECHANIC,
        JobType.ELECTRICIAN,
        JobType.CONSTRUCTION_PLANNER,
        JobType.CONSTRUCTION_WORKER,
        JobType.CLEANER,
        JobType.TAXI_DRIVER,
        JobType.ARTIST,
        JobType.WRITER,
        JobType.MUSICIAN,
    ],
}

# === WEALTH CLASS CONFIG ===
WEALTH_CLASS_MONEY_RANGES: dict[WealthClass, tuple[float, float]] = {
    WealthClass.POOR: (100.0, 800.0),
    WealthClass.MIDDLE: (2000.0, 8000.0),
    WealthClass.RICH: (15000.0, 80000.0),
    WealthClass.BUSINESS_OWNER: (80000.0, 200000.0),
}

WEALTH_CLASS_DISTRIBUTION: dict[WealthClass, Percentage] = {
    WealthClass.POOR: Percentage(50.0),
    WealthClass.MIDDLE: Percentage(35.0),
    WealthClass.RICH: Percentage(15.0),
    WealthClass.BUSINESS_OWNER: Percentage(0.0),
}

WEALTH_CLASS_THRESHOLDS: dict[WealthClass, tuple[float, float]] = {
    WealthClass.POOR: (0.0, 1000.0),
    WealthClass.MIDDLE: (1000.0, 15000.0),
    WealthClass.RICH: (15000.0, 80000.0),
    WealthClass.BUSINESS_OWNER: (80000.0, float("inf")),
}

# Education probability by wealth class
EDUCATION_BY_WEALTH: dict[WealthClass, dict[EducationLevel, float]] = {
    WealthClass.POOR: {
        EducationLevel.PRIMARY: 0.70,
        EducationLevel.SECONDARY: 0.27,
        EducationLevel.HIGHER: 0.03,
    },
    WealthClass.MIDDLE: {
        EducationLevel.PRIMARY: 0.20,
        EducationLevel.SECONDARY: 0.60,
        EducationLevel.HIGHER: 0.20,
    },
    WealthClass.RICH: {
        EducationLevel.PRIMARY: 0.05,
        EducationLevel.SECONDARY: 0.35,
        EducationLevel.HIGHER: 0.60,
    },
    WealthClass.BUSINESS_OWNER: {
        EducationLevel.PRIMARY: 0.02,
        EducationLevel.SECONDARY: 0.18,
        EducationLevel.HIGHER: 0.80,
    },
}

# Property ownership probability by wealth class
PROPERTY_OWNERSHIP: dict[WealthClass, float] = {
    WealthClass.POOR: 0.10,
    WealthClass.MIDDLE: 0.60,
    WealthClass.RICH: 0.90,
    WealthClass.BUSINESS_OWNER: 0.98,
}

# Rent cost per tick by wealth class
RENT_COST: dict[WealthClass, float] = {
    WealthClass.POOR: 5.0,
    WealthClass.MIDDLE: 25.0,
    WealthClass.RICH: 80.0,
    WealthClass.BUSINESS_OWNER: 120.0,
}

# === BETA DISTRIBUTION PARAMETERS ===
BETA_PARAMS: dict[str, tuple[float, float]] = {
    "creativity": (2.0, 2.0),
    "morality": (2.0, 2.0),
    "anger_tendency": (2.0, 3.0),
    "extraversion": (2.0, 2.0),
    "ambition": (2.0, 2.0),
    "resilience": (2.0, 2.0),
    "dominance_urge": (2.0, 2.0),
    "risk_tolerance": (2.0, 2.0),
}

# === DOCTOR / THERAPIST JOB EFFECTS ===
DOCTOR_SALARY: float = 120.0
THERAPIST_SALARY: float = 85.0
DOCTOR_EDUCATION_REQUIRED: EducationLevel = EducationLevel.HIGHER
THERAPIST_EDUCATION_REQUIRED: EducationLevel = EducationLevel.SECONDARY
THERAPIST_MIN_EXTRAVERSION: float = 0.4
HEAL_EFFECTIVENESS: float = 0.15
THERAPY_HAPPINESS_BOOST: float = 0.08
MAX_PATIENTS_PER_DOCTOR: int = 5
MAX_CLIENTS_PER_THERAPIST: int = 8

# === CREATIVE PROFESSION SALARIES (annual, in pounds) ===
ARTIST_SALARY: float = 45.0
WRITER_SALARY: float = 55.0
MUSICIAN_SALARY: float = 40.0
COMMUNITY_LEADER_SALARY: float = 70.0

# === CREATIVE / LEADERSHIP THRESHOLDS ===
CREATIVE_MIN_CREATIVITY: float = 0.7
LEADER_MIN_REPUTATION: float = 0.6
LEADER_MIN_MORALITY: float = 0.5
LEADER_ELECTION_INTERVAL: int = 50
