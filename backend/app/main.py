"""
FastAPI Application
===================

Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import simulation, policies, metrics, agents, health
from backend.app.middleware.logging import LoggingMiddleware
from backend.app.websocket.manager import WebSocketManager


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="SOCIETAS API",
        description="AI-powered governance simulation API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Register routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])
    app.include_router(policies.router, prefix="/api/v1/policies", tags=["policies"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    
    return app


app = create_app()
