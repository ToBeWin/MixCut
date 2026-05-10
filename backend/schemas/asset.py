"""Asset schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from backend.schemas.base import TimestampedModel


class AssetStatus(str, Enum):
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    READY = "ready"
    FAILED = "failed"


class AssetCreate(TimestampedModel):
    project_id: str
    filename: str
    storage_path: str
    content_type: str = "video/mp4"


class Asset(TimestampedModel):
    id: str
    project_id: str
    filename: str
    storage_path: str
    content_type: str = "video/mp4"
    status: AssetStatus = AssetStatus.UPLOADED
    duration_seconds: float | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    fps: float | None = Field(default=None, ge=0)
    codec: str | None = None
    audio_present: bool = False
    audio_codec: str | None = None
    poster_path: str | None = None
    proxy_path: str | None = None


class AssetList(TimestampedModel):
    project_id: str
    assets: list[Asset]
