"""Managed agent loop primitives."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar


T = TypeVar("T")


class LoopMode(str, Enum):
    SINGLE = "single"
    RETRY_ON_INVALID = "retry_on_invalid"


class MaxIterationsExceeded(RuntimeError):
    """Raised when an agent cannot converge within the configured loop."""


StopCondition = Callable[[T], bool]


@dataclass(frozen=True)
class LoopPolicy:
    max_iterations: int = 10
    mode: LoopMode = LoopMode.RETRY_ON_INVALID
    stop_conditions: list[StopCondition[T]] = field(default_factory=list)


async def run_agent_loop(step: Callable[[int], Awaitable[T]], policy: LoopPolicy[T] | None = None) -> T:
    active_policy = policy or LoopPolicy()
    last_result: T | None = None
    for index in range(active_policy.max_iterations):
        last_result = await step(index)
        if not active_policy.stop_conditions or all(condition(last_result) for condition in active_policy.stop_conditions):
            return last_result
        if active_policy.mode is LoopMode.SINGLE:
            break
    raise MaxIterationsExceeded(f"Agent loop exceeded {active_policy.max_iterations} iterations")

