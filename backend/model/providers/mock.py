"""Deterministic local provider for development and tests."""

from __future__ import annotations

from backend.model.base import ModelMessage, ModelProvider


class MockModelProvider(ModelProvider):
    name = "mock"
    supports_vision = True
    context_window = 8192
    max_output_tokens = 2048
    models = ["mock-text", "mock-vision"]

    async def chat(
        self,
        messages: list[ModelMessage],
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        del system, max_tokens, temperature, model
        last = messages[-1].content if messages else ""
        return f"mock response: {last}".strip()

    async def vision(
        self,
        messages: list[ModelMessage],
        images_b64: list[str],
        system: str | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> str:
        del system, max_tokens, model
        return f"mock vision response for {len(images_b64)} image(s) and {len(messages)} message(s)"

    def default_model_for_task(self, task: str) -> str | None:
        return "mock-vision" if task == "multimodal_understanding" else "mock-text"
