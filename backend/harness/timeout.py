"""Timeout enforcement helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar("T")


class NodeTimeoutError(TimeoutError):
    """Raised when an agent node exceeds its timeout."""


@dataclass(frozen=True)
class TimeoutPolicy:
    seconds: float
    node_name: str = "unknown"


async def run_with_timeout(awaitable: Awaitable[T], policy: TimeoutPolicy) -> T:
    try:
        return await asyncio.wait_for(awaitable, timeout=policy.seconds)
    except asyncio.TimeoutError as exc:
        raise NodeTimeoutError(f"{policy.node_name} exceeded {policy.seconds}s timeout") from exc

