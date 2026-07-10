import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from shared.schemas.save_state import SimulationSaveMetadata
from backend.app.dependencies import get_simulation_service
from backend.app.services.simulation_service import SimulationService
from simulation.engine.save_load_manager import (
    list_saves as _list_saves,
    delete_save as _delete_save,
)

router = APIRouter()

SAVE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "saves",
)
os.makedirs(SAVE_DIR, exist_ok=True)


class SaveCreateRequest(BaseModel):
    filepath: str


class SaveCreateResponse(BaseModel):
    save_id: str
    filepath: str


class SaveLoadRequest(BaseModel):
    filepath: str


@router.get("/", response_model=List[SimulationSaveMetadata])
async def list_all_saves():
    return _list_saves(SAVE_DIR)


@router.post("/", response_model=SaveCreateResponse)
async def create_save(
    request: SaveCreateRequest,
    service: SimulationService = Depends(get_simulation_service),
):
    engine = service.get_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="No active simulation")
    if not engine.is_running():
        raise HTTPException(status_code=400, detail="Simulation is not running")

    filepath = request.filepath
    if not os.path.isabs(filepath):
        filepath = os.path.join(SAVE_DIR, filepath)

    save_id = engine.save(filepath)
    return SaveCreateResponse(save_id=save_id, filepath=filepath)


@router.post("/load", response_model=dict)
async def load_save(
    request: SaveLoadRequest,
    service: SimulationService = Depends(get_simulation_service),
):
    engine = service.get_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="No active simulation")

    filepath = request.filepath
    if not os.path.isabs(filepath):
        filepath = os.path.join(SAVE_DIR, filepath)

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Save file not found")

    engine.load(filepath)
    return {"status": "loaded", "filepath": filepath}


@router.delete("/{save_id}", response_model=dict)
async def delete_save(save_id: str):
    success = _delete_save(save_id, SAVE_DIR)
    if not success:
        raise HTTPException(status_code=404, detail="Save not found")
    return {"status": "deleted", "save_id": save_id}
