"""Provider registry and task routing with circuit breaker integration."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.harness.circuit_breaker import CircuitBreaker
from backend.harness.config import get_circuit_breakers
from backend.model.base import ModelProvider
from backend.model.providers.mock import MockModelProvider
from backend.models.model_route import ModelRouteConfig
from backend.observability.logging import get_logger
from backend.schemas.model import ModelHealth, ModelProviderInfo, ModelTaskRoute

logger = get_logger(__name__)

TASK_METADATA = {
    "multimodal_understanding": {"display_name": "Image / Video Understanding", "modality": "multimodal"},
    "edit_planning": {"display_name": "Edit Planning", "modality": "text"},
    "correction_intent": {"display_name": "Correction Intent", "modality": "text"},
    "tts_script_writing": {"display_name": "TTS Script Writing", "modality": "text"},
}

_route_overrides: dict[str, dict[str, object]] = {}


@dataclass
class ModelRegistry:
    providers: dict[str, ModelProvider]
    task_routes: dict[str, list[str]]
    circuit_breakers: dict[str, CircuitBreaker] = field(default_factory=dict)

    def get(self, name: str) -> ModelProvider:
        return self.providers[name]

    def route_names_for_task(self, task: str) -> list[str]:
        override = _route_overrides.get(task)
        if override:
            primary = str(override["provider"])
            fallback_names = [str(name) for name in override.get("fallback_providers", [])]
            ordered = [primary, *[name for name in fallback_names if name != primary]]
            return ordered
        return list(self.task_routes.get(task, []))

    def available_providers_for_task(self, task: str) -> list[str]:
        metadata = TASK_METADATA.get(task, {})
        modality = metadata.get("modality")
        providers = list(self.providers.values())
        if modality == "multimodal":
            providers = [provider for provider in providers if provider.supports_vision]
        return [provider.name for provider in providers]

    def route_model_for_task(self, task: str, provider_name: str) -> str | None:
        override = _route_overrides.get(task)
        if override and override.get("provider") == provider_name:
            model = override.get("model")
            if isinstance(model, str) and model:
                return model
        provider = self.providers.get(provider_name)
        return provider.default_model_for_task(task) if provider else None

    def provider_for_task(self, task: str) -> ModelProvider:
        route = self.route_names_for_task(task)
        for provider_name in route:
            if provider_name not in self.providers:
                continue
            cb = self.circuit_breakers.get(provider_name)
            if cb and not cb.allow_request():
                logger.warning("circuit_open", provider=provider_name, task=task)
                continue
            return self.providers[provider_name]
        if self.circuit_breakers:
            for name, provider in self.providers.items():
                cb = self.circuit_breakers.get(name)
                if cb is None or cb.allow_request():
                    return provider
        elif self.providers:
            return next(iter(self.providers.values()))
        return MockModelProvider()

    def record_success(self, provider_name: str) -> None:
        cb = self.circuit_breakers.get(provider_name)
        if cb:
            cb.record_success()

    def record_failure(self, provider_name: str) -> None:
        cb = self.circuit_breakers.get(provider_name)
        if cb:
            cb.record_failure()

    def list_provider_info(self) -> list[ModelProviderInfo]:
        return [
            ModelProviderInfo(
                name=provider.name,
                supports_vision=provider.supports_vision,
                context_window=provider.context_window,
                max_output_tokens=provider.max_output_tokens,
                models=provider.models,
                default_model=provider.default_model_for_task("multimodal_understanding"),
            )
            for provider in self.providers.values()
        ]

    def list_task_routes(self) -> list[ModelTaskRoute]:
        routes: list[ModelTaskRoute] = []
        for task, metadata in TASK_METADATA.items():
            available_providers = [name for name in self.route_names_for_task(task) if name in self.providers]
            if not available_providers:
                available_providers = self.available_providers_for_task(task)
            provider_name = available_providers[0] if available_providers else "mock"
            routes.append(
                ModelTaskRoute(
                    task=task,
                    display_name=metadata["display_name"],
                    modality=metadata["modality"],
                    provider=provider_name,
                    model=self.route_model_for_task(task, provider_name),
                    fallback_providers=available_providers[1:],
                    available_providers=self.available_providers_for_task(task),
                )
            )
        return routes

    def update_task_route(
        self,
        task: str,
        provider_name: str,
        model: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> ModelTaskRoute:
        if task not in TASK_METADATA:
            raise KeyError(task)
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}")
        if TASK_METADATA[task]["modality"] == "multimodal" and not provider.supports_vision:
            raise ValueError(f"Provider {provider_name} does not support multimodal understanding")
        if model and model not in provider.models:
            raise ValueError(f"Provider {provider_name} does not expose model {model}")
        available_provider_names = set(self.available_providers_for_task(task))
        fallback_names = [
            name for name in (fallback_providers or [])
            if name in self.providers and name != provider_name and name in available_provider_names
        ]
        _route_overrides[task] = {
            "provider": provider_name,
            "model": model,
            "fallback_providers": fallback_names,
        }
        metadata = TASK_METADATA[task]
        return ModelTaskRoute(
            task=task,
            display_name=metadata["display_name"],
            modality=metadata["modality"],
            provider=provider_name,
            model=model or provider.default_model_for_task(task),
            fallback_providers=fallback_names,
            available_providers=self.available_providers_for_task(task),
        )

    async def health_report(self) -> list[ModelHealth]:
        return [
            ModelHealth(name=provider.name, online=await provider.health_check())
            for provider in self.providers.values()
        ]


def build_default_registry(settings: Settings) -> ModelRegistry:
    providers: dict[str, ModelProvider] = {}
    providers["mock"] = MockModelProvider()

    try:
        from backend.model.providers.anthropic import AnthropicProvider

        if settings.anthropic_api_key:
            providers["anthropic"] = AnthropicProvider(api_key=settings.anthropic_api_key)
    except ImportError:
        pass

    try:
        from backend.model.providers.openai import OpenAIProvider

        if settings.openai_api_key:
            providers["openai"] = OpenAIProvider(api_key=settings.openai_api_key)
    except ImportError:
        pass

    try:
        from backend.model.providers.google import GoogleProvider

        if settings.google_api_key:
            providers["google"] = GoogleProvider(api_key=settings.google_api_key)
    except ImportError:
        pass

    try:
        from backend.model.providers.qwen import DashScopeProvider

        if settings.dashscope_api_key:
            providers["dashscope"] = DashScopeProvider(api_key=settings.dashscope_api_key)
    except ImportError:
        pass

    try:
        from backend.model.providers.ollama import OllamaProvider

        providers["ollama"] = OllamaProvider(
            base_url=settings.ollama_base_url,
            default_model=settings.ollama_default_model,
        )
    except ImportError:
        pass

    try:
        from backend.model.providers.openai_compatible import OpenAICompatibleProvider

        if settings.openai_compatible_base_url or settings.openai_compatible_api_key:
            providers["openai_compatible"] = OpenAICompatibleProvider(
                settings.openai_compatible_base_url,
                settings.openai_compatible_api_key,
                settings.openai_compatible_default_model,
            )
    except ImportError:
        pass

    task_routes: dict[str, list[str]] = {
        "multimodal_understanding": ["dashscope", "google", "openai", "mock"],
        "edit_planning": ["anthropic", "openai", "dashscope", "openai_compatible", "mock"],
        "correction_intent": ["anthropic", "openai", "mock"],
        "tts_script_writing": ["dashscope", "anthropic", "mock"],
    }

    circuit_breakers = get_circuit_breakers()

    return ModelRegistry(
        providers=providers,
        task_routes=task_routes,
        circuit_breakers=circuit_breakers,
    )


def _parse_fallbacks(raw_fallbacks: str) -> list[str]:
    return [item for item in raw_fallbacks.split(",") if item]


async def build_runtime_registry(settings: Settings, db: AsyncSession | None = None) -> ModelRegistry:
    registry = build_default_registry(settings)

    if db is not None:
        result = await db.execute(select(ModelRouteConfig))
        route_configs = result.scalars().all()
    else:
        from backend.database import _get_session_factory

        async with _get_session_factory()() as session:
            result = await session.execute(select(ModelRouteConfig))
            route_configs = result.scalars().all()

    for route in route_configs:
        try:
            registry.update_task_route(
                task=route.task,
                provider_name=route.provider,
                model=route.model,
                fallback_providers=_parse_fallbacks(route.fallback_providers),
            )
        except ValueError as exc:
            logger.warning("invalid_persisted_model_route", task=route.task, provider=route.provider, error=str(exc))

    return registry
