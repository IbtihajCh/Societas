"""
Economy State Schema
====================

Defines the economic state for the SOCIETAS simulation.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EconomyState:
    """
    Economic state of the simulated world.
    
    Tracks macroeconomic indicators and economic health metrics.
    
    Attributes:
        gdp: Gross Domestic Product (monetary units)
        unemployment_rate: Unemployment rate (0.0 to 1.0)
        inflation_rate: Inflation rate (0.0 to 1.0)
        wealth_distribution: Distribution of wealth across classes
        employment_rate: Employment rate (0.0 to 1.0)
        consumer_confidence: Consumer confidence index (0.0 to 1.0)
        market_stability: Market stability index (0.0 to 1.0)
        tax_revenue: Government tax revenue
        government_spending: Government expenditure
        trade_balance: Trade balance (exports - imports)
    """
    
    gdp: float = 0.0
    unemployment_rate: float = 0.1
    inflation_rate: float = 0.02
    wealth_distribution: Dict[str, float] = field(default_factory=dict)
    employment_rate: float = 0.9
    consumer_confidence: float = 0.5
    market_stability: float = 0.5
    tax_revenue: float = 0.0
    government_spending: float = 0.0
    trade_balance: float = 0.0
