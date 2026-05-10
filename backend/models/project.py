"""Project ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    assets: Mapped[list["VideoAsset"]] = relationship(back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    jobs: Mapped[list["RenderJob"]] = relationship(back_populates="project", cascade="all, delete-orphan", lazy="selectin")
