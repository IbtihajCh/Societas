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
    ],
}

# === WEALTH CLASS CONFIG ===
WEALTH_CLASS_MONEY_RANGES: dict[WealthClass, tuple[float, float]] = {
    WealthClass.POOR: (100.0, 800.0),
    WealthClass.MIDDLE: (2000.0, 8000.0),
    WealthClass.RICH: (15000.0, 80000.0),
}

WEALTH_CLASS_DISTRIBUTION: dict[WealthClass, Percentage] = {
    WealthClass.POOR: Percentage(50.0),
    WealthClass.MIDDLE: Percentage(35.0),
    WealthClass.RICH: Percentage(15.0),
}

WEALTH_CLASS_THRESHOLDS: dict[WealthClass, tuple[float, float]] = {
    WealthClass.POOR: (0.0, 1000.0),
    WealthClass.MIDDLE: (1000.0, 15000.0),
    WealthClass.RICH: (15000.0, float("inf")),
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
}

# Property ownership probability by wealth class
PROPERTY_OWNERSHIP: dict[WealthClass, float] = {
    WealthClass.POOR: 0.10,
    WealthClass.MIDDLE: 0.60,
    WealthClass.RICH: 0.90,
}

# Rent cost per tick by wealth class
RENT_COST: dict[WealthClass, float] = {
    WealthClass.POOR: 5.0,
    WealthClass.MIDDLE: 25.0,
    WealthClass.RICH: 80.0,
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
