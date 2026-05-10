"""Small circuit breaker implementation for external services."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar


T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when a call is blocked by an open circuit."""


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    opened_at: float | None = None

    def allow_request(self) -> bool:
        if self.state is CircuitState.CLOSED:
            return True
        if self.state is CircuitState.OPEN and self.opened_at is not None:
            if time.monotonic() - self.opened_at >= self.recovery_timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
        return self.state is CircuitState.HALF_OPEN

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        if not self.allow_request():
            raise CircuitOpenError(f"Circuit '{self.name}' is open")
        try:
            result = await func()
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()

