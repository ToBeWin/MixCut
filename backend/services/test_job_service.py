"""Tests for job service layer."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.database import Base
from backend.errors import NotFoundError, RateLimitError
from backend.models.job import RenderJob
from backend.schemas.job import JobStatus
from backend.schemas.user_goal import UserGoal
from backend.services.job_service import _to_schema


@pytest_asyncio.fixture
async def db_engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


def make_goal() -> UserGoal:
    return UserGoal(
        prompt="Test",
        platform="douyin",
        aspect_ratio="9:16",
        style="lively",
        target_duration=30,
    )


class TestToSchema:
    def test_converts_render_job(self):
        job = RenderJob(
            id="test-id",
            project_id="proj-1",
            goal={"prompt": "Test", "platform": "douyin", "aspect_ratio": "9:16", "style": "lively", "target_duration": 30},
            status=JobStatus.QUEUED.value,
            progress=0.0,
        )
        schema = _to_schema(job)
        assert schema.id == "test-id"
        assert schema.project_id == "proj-1"
        assert schema.status == JobStatus.QUEUED

    def test_handles_non_dict_goal(self):
        job = RenderJob(
            id="test-id",
            project_id="proj-1",
            goal="invalid",  # not a dict
            status=JobStatus.QUEUED.value,
            progress=0.0,
        )
        schema = _to_schema(job)
        assert schema.id == "test-id"


class TestJobServiceDB:
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, db: AsyncSession):
        from backend.services.job_service import get_job
        with pytest.raises(NotFoundError):
            await get_job(db, "nonexistent")

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, db: AsyncSession):
        from backend.services.job_service import cancel_job
        with pytest.raises(NotFoundError):
            await cancel_job(db, "nonexistent")

    @pytest.mark.asyncio
    async def test_pause_job_not_found(self, db: AsyncSession):
        from backend.services.job_service import pause_job
        with pytest.raises(NotFoundError):
            await pause_job(db, "nonexistent")

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, db: AsyncSession):
        from backend.services.job_service import list_jobs
        result = await list_jobs(db, "nonexistent-project")
        assert result == []
