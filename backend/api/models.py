"""Model listing and health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.deps import ModelRegistryDep
from backend.models.model_route import ModelRouteConfig
from backend.schemas.model import (
    ModelHealth,
    ModelProviderInfo,
    ModelTaskRoute,
    ModelTaskRoutes,
    ModelTaskRouteUpdate,
)


router = APIRouter()


@router.get("", response_model=list[ModelProviderInfo])
async def list_models(registry: ModelRegistryDep) -> list[ModelProviderInfo]:
    return registry.list_provider_info()


@router.get("/health", response_model=list[ModelHealth])
async def model_health(registry: ModelRegistryDep) -> list[ModelHealth]:
    return await registry.health_report()


@router.get("/routes", response_model=ModelTaskRoutes)
async def list_model_routes(registry: ModelRegistryDep) -> ModelTaskRoutes:
    return ModelTaskRoutes(routes=registry.list_task_routes())


@router.patch("/routes/{task}", response_model=ModelTaskRoute)
async def update_model_route(
    task: str,
    payload: ModelTaskRouteUpdate,
    registry: ModelRegistryDep,
    db: AsyncSession = Depends(get_db),
) -> ModelTaskRoute:
    try:
        updated_route = registry.update_task_route(
            task=task,
            provider_name=payload.provider,
            model=payload.model,
            fallback_providers=payload.fallback_providers,
        )
        result = await db.execute(select(ModelRouteConfig).where(ModelRouteConfig.task == task))
        config = result.scalar_one_or_none()
        fallback_csv = ",".join(payload.fallback_providers)
        if config is None:
            config = ModelRouteConfig(
                task=task,
                provider=payload.provider,
                model=payload.model,
                fallback_providers=fallback_csv,
            )
            db.add(config)
        else:
            config.provider = payload.provider
            config.model = payload.model
            config.fallback_providers = fallback_csv
        await db.flush()
        return updated_route
    except KeyError:
        raise HTTPException(status_code=404, detail="Task route not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
