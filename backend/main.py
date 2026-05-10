from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.error_handler import ErrorHandlerMiddleware
from backend.api.rate_limit import RateLimitMiddleware
from backend.api.router import api_router
from backend.config import get_settings
from backend.database import create_all_tables
from backend.observability.logging import configure_logging, get_logger
from backend.observability.metrics import metrics_router
from backend.observability.tracing import configure_tracing


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    configure_tracing(settings)
    await create_all_tables()
    logger.info("mixcut_backend_starting", environment=settings.environment)
    yield
    logger.info("mixcut_backend_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        default_limit=settings.api_rate_limit_default,
        upload_limit=settings.api_rate_limit_uploads,
        job_limit=settings.api_rate_limit_jobs,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(metrics_router)
    return app


app = create_app()