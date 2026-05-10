"""Async database session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import get_settings
from backend.models.base import Base

_engine = None
_session_factory = None


class _SessionFactoryHolder:
    __slots__ = ("_override",)

    def __init__(self) -> None:
        self._override: async_sessionmaker[AsyncSession] | None = None

    def set(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._override = factory

    def get(self) -> async_sessionmaker[AsyncSession] | None:
        return self._override

    def clear(self) -> None:
        self._override = None


_session_factory_holder = _SessionFactoryHolder()


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def _get_session_factory():
    override = _session_factory_holder.get()
    if override is not None:
        return override
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables() -> None:
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)