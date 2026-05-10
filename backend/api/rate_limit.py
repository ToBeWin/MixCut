from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.observability.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter with Redis backend and in-memory fallback.

    Limits are keyed by client IP + route category. When Redis is available
    the counters are shared across all API processes; otherwise falls back to
    a local dict (single-process only).
    """

    def __init__(
        self,
        app: Callable,
        default_limit: int = 100,
        default_window_seconds: int = 60,
        upload_limit: int = 10,
        job_limit: int = 5,
    ) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self.upload_limit = upload_limit
        self.job_limit = job_limit
        self._requests: dict[str, list[float]] = {}
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis
                from backend.config import get_settings
                settings = get_settings()
                self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = False  # type: ignore[assignment]
        return self._redis if self._redis is not False else None

    def _get_limit(self, path: str) -> tuple[int, int]:
        if "/upload" in path:
            return self.upload_limit, self.default_window_seconds
        if path.rstrip("/").endswith("/jobs"):
            return self.job_limit, self.default_window_seconds
        return self.default_limit, self.default_window_seconds

    def _check_rate_local(self, key: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        timestamps = self._requests.get(key, [])
        timestamps = [t for t in timestamps if now - t < window]
        self._requests[key] = timestamps
        if len(timestamps) >= limit:
            return False
        timestamps.append(now)
        return True

    async def _check_rate_redis(self, key: str, limit: int, window: int) -> bool:
        r = self._get_redis()
        if r is None:
            return self._check_rate_local(key, limit, window)
        try:
            now = time.time()
            pipe = r.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = pipe.execute()
            count = results[2]
            return count <= limit
        except Exception:
            logger.warning("redis_rate_limit_fallback")
            return self._check_rate_local(key, limit, window)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        limit, window = self._get_limit(request.url.path)
        client_key = request.client.host if request.client else "unknown"
        category = "upload" if "/upload" in request.url.path else "jobs" if "/jobs" in request.url.path else "default"
        key = f"rl:{client_key}:{category}"

        allowed = await self._check_rate_redis(key, limit, window)
        if not allowed:
            logger.warning("rate_limit_exceeded", client=client_key, path=request.url.path)
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)
