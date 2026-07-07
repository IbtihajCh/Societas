"""
Backend Middleware Module
=========================

HTTP middleware implementations.
"""

from backend.app.middleware.logging import LoggingMiddleware

__all__ = [
    "LoggingMiddleware",
]
