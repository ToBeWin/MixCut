from __future__ import annotations

import asyncio
import time

from backend.harness.circuit_breaker import CircuitOpenError
from backend.harness.config import get_model_retry
from backend.harness.cost_tracker import CostRecord, CostTracker, current_node
from backend.harness.retry import retry_async
from backend.model.base import ModelMessage, ModelProvider
from backend.model.registry import ModelRegistry
from backend.observability.logging import get_logger

logger = get_logger(__name__)

# Per-provider concurrency semaphores — prevents hammering a single model API
_provider_semaphores: dict[str, asyncio.Semaphore] = {}


def _get_provider_semaphore(provider_name: str) -> asyncio.Semaphore:
    if provider_name not in _provider_semaphores:
        from backend.config import get_settings
        limit = get_settings().max_model_concurrent_calls
        _provider_semaphores[provider_name] = asyncio.Semaphore(limit)
    return _provider_semaphores[provider_name]

_MEDIA_RETRY_ON = (ConnectionError, TimeoutError, OSError)


def _track_usage(provider: ModelProvider, task: str, selected_model: str | None, elapsed_ms: float) -> None:
    usage = provider.last_usage
    if usage is None:
        return
    node = current_node.get("unknown")
    model_label = selected_model or ""
    CostTracker.instance().record(CostRecord(
        node=node,
        task=task,
        provider=provider.name,
        model=model_label,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=usage.cache_read_tokens,
        cache_creation_tokens=usage.cache_creation_tokens,
        duration_ms=elapsed_ms,
    ))

    # Prometheus metrics
    try:
        from backend.observability.metrics import model_call_duration_seconds, model_tokens_total
        model_call_duration_seconds.labels(provider=provider.name, model=model_label).observe(elapsed_ms / 1000)
        model_tokens_total.labels(provider=provider.name, model=model_label, type="input").inc(usage.input_tokens)
        model_tokens_total.labels(provider=provider.name, model=model_label, type="output").inc(usage.output_tokens)
    except (ImportError, Exception):
        pass


async def call_model(
    registry: ModelRegistry,
    task: str,
    messages: list[ModelMessage],
    system: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.2,
    retry_on: tuple[type[BaseException], ...] = _MEDIA_RETRY_ON,
) -> str:
    provider = registry.provider_for_task(task)
    selected_model = registry.route_model_for_task(task, provider.name)
    policy = get_model_retry()

    sem = _get_provider_semaphore(provider.name)

    @retry_async(policy=policy, retry_on=retry_on + (CircuitOpenError,))
    async def _call() -> str:
        async with sem:
            start = time.monotonic()
            result = await provider.chat(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                model=selected_model,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            registry.record_success(provider.name)
            _track_usage(provider, task, selected_model, elapsed_ms)
            return result

    try:
        return await _call()
    except CircuitOpenError:
        logger.error("model_circuit_open", task=task, provider=provider.name)
        fallback_route = registry.task_routes.get(task, [])
        for fallback_name in fallback_route:
            if fallback_name == provider.name:
                continue
            fb_provider = registry.providers.get(fallback_name)
            if fb_provider is None:
                continue
            fb_cb = registry.circuit_breakers.get(fallback_name)
            if fb_cb and not fb_cb.allow_request():
                continue
            try:
                fb_sem = _get_provider_semaphore(fallback_name)
                async with fb_sem:
                    start = time.monotonic()
                    result = await fb_provider.chat(
                        messages=messages,
                        system=system,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        model=registry.route_model_for_task(task, fallback_name),
                    )
                    elapsed_ms = (time.monotonic() - start) * 1000
                    registry.record_success(fallback_name)
                    _track_usage(fb_provider, task, registry.route_model_for_task(task, fallback_name), elapsed_ms)
                    return result
            except Exception as exc:
                registry.record_failure(fallback_name)
                logger.error("model_fallback_failed", task=task, provider=fallback_name, error=str(exc))
        raise
    except Exception as exc:
        registry.record_failure(provider.name)
        raise


async def call_vision_model(
    registry: ModelRegistry,
    task: str,
    messages: list[ModelMessage],
    images_b64: list[str],
    system: str | None = None,
    max_tokens: int | None = None,
    retry_on: tuple[type[BaseException], ...] = _MEDIA_RETRY_ON,
) -> str:
    provider = registry.provider_for_task(task)
    selected_model = registry.route_model_for_task(task, provider.name)
    policy = get_model_retry()
    sem = _get_provider_semaphore(provider.name)

    @retry_async(policy=policy, retry_on=retry_on + (CircuitOpenError,))
    async def _call() -> str:
        async with sem:
            start = time.monotonic()
            result = await provider.vision(
                messages=messages,
                images_b64=images_b64,
                system=system,
                max_tokens=max_tokens,
                model=selected_model,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            registry.record_success(provider.name)
            _track_usage(provider, task, selected_model, elapsed_ms)
            return result

    try:
        return await _call()
    except CircuitOpenError:
        logger.error("vision_model_circuit_open", task=task, provider=provider.name)
        for fallback_name in registry.route_names_for_task(task):
            if fallback_name == provider.name:
                continue
            fb_provider = registry.providers.get(fallback_name)
            if fb_provider is None or not fb_provider.supports_vision:
                continue
            fb_cb = registry.circuit_breakers.get(fallback_name)
            if fb_cb and not fb_cb.allow_request():
                continue
            try:
                fb_sem = _get_provider_semaphore(fallback_name)
                async with fb_sem:
                    start = time.monotonic()
                    result = await fb_provider.vision(
                        messages=messages,
                        images_b64=images_b64,
                        system=system,
                        max_tokens=max_tokens,
                        model=registry.route_model_for_task(task, fallback_name),
                    )
                    elapsed_ms = (time.monotonic() - start) * 1000
                    registry.record_success(fallback_name)
                    _track_usage(fb_provider, task, registry.route_model_for_task(task, fallback_name), elapsed_ms)
                    return result
            except Exception as exc:
                registry.record_failure(fallback_name)
                logger.error("vision_model_fallback_failed", task=task, provider=fallback_name, error=str(exc))
        raise
    except Exception:
        registry.record_failure(provider.name)
        raise
