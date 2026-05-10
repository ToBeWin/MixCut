"""Provider interface shared by model backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelMessage:
    role: str
    content: str


@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


class ModelProvider(ABC):
    name: str
    supports_vision: bool
    context_window: int
    max_output_tokens: int
    models: list[str]
    _last_usage: ModelUsage | None = None

    @property
    def last_usage(self) -> ModelUsage | None:
        return self._last_usage

    @abstractmethod
    async def chat(
        self,
        messages: list[ModelMessage],
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        """Return a complete text response."""

    async def vision(
        self,
        messages: list[ModelMessage],
        images_b64: list[str],
        system: str | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> str:
        raise NotImplementedError(f"{self.name} does not support vision")

    async def stream_chat(
        self,
        messages: list[ModelMessage],
        system: str | None = None,
    ) -> AsyncIterator[str]:
        yield await self.chat(messages=messages, system=system)

    async def health_check(self) -> bool:
        return True

    def default_model_for_task(self, task: str) -> str | None:
        del task
        default_model = getattr(self, "default_model", None)
        if default_model:
            return default_model
        return self.models[0] if self.models else None
