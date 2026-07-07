import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("societas.api")

SKIP_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in SKIP_PATHS:
            return await call_next(request)

        start_time = time.time()
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "%s %s -> %d (%.1fms) [%s]",
            method,
            path,
            response.status_code,
            duration_ms,
            client_ip,
        )
        return response
