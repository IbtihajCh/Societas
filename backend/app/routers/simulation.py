from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from shared.dto.simulation_dto import (
    SimulationStartRequestDTO,
    SimulationStateResponseDTO,
    SimulationStatusDTO,
)

from backend.app.dependencies import get_simulation_service
from backend.app.services.simulation_service import SimulationService

router = APIRouter()


@router.get("/status", response_model=SimulationStatusDTO)
async def get_simulation_status(
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.get_status()


@router.post("/start")
async def start_simulation(
    request: SimulationStartRequestDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    status = await service.start_simulation(request)
    return {"simulation_id": "sim-001", "status": "started", "tick": status.tick}


@router.post("/stop")
async def stop_simulation(
    service: SimulationService = Depends(get_simulation_service),
):
    status = await service.stop_simulation()
    return {"status": "stopped", "tick": status.tick}


@router.post("/tick")
async def advance_tick(
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        state = await service.advance_tick()
        return {"tick": state.tick, "status": "completed"}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/state", response_model=SimulationStateResponseDTO)
async def get_simulation_state(
    service: SimulationService = Depends(get_simulation_service),
):
    return await service.get_state()


@router.post("/reset")
async def reset_simulation(
    seed: Optional[int] = None,
    service: SimulationService = Depends(get_simulation_service),
):
    status = await service.reset_simulation(seed)
    return {"status": "reset", "tick": status.tick}
