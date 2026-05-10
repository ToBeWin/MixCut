"""Job schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from backend.schemas.base import TimestampedModel
from backend.schemas.user_goal import UserGoal


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PENDING_REVIEW = "pending_review"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class JobCreate(TimestampedModel):
    project_id: str
    goal: UserGoal = Field(default_factory=UserGoal)
    asset_ids: list[str] = Field(default_factory=list)


class Job(TimestampedModel):
    id: str
    project_id: str
    goal: UserGoal = Field(default_factory=UserGoal)
    status: JobStatus = JobStatus.QUEUED
    progress: float = Field(default=0.0, ge=0, le=1)
    current_step: str | None = None
    output_path: str | None = None
    edit_script: dict | None = None
    error: str | None = None

