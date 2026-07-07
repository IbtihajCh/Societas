from fastapi import APIRouter, Depends
from typing import Optional

from shared.dto.metrics_dto import MetricsResponseDTO

from backend.app.dependencies import get_metrics_service
from backend.app.services.metrics_service import MetricsService

router = APIRouter()


@router.get("/", response_model=MetricsResponseDTO)
async def get_metrics(
    tick_from: Optional[int] = 0,
    tick_to: Optional[int] = 0,
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.get_metrics(tick_from or 0, tick_to or 0)


@router.get("/dashboard")
async def get_dashboard_data(
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.get_dashboard_data()
