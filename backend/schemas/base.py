"""Common schema helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrictBaseModel(BaseModel):
    """Base model using Pydantic v2 strict-ish defaults."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, arbitrary_types_allowed=False)


class TimestampedModel(StrictBaseModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


JsonDict = dict[str, Any]

