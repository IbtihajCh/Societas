import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import get_settings
from backend.app.database.connection import close_db, init_db
from backend.app.middleware.logging import LoggingMiddleware
from backend.app.routers import agents, ai, ai_historian, explain, governance, health, metrics, policies, save, simulation
from backend.app.websocket.manager import WebSocketManager, ws_manager

logger = logging.getLogger("societas.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Application started")
    yield
    await close_db()
    logger.info("Application stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SOCIETAS API",
        description="AI-powered governance simulation API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(LoggingMiddleware)

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])
    app.include_router(policies.router, prefix="/api/v1/policies", tags=["policies"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
    app.include_router(ai_historian.router, prefix="/api/v1/ai", tags=["ai"])
    app.include_router(governance.router, prefix="/api/v1/governance", tags=["governance"])
    app.include_router(save.router, prefix="/api/v1/saves", tags=["saves"])
    app.include_router(explain.router, prefix="/api/v1", tags=["explain"])

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_manager.send_to(websocket, {"echo": data})
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
        except Exception:
            await ws_manager.disconnect(websocket)

    return app


app = create_app()
