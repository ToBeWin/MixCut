"""Top-level API router."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api import assets, chat, export, jobs, models, projects


api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(export.router, prefix="/export", tags=["export"])


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

