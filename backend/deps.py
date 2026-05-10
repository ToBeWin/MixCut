"""FastAPI dependency helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings, get_settings
from backend.database import get_db
from backend.model.registry import ModelRegistry, build_runtime_registry
from backend.tools.storage import StorageBackend, build_storage_backend


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_model_registry(
    settings: SettingsDep,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModelRegistry:
    """Build the lightweight provider registry for request handlers."""

    return await build_runtime_registry(settings, db)


def get_storage_backend(settings: SettingsDep) -> StorageBackend:
    return build_storage_backend(settings)


ModelRegistryDep = Annotated[ModelRegistry, Depends(get_model_registry)]
StorageBackendDep = Annotated[StorageBackend, Depends(get_storage_backend)]
