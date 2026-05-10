from __future__ import annotations

import httpx

from backend.errors import ModelAPIError
from backend.model.base import ModelMessage, ModelProvider


class OllamaProvider(ModelProvider):
    name = "ollama"
    supports_vision = False
    context_window = 32768
    max_output_tokens = 4096
    models: list[str] = []

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.3",
        api_key: str = "ollama",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=f"{self.base_url}/v1",
            )
        return self._client

    @staticmethod
    def _convert_messages(messages: list[ModelMessage], system: str | None = None) -> list[dict]:
        converted: list[dict] = []
        if system is not None:
            converted.append({"role": "system", "content": system})
        for msg in messages:
            role = msg.role if msg.role in ("user", "assistant", "system") else "user"
            converted.append({"role": role, "content": msg.content})
        return converted

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
                "messages": self._convert_messages(messages, system),
                "temperature": temperature,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise ModelAPIError("ollama", str(exc)) from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as http:
                resp = await http.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    self.models = [m["name"] for m in data.get("models", [])]
                    return True
                return False
        except Exception:
            return False
