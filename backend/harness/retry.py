"""Async retry helpers with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 1.0
    multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    jitter_ratio: float = 0.2

    def delay_for_attempt(self, attempt_index: int) -> float:
        raw = min(self.base_delay_seconds * (self.multiplier ** attempt_index), self.max_delay_seconds)
        jitter = raw * self.jitter_ratio
        return max(0.0, raw + random.uniform(-jitter, jitter))


def retry_async(
    policy: RetryPolicy | None = None,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorate an async callable with retry behavior."""

    active_policy = policy or RetryPolicy()

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: BaseException | None = None
            for attempt in range(active_policy.attempts):
                try:
                    return await func(*args, **kwargs)
                except retry_on as exc:
                    last_error = exc
                    if attempt >= active_policy.attempts - 1:
                        break
                    await asyncio.sleep(active_policy.delay_for_attempt(attempt))
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator

