"""Model provider schemas."""

from __future__ import annotations

from backend.schemas.base import StrictBaseModel


class ModelProviderInfo(StrictBaseModel):
    name: str
    supports_vision: bool
    context_window: int
    max_output_tokens: int
    models: list[str]
    default_model: str | None = None


class ModelHealth(StrictBaseModel):
    name: str
    online: bool
    detail: str | None = None


class ModelTaskRoute(StrictBaseModel):
    task: str
    display_name: str
    modality: str
    provider: str
    model: str | None = None
    fallback_providers: list[str]
    available_providers: list[str]


class ModelTaskRouteUpdate(StrictBaseModel):
    provider: str
    model: str | None = None
    fallback_providers: list[str] = []


class ModelTaskRoutes(StrictBaseModel):
    routes: list[ModelTaskRoute]
