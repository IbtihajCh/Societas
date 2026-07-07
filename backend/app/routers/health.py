from fastapi import APIRouter, Depends

from backend.app.dependencies import get_engine

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "societas-backend"}


@router.get("/ready")
async def readiness_check(engine=Depends(get_engine)):
    is_ready = engine is not None
    return {"status": "ready" if is_ready else "not_ready", "simulation": bool(is_ready)}
