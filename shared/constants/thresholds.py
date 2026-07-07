"""
Threshold Constants
===================

Threshold values for simulation parameters.
"""

AMBIGUITY_THRESHOLD_MIN: float = 0.01
"""Minimum ambiguity threshold."""

AMBIGUITY_THRESHOLD_MAX: float = 0.20
"""Maximum ambiguity threshold."""

CONFIDENCE_THRESHOLD_LOW: float = 0.3
"""Low confidence threshold - may need review."""

CONFIDENCE_THRESHOLD_MEDIUM: float = 0.6
"""Medium confidence threshold."""

CONFIDENCE_THRESHOLD_HIGH: float = 0.85
"""High confidence threshold - reliable decision."""

NEED_CRITICAL_THRESHOLD: float = 0.8
"""Need level above which a need is considered critical."""

NEED_SATISFIED_THRESHOLD: float = 0.2
"""Need level below which a need is considered satisfied."""

EMOTION_INTENSITY_LOW: float = 0.2
"""Low emotion intensity threshold."""

EMOTION_INTENSITY_HIGH: float = 0.7
"""High emotion intensity threshold."""

WEALTH_POOR_THRESHOLD: float = 50.0
"""Wealth below which an agent is classified as poor."""

WEALTH_WEALTHY_THRESHOLD: float = 500.0
"""Wealth above which an agent is classified as wealthy."""

CRIME_RATE_HIGH_THRESHOLD: float = 0.15
"""Crime rate above which public safety is considered at risk."""

UNLUST_HIGH_THRESHOLD: float = 0.7
"""Unlust level above which societal dissatisfaction is high."""

POPULATION_GROWTH_RATE_MAX: float = 0.05
"""Maximum population growth rate per tick."""

INFLATION_RATE_TARGET: float = 0.02
"""Target inflation rate."""

UNEMPLOYMENT_RATE_NATURAL: float = 0.05
"""Natural rate of unemployment."""
