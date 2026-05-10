"""Persisted task-level model routing overrides."""

from __future__ import annotations

import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class ModelRouteConfig(TimestampMixin, Base):
    __tablename__ = "model_routes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    task: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fallback_providers: Mapped[str] = mapped_column(Text, nullable=False, default="")
