from __future__ import annotations

from backend.errors import ModelAPIError
from backend.model.base import ModelMessage, ModelProvider, ModelUsage


class AnthropicProvider(ModelProvider):
    name = "anthropic"
    supports_vision = False
    context_window = 200000
    max_output_tokens = 8192
    models = ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]

    def __init__(self, api_key: str | None, default_model: str = "claude-sonnet-4-20250514") -> None:
        self.api_key = api_key
        self.default_model = default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    @staticmethod
    def _convert_messages(messages: list[ModelMessage]) -> list[dict]:
        converted: list[dict] = []
        for msg in messages:
            role = msg.role if msg.role in ("user", "assistant") else "user"
            converted.append({"role": role, "content": msg.content})
        return converted

    def _extract_usage(self, response) -> None:
        try:
            usage = response.usage
            self._last_usage = ModelUsage(
                input_tokens=getattr(usage, "input_tokens", 0),
                output_tokens=getattr(usage, "output_tokens", 0),
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
                cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            )
        except Exception:
            self._last_usage = None

    async def chat(
        self,
        messages: list[ModelMessage],
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        try:
            client = self._get_client()
            kwargs: dict = {
                "model": model or self.default_model,
                "messages": self._convert_messages(messages),
                "temperature": temperature,
            }
            if system is not None:
                kwargs["system"] = system
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            else:
                kwargs["max_tokens"] = self.max_output_tokens
            response = await client.messages.create(**kwargs)
            self._extract_usage(response)
            return response.content[0].text
        except Exception as exc:
            self._last_usage = None
            raise ModelAPIError("anthropic", str(exc)) from exc

    async def health_check(self) -> bool:
        return bool(self.api_key)
