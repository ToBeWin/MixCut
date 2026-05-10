"""Task-aware model selection with circuit breaker awareness."""

from __future__ import annotations

from backend.model.base import ModelProvider
from backend.model.registry import ModelRegistry


def select_provider(registry: ModelRegistry, task: str, override: str | None = None) -> ModelProvider:
    if override:
        provider = registry.providers.get(override)
        if provider is not None:
            cb = registry.circuit_breakers.get(override)
            if cb and not cb.allow_request():
                return registry.provider_for_task(task)
            return provider
    return registry.provider_for_task(task)