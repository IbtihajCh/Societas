"""
Health Check Router
===================

Health and readiness endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "societas-backend"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns:
        Readiness status
        
    TODO: Check dependencies (simulation, AI router)
    """
    # TODO: Check if simulation and AI router are available
    return {"status": "ready"}
