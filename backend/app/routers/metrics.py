"""
Metrics Router
==============

Metrics and dashboard data endpoints.
"""

from fastapi import APIRouter
from typing import Optional

from shared.dto.metrics_dto import MetricsResponseDTO

router = APIRouter()


@router.get("/", response_model=MetricsResponseDTO)
async def get_metrics(tick_from: Optional[int] = None, tick_to: Optional[int] = None):
    """
    Get simulation metrics.
    
    Args:
        tick_from: Start tick (optional)
        tick_to: End tick (optional)
        
    Returns:
        MetricsResponseDTO
        
    TODO: Implement metrics retrieval
    """
    # TODO: Get metrics from simulation engine
    return MetricsResponseDTO()


@router.get("/dashboard")
async def get_dashboard_data():
    """
    Get dashboard summary data.
    
    Returns:
        Dashboard summary
        
    TODO: Implement dashboard data aggregation
    """
    # TODO: Aggregate data for dashboard
    return {"status": "ok"}
