from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from shared.dto.simulation_dto import (
    SimulationStartRequestDTO,
    SimulationStateResponseDTO,
    SimulationStatusDTO,
)

from backend.app.dependencies import get_simulation_service, set_engine
from backend.app.services.simulation_service import SimulationService

router = APIRouter()


@router.get("/status", response_model=SimulationStatusDTO)
async def get_simulation_status(
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.get_status()


@router.post("/start", response_model=SimulationStatusDTO)
async def start_simulation(
    request: SimulationStartRequestDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    status = await service.start_simulation(request)
    engine = service.get_engine()
    if engine is not None:
        set_engine(engine)
    return status


@router.post("/stop", response_model=SimulationStatusDTO)
async def stop_simulation(
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.stop_simulation()


@router.post("/tick", response_model=SimulationStateResponseDTO)
async def advance_tick(
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        return await service.advance_tick()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/state", response_model=SimulationStateResponseDTO)
async def get_simulation_state(
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.get_state()


@router.post("/reset", response_model=SimulationStatusDTO)
async def reset_simulation(
    seed: Optional[int] = None,
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.reset_simulation(seed)
