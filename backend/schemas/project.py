"""Project schemas."""

from __future__ import annotations

from backend.schemas.base import TimestampedModel


class ProjectCreate(TimestampedModel):
    name: str
    description: str | None = None


class Project(TimestampedModel):
    id: str
    name: str
    description: str | None = None
    status: str = "active"


class ProjectList(TimestampedModel):
    projects: list[Project]

