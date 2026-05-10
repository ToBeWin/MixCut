from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass

from backend.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ProgressEvent:
    job_id: str
    event: str
    progress: float = 0.0
    message: str | None = None
    node: str | None = None
    cost: dict | None = None

    def to_sse(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(asdict(self), ensure_ascii=False)}\n\n"


_subscriptions: dict[str, list[asyncio.Queue[ProgressEvent]]] = {}


def publish_event(event: ProgressEvent) -> None:
    for queue in _subscriptions.get(event.job_id, []):
        queue.put_nowait(event)


async def progress_event_stream(job_id: str) -> AsyncIterator[str]:
    queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()
    _subscriptions.setdefault(job_id, []).append(queue)
    try:
        yield ProgressEvent(job_id=job_id, event="connected", message="progress stream ready").to_sse()
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield event.to_sse()
            if event.event in ("completed", "failed", "canceled"):
                break
    except asyncio.TimeoutError:
        yield ProgressEvent(job_id=job_id, event="heartbeat", message="keep-alive").to_sse()
    finally:
        _subscriptions.get(job_id, []).remove(queue)