"""OpenAI-compatible provider.

Works with any service that implements the OpenAI API spec (vLLM, Ollama, DeepSeek, etc).
"""

from __future__ import annotations

from backend.errors import ModelAPIError
from backend.model.base import ModelMessage, ModelProvider, ModelUsage


class OpenAICompatibleProvider(ModelProvider):
    name = "openai_compatible"
    supports_vision = False
    context_window = 128000
    max_output_tokens = 4096

    def __init__(self, base_url: str | None, api_key: str | None, default_model: str) -> None:
        self.base_url = base_url or "http://localhost:11434/v1"
        self.api_key = api_key or "no-key"
        self.default_model = default_model
        self.models = [default_model]
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def _extract_usage(self, response) -> None:
        try:
            usage = response.usage
            self._last_usage = ModelUsage(
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            )
        except Exception:
            self._last_usage = None

    @staticmethod
    def _convert_messages(messages: list[ModelMessage], system: str | None = None) -> list[dict]:
        converted: list[dict] = []
        if system is not None:
            converted.append({"role": "system", "content": system})
        for msg in messages:
            converted.append({"role": msg.role, "content": msg.content})
        return converted

    async def chat(
        self,
        messages: list[ModelMessage],
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        client = self._get_client()
        converted = self._convert_messages(messages, system)
        try:
            response = await client.chat.completions.create(
                model=model or self.default_model,
                messages=converted,
                max_tokens=max_tokens or self.max_output_tokens,
                temperature=temperature,
            )
            self._extract_usage(response)
            return response.choices[0].message.content or ""
        except Exception as exc:
            self._last_usage = None
            raise ModelAPIError(self.name, str(exc)) from exc

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception:
            return False

    def default_model_for_task(self, task: str) -> str | None:
        return self.default_model
