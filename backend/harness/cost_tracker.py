"""Token usage and cost tracking for model calls."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class CostRecord:
    node: str
    task: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    duration_ms: float = 0.0


current_node: ContextVar[str] = ContextVar("current_node", default="unknown")


class CostTracker:
    """Tracks model call costs per job. Thread-safe via instance isolation."""

    _instance: CostTracker | None = None

    def __init__(self) -> None:
        self.records: list[CostRecord] = []

    @classmethod
    def instance(cls) -> CostTracker:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def reset(self) -> None:
        self.records.clear()

    def record(self, record: CostRecord) -> None:
        self.records.append(record)

    def total_tokens(self) -> int:
        return sum(r.input_tokens + r.output_tokens for r in self.records)

    def summary_by_node(self) -> dict[str, dict[str, int | float]]:
        summary: dict[str, dict[str, int | float]] = {}
        for r in self.records:
            entry = summary.setdefault(r.node, {"input_tokens": 0, "output_tokens": 0, "calls": 0, "duration_ms": 0.0})
            entry["input_tokens"] += r.input_tokens
            entry["output_tokens"] += r.output_tokens
            entry["calls"] += 1
            entry["duration_ms"] += r.duration_ms
        return summary

    def summary_by_provider(self) -> dict[str, dict[str, int | float]]:
        summary: dict[str, dict[str, int | float]] = {}
        for r in self.records:
            entry = summary.setdefault(r.provider, {"input_tokens": 0, "output_tokens": 0, "calls": 0, "duration_ms": 0.0})
            entry["input_tokens"] += r.input_tokens
            entry["output_tokens"] += r.output_tokens
            entry["calls"] += 1
            entry["duration_ms"] += r.duration_ms
        return summary

    def to_dict(self) -> dict:
        return {
            "total_tokens": self.total_tokens(),
            "total_calls": len(self.records),
            "by_node": self.summary_by_node(),
            "by_provider": self.summary_by_provider(),
        }
