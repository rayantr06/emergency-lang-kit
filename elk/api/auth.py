"""
API Key authentication middleware.
Enforces X-API-Key or Authorization: Bearer when settings.API_KEY is set.
"""

from typing import Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from elk.core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Require API key on all endpoints except health/metrics."""

    async def dispatch(self, request: Request, call_next: Callable):
        if not settings.API_KEY:
            return await call_next(request)

        path = request.url.path
        if path in {"/health", "/metrics"}:
            return await call_next(request)

        provided = request.headers.get("x-api-key") or request.headers.get("authorization")
        if provided and provided.lower().startswith("bearer "):
            provided = provided.split(" ", 1)[1]

        if provided != settings.API_KEY:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"}
            )

        return await call_next(request)
