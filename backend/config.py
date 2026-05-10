"""Application settings for the MixCut backend.

Settings are intentionally cheap to import: no network checks, database
connections, or filesystem provisioning happens here.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "MixCut API"
    environment: Environment = Field(default="development", validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"))
    debug: bool = True
    api_prefix: str = Field(default="/api/v1", validation_alias=AliasChoices("API_PREFIX", "MIXCUT_API_PREFIX"))
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS", "MIXCUT_CORS_ORIGINS"),
    )

    storage_root: Path = Field(default=Path("storage"), validation_alias=AliasChoices("STORAGE_PATH", "MIXCUT_STORAGE_ROOT"))
    output_root: Path = Field(default=Path("storage/outputs"), validation_alias=AliasChoices("OUTPUT_PATH", "MIXCUT_OUTPUT_ROOT"))
    storage_backend: Literal["local", "s3"] = Field(default="local", validation_alias=AliasChoices("STORAGE_BACKEND", "MIXCUT_STORAGE_BACKEND"))
    s3_endpoint: str | None = Field(default=None, validation_alias=AliasChoices("S3_ENDPOINT", "MIXCUT_S3_ENDPOINT"))
    s3_bucket: str = Field(default="mixcut", validation_alias=AliasChoices("S3_BUCKET", "MIXCUT_S3_BUCKET"))
    s3_access_key: str | None = Field(default=None, validation_alias=AliasChoices("S3_ACCESS_KEY", "MIXCUT_S3_ACCESS_KEY"))
    s3_secret_key: str | None = Field(default=None, validation_alias=AliasChoices("S3_SECRET_KEY", "MIXCUT_S3_SECRET_KEY"))
    s3_region: str = Field(default="us-east-1", validation_alias=AliasChoices("S3_REGION", "MIXCUT_S3_REGION"))

    default_model_provider: str = Field(default="mock", validation_alias=AliasChoices("DEFAULT_MODEL_PROVIDER", "MIXCUT_DEFAULT_MODEL_PROVIDER"))
    anthropic_api_key: str | None = Field(default=None, validation_alias=AliasChoices("ANTHROPIC_API_KEY", "MIXCUT_ANTHROPIC_API_KEY"))
    openai_api_key: str | None = Field(default=None, validation_alias=AliasChoices("OPENAI_API_KEY", "MIXCUT_OPENAI_API_KEY"))
    google_api_key: str | None = Field(default=None, validation_alias=AliasChoices("GOOGLE_API_KEY", "MIXCUT_GOOGLE_API_KEY"))
    dashscope_api_key: str | None = Field(default=None, validation_alias=AliasChoices("DASHSCOPE_API_KEY", "MIXCUT_DASHSCOPE_API_KEY"))
    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias=AliasChoices("OLLAMA_BASE_URL", "MIXCUT_OLLAMA_BASE_URL"))
    ollama_default_model: str = Field(default="llama3.3", validation_alias=AliasChoices("OLLAMA_DEFAULT_MODEL", "MIXCUT_OLLAMA_DEFAULT_MODEL"))
    openai_compatible_base_url: str | None = Field(default=None, validation_alias=AliasChoices("OPENAI_COMPATIBLE_BASE_URL", "DASHSCOPE_API_BASE"))
    openai_compatible_api_key: str | None = Field(default=None, validation_alias=AliasChoices("OPENAI_COMPATIBLE_API_KEY", "DASHSCOPE_API_KEY"))
    openai_compatible_default_model: str = Field(default="gpt-4o-mini", validation_alias=AliasChoices("OPENAI_COMPATIBLE_DEFAULT_MODEL", "MODEL_EDIT_PLANNING"))

    minimax_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MINIMAX_API_KEY"))
    minimax_group_id: str | None = Field(default=None, validation_alias=AliasChoices("MINIMAX_GROUP_ID"))
    volcengine_tts_app_id: str | None = Field(default=None, validation_alias=AliasChoices("VOLCENGINE_TTS_APP_ID"))
    volcengine_tts_access_token: str | None = Field(default=None, validation_alias=AliasChoices("VOLCENGINE_TTS_ACCESS_TOKEN"))

    agent_max_iterations: int = 10
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_seconds: float = 60.0

    max_concurrent_jobs_per_user: int = Field(
        default=3, validation_alias=AliasChoices("MAX_CONCURRENT_JOBS_PER_USER")
    )
    max_model_concurrent_calls: int = Field(
        default=5, validation_alias=AliasChoices("MAX_MODEL_CONCURRENT_CALLS")
    )
    api_rate_limit_default: int = Field(
        default=100, validation_alias=AliasChoices("API_RATE_LIMIT_DEFAULT")
    )
    api_rate_limit_jobs: int = Field(
        default=5, validation_alias=AliasChoices("API_RATE_LIMIT_JOBS")
    )
    api_rate_limit_uploads: int = Field(
        default=10, validation_alias=AliasChoices("API_RATE_LIMIT_UPLOADS")
    )

    database_url: str = Field(
        default="postgresql+asyncpg://mixcut:mixcut@localhost:5432/mixcut",
        validation_alias=AliasChoices("DATABASE_URL", "MIXCUT_DATABASE_URL"),
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "MIXCUT_REDIS_URL"),
    )

    otel_exporter_otlp_endpoint: str | None = Field(
        default=None, validation_alias=AliasChoices("OTEL_EXPORTER_OTLP_ENDPOINT")
    )
    prometheus_metrics_enabled: bool = Field(
        default=True, validation_alias=AliasChoices("PROMETHEUS_METRICS_ENABLED")
    )
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for dependency injection."""

    return Settings()
