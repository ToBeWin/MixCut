"""EditScript ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class EditScript(TimestampMixin, Base):
    __tablename__ = "edit_scripts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    target_platform: Mapped[str] = mapped_column(String(32), nullable=False, default="custom")
    target_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    aspect_ratio: Mapped[str] = mapped_column(String(8), nullable=False, default="9:16")
    segments: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    bgm_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    voiceover_script: Mapped[str | None] = mapped_column(Text, nullable=True)
    planning_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
