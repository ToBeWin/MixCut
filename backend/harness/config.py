from __future__ import annotations

from backend.config import get_settings
from backend.harness.circuit_breaker import CircuitBreaker
from backend.harness.loop import LoopPolicy
from backend.harness.retry import RetryPolicy
from backend.harness.timeout import TimeoutPolicy

_TIMEOUT_MAP = {
    "understand": "agent_node_timeout_understand",
    "plan": "agent_node_timeout_plan",
    "execute": "agent_node_timeout_execute",
    "subtitle": "agent_node_timeout_subtitle",
    "tts": "agent_node_timeout_tts",
    "correct": "agent_node_timeout_correct",
}


def get_timeout(node_name: str) -> TimeoutPolicy:
    settings = get_settings()
    key = _TIMEOUT_MAP.get(node_name)
    seconds = getattr(settings, key, 120) if key else 120
    return TimeoutPolicy(seconds=seconds, node_name=node_name)


def get_model_retry() -> RetryPolicy:
    return RetryPolicy(attempts=3, base_delay_seconds=1.0, multiplier=2.0, max_delay_seconds=30.0, jitter_ratio=0.2)


def get_ffmpeg_retry() -> RetryPolicy:
    return RetryPolicy(attempts=2, base_delay_seconds=0.5, multiplier=2.0, max_delay_seconds=10.0, jitter_ratio=0.1)


def get_correction_loop_policy() -> LoopPolicy:
    settings = get_settings()
    from backend.harness.loop import LoopMode

    return LoopPolicy(
        max_iterations=settings.agent_max_iterations,
        mode=LoopMode.RETRY_ON_INVALID,
    )


def get_circuit_breakers() -> dict[str, CircuitBreaker]:
    settings = get_settings()
    return {
        "anthropic": CircuitBreaker(name="anthropic", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
        "openai": CircuitBreaker(name="openai", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
        "google": CircuitBreaker(name="google", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
        "dashscope": CircuitBreaker(name="dashscope", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
        "ollama": CircuitBreaker(name="ollama", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
        "minimax": CircuitBreaker(name="minimax", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
        "volcengine": CircuitBreaker(name="volcengine", failure_threshold=settings.circuit_failure_threshold, recovery_timeout_seconds=settings.circuit_recovery_timeout_seconds),
    }