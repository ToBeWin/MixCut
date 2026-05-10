"""VideoAsset ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class VideoAsset(TimestampMixin, Base):
    __tablename__ = "assets"

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
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False, default="video/mp4")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    codec: Mapped[str | None] = mapped_column(String(32), nullable=True)
    audio_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    audio_codec: Mapped[str | None] = mapped_column(String(32), nullable=True)
    poster_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    proxy_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="assets")
