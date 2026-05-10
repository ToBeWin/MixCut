from __future__ import annotations

from backend.errors import ModelAPIError
from backend.model.base import ModelMessage, ModelProvider, ModelUsage


class DashScopeProvider(ModelProvider):
    name = "dashscope"
    supports_vision = True
    context_window = 128000
    max_output_tokens = 8192
    models = ["qwen3-vl", "qwen3"]

    def __init__(
        self,
        api_key: str | None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        vision_model: str = "qwen3-vl",
        text_model: str = "qwen3",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.vision_model = vision_model
        self.text_model = text_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(
                api_key=self.api_key or "EMPTY",
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
                "model": model or self.text_model,
                "messages": self._convert_messages(messages, system),
                "temperature": temperature,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            response = await client.chat.completions.create(**kwargs)
            self._extract_usage(response)
            return response.choices[0].message.content or ""
        except Exception as exc:
            self._last_usage = None
            raise ModelAPIError("dashscope", str(exc)) from exc

    async def vision(
        self,
        messages: list[ModelMessage],
        images_b64: list[str],
        system: str | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> str:
        try:
            client = self._get_client()
            content_parts: list[dict] = []
            for img_b64 in images_b64:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                })
            converted: list[dict] = []
            if system is not None:
                converted.append({"role": "system", "content": system})
            for msg in messages:
                role = msg.role if msg.role in ("user", "assistant", "system") else "user"
                converted.append({"role": role, "content": msg.content})
            last_user_idx = None
            for i, m in enumerate(converted):
                if m["role"] == "user":
                    last_user_idx = i
            if last_user_idx is not None:
                user_content = converted[last_user_idx]["content"]
                if isinstance(user_content, str):
                    parts: list[dict] = [{"type": "text", "text": user_content}]
                else:
                    parts = []
                parts.extend(content_parts)
                converted[last_user_idx] = {"role": "user", "content": parts}
            else:
                converted.append({"role": "user", "content": content_parts})
            kwargs: dict = {
                "model": model or self.vision_model,
                "messages": converted,
                "temperature": 0.2,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            response = await client.chat.completions.create(**kwargs)
            self._extract_usage(response)
            return response.choices[0].message.content or ""
        except Exception as exc:
            self._last_usage = None
            raise ModelAPIError("dashscope", str(exc)) from exc

    async def health_check(self) -> bool:
        return bool(self.api_key)

    def default_model_for_task(self, task: str) -> str | None:
        return self.vision_model if task == "multimodal_understanding" else self.text_model
