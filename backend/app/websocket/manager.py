import json
import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger("societas.websocket")


class WebSocketManager:
    def __init__(self):
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WebSocket connected (%d active)", len(self._connections))

    async def disconnect(self, websocket: WebSocket):
        self._connections.discard(websocket)
        logger.info("WebSocket disconnected (%d active)", len(self._connections))

    async def broadcast(self, message: dict):
        dead: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self._connections.discard(connection)

    async def send_to(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            self._connections.discard(websocket)

    def get_connection_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()
