from __future__ import annotations

import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.errors import MixCutError
from backend.observability.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except MixCutError as exc:
            logger.warning("mixcut_error", error_class=exc.error_class.value, detail=exc.message)
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
            )
        except Exception as exc:
            logger.error("unhandled_error", path=request.url.path, error=str(exc), traceback=traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"type": "internal", "title": "InternalServerError", "status": 500, "detail": "An unexpected error occurred"},
            )