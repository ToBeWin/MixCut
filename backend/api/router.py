"""Top-level API router."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api import assets, chat, export, jobs, models, projects
from backend.deps import ModelRegistryDep, StorageBackendDep


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


@api_router.get("/health/models", tags=["health"])
async def health_models(registry: ModelRegistryDep) -> dict[str, object]:
    report = await registry.health_report()
    all_online = all(m.online for m in report)
    return {
        "status": "ok" if all_online else "degraded",
        "providers": [{"name": m.name, "online": m.online, "detail": m.detail} for m in report],
    }


@api_router.get("/health/storage", tags=["health"])
async def health_storage(storage: StorageBackendDep) -> dict[str, str]:
    try:
        await storage.exists("__health_check__")
        return {"status": "ok", "backend": type(storage).__name__}
    except Exception as exc:
        return {"status": "error", "backend": type(storage).__name__, "detail": str(exc)}

