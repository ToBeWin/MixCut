"""API key authentication middleware."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import get_settings
from backend.observability.logging import get_logger

logger = get_logger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/health",
    "/health/models",
    "/health/storage",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware.

    If API_KEY is set in config, all requests must include either:
    - Header: Authorization: Bearer <api_key>
    - Query param: ?api_key=<api_key>

    Public paths (health, metrics, docs) are exempt.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # Skip auth if no API key configured
        if not settings.api_key:
            return await call_next(request)

        # Skip auth for public paths
        path = request.url.path
        # Strip API prefix for comparison
        stripped = path.removeprefix(settings.api_prefix) if path.startswith(settings.api_prefix) else path
        if stripped in PUBLIC_PATHS or path in PUBLIC_PATHS:
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token == settings.api_key:
                return await call_next(request)

        # Check query param
        query_key = request.query_params.get("api_key")
        if query_key == settings.api_key:
            return await call_next(request)

        logger.warning("auth_failed", path=path, method=request.method)
        return JSONResponse(
            status_code=401,
            content={"type": "auth", "title": "Unauthorized", "status": 401, "detail": "Invalid or missing API key"},
        )
