from __future__ import annotations

from enum import Enum


class ErrorClass(str, Enum):
    MODEL_API = "model_api"
    MODEL_OUTPUT = "model_output"
    FFMPEG = "ffmpeg"
    ASSET = "asset"
    STORAGE = "storage"
    NODE_TIMEOUT = "node_timeout"
    MAX_ITERATIONS = "max_iterations"
    CIRCUIT_OPEN = "circuit_open"
    AMBIGUITY = "ambiguity"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    INTERNAL = "internal"


class MixCutError(Exception):
    error_class: ErrorClass = ErrorClass.INTERNAL
    status_code: int = 500

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> dict:
        return {
            "type": self.error_class.value,
            "title": self.__class__.__name__,
            "status": self.status_code,
            "detail": self.message,
            **self.detail,
        }


class ModelAPIError(MixCutError):
    error_class = ErrorClass.MODEL_API
    status_code = 502

    def __init__(self, provider: str, message: str, status_code: int | None = None) -> None:
        super().__init__(message, {"provider": provider})
        if status_code is not None:
            self.status_code = status_code


class ModelOutputError(MixCutError):
    error_class = ErrorClass.MODEL_OUTPUT
    status_code = 422

    def __init__(self, message: str, raw_output: str | None = None) -> None:
        super().__init__(message, {"raw_output_snippet": (raw_output or "")[:200]})


class FFmpegError(MixCutError):
    error_class = ErrorClass.FFMPEG
    status_code = 500

    def __init__(self, message: str, command: str | None = None, exit_code: int | None = None) -> None:
        super().__init__(message, {"command": command, "exit_code": exit_code})


class AssetError(MixCutError):
    error_class = ErrorClass.ASSET
    status_code = 400

    def __init__(self, message: str, asset_id: str | None = None) -> None:
        super().__init__(message, {"asset_id": asset_id})


class StorageError(MixCutError):
    error_class = ErrorClass.STORAGE
    status_code = 500

    def __init__(self, message: str, key: str | None = None) -> None:
        super().__init__(message, {"key": key})


class NodeTimeoutError(MixCutError):
    error_class = ErrorClass.NODE_TIMEOUT
    status_code = 408

    def __init__(self, node_name: str, timeout_seconds: float) -> None:
        super().__init__(f"Node '{node_name}' exceeded {timeout_seconds}s timeout", {"node": node_name, "timeout_seconds": timeout_seconds})


class MaxIterationsExceededError(MixCutError):
    error_class = ErrorClass.MAX_ITERATIONS
    status_code = 422

    def __init__(self, node_name: str, max_iterations: int) -> None:
        super().__init__(f"Node '{node_name}' exceeded {max_iterations} iterations", {"node": node_name, "max_iterations": max_iterations})


class CircuitOpenError(MixCutError):
    error_class = ErrorClass.CIRCUIT_OPEN
    status_code = 503

    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider '{provider}' circuit breaker is open", {"provider": provider})


class AmbiguityError(MixCutError):
    error_class = ErrorClass.AMBIGUITY
    status_code = 300

    def __init__(self, message: str, candidates: list[dict] | None = None) -> None:
        super().__init__(message, {"candidates": candidates or []})


class ValidationError(MixCutError):
    error_class = ErrorClass.VALIDATION
    status_code = 422

    def __init__(self, message: str, fields: dict | None = None) -> None:
        super().__init__(message, {"fields": fields or {}})


class RateLimitError(MixCutError):
    error_class = ErrorClass.RATE_LIMIT
    status_code = 429

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message)


class NotFoundError(MixCutError):
    error_class = ErrorClass.NOT_FOUND
    status_code = 404

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} '{resource_id}' not found", {"resource": resource, "id": resource_id})