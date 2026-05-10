"""Export schemas."""

from __future__ import annotations

from typing import Literal

from backend.schemas.base import StrictBaseModel


class ExportRequest(StrictBaseModel):
    project_id: str
    job_id: str
    format: Literal["mp4", "mov"] = "mp4"
    quality: Literal["draft", "standard", "high"] = "standard"


class ExportResponse(StrictBaseModel):
    job_id: str
    status: str
    download_url: str | None = None

