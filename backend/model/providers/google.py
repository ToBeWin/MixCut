from __future__ import annotations

import base64

from backend.errors import ModelAPIError
from backend.model.base import ModelMessage, ModelProvider, ModelUsage


class GoogleProvider(ModelProvider):
    name = "google"
    supports_vision = True
    context_window = 1048576
    max_output_tokens = 8192
    models = ["gemini-2.5-flash", "gemini-2.5-pro"]

    def __init__(self, api_key: str | None, default_model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.default_model = default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _extract_usage(self, response) -> None:
        try:
            meta = response.usage_metadata
            self._last_usage = ModelUsage(
                input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
                output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
            )
        except Exception:
            self._last_usage = None

    @staticmethod
    def _convert_messages(messages: list[ModelMessage]) -> list[dict]:
        converted: list[dict] = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            converted.append({"role": role, "parts": [msg.content]})
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
            from google.genai import types

            client = self._get_client()
            contents = self._convert_messages(messages)
            config_kwargs: dict = {
                "temperature": temperature,
            }
            if max_tokens is not None:
                config_kwargs["max_output_tokens"] = max_tokens
            config = types.GenerateContentConfig(**config_kwargs)
            if system is not None:
                config.system_instruction = system
            response = await client.aio.models.generate_content(
                model=model or self.default_model,
                contents=contents,
                config=config,
            )
            self._extract_usage(response)
            return response.text or ""
        except Exception as exc:
            self._last_usage = None
            raise ModelAPIError("google", str(exc)) from exc

    async def vision(
        self,
        messages: list[ModelMessage],
        images_b64: list[str],
        system: str | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> str:
        try:
            from google.genai import types

            client = self._get_client()
            image_parts: list[types.Part] = []
            for img_b64 in images_b64:
                image_parts.append(
                    types.Part.from_bytes(
                        data=base64.b64decode(img_b64),
                        mime_type="image/jpeg",
                    )
                )
            contents: list[dict] = []
            text_messages = [m for m in messages if m.role != "system"]
            if not text_messages:
                text_messages = [ModelMessage(role="user", content="Describe these images.")]
            for msg in text_messages:
                role = "model" if msg.role == "assistant" else "user"
                parts = [types.Part.from_text(text=msg.content)]
                if role == "user" and image_parts:
                    parts.extend(image_parts)
                    image_parts = []
                contents.append({"role": role, "parts": parts})
            if image_parts:
                contents.append({"role": "user", "parts": image_parts})
            config_kwargs: dict = {"temperature": 0.2}
            if max_tokens is not None:
                config_kwargs["max_output_tokens"] = max_tokens
            config = types.GenerateContentConfig(**config_kwargs)
            if system is not None:
                config.system_instruction = system
            response = await client.aio.models.generate_content(
                model=model or self.default_model,
                contents=contents,
                config=config,
            )
            self._extract_usage(response)
            return response.text or ""
        except Exception as exc:
            self._last_usage = None
            raise ModelAPIError("google", str(exc)) from exc

    async def health_check(self) -> bool:
        return bool(self.api_key)
