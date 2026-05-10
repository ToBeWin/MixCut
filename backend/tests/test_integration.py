"""Integration tests for MixCut API and agent pipeline.

These tests exercise the full request lifecycle without external services.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, _session_factory_holder, get_db

# Import models so they register with Base.metadata for create_all
import backend.models.project  # noqa: F401
import backend.models.job  # noqa: F401
import backend.models.asset  # noqa: F401


@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def integration_engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def client(integration_engine) -> AsyncClient:
    test_session_factory = async_sessionmaker(integration_engine, expire_on_commit=False)
    _session_factory_holder.set(test_session_factory)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Patch lifespan to skip create_all_tables (tables already exist)
    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    # Patch asyncio.create_task to prevent background jobs from running
    # (they use _get_session_factory directly, bypassing our override)
    import asyncio
    _orig_create_task = asyncio.create_task
    _background_tasks = []
    def _capture_create_task(coro, **kwargs):
        task = _orig_create_task(coro, **kwargs)
        _background_tasks.append(task)
        return task

    from backend.main import create_app
    app = create_app()
    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("backend.api.jobs._run_job_background", new_callable=AsyncMock):
            yield ac

    app.dependency_overrides.clear()
    _session_factory_holder.clear()


class TestProjectLifecycle:
    """Full project lifecycle: create → list → get → update → delete."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, client: AsyncClient):
        # Create
        resp = await client.post("/api/v1/projects", json={"name": "Test Project", "description": "Integration test"})
        assert resp.status_code == 201
        project = resp.json()
        project_id = project["id"]
        assert project["name"] == "Test Project"

        # List
        resp = await client.get("/api/v1/projects")
        assert resp.status_code == 200
        projects = resp.json()["projects"]
        assert any(p["id"] == project_id for p in projects)

        # Get
        resp = await client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Project"

        # Update
        resp = await client.patch(f"/api/v1/projects/{project_id}", json={"name": "Updated", "description": "Changed"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

        # Delete
        resp = await client.delete(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 204

        # Verify deleted
        resp = await client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 404


class TestJobLifecycle:
    """Job lifecycle: create project → create job → get → list → cancel."""

    @pytest.mark.asyncio
    async def test_job_flow(self, client: AsyncClient):
        # Create project
        resp = await client.post("/api/v1/projects", json={"name": "Job Test"})
        project_id = resp.json()["id"]

        # Create job
        goal = {
            "prompt": "Make a short product video",
            "platform": "douyin",
            "aspect_ratio": "9:16",
            "style": "lively",
            "target_duration": 30,
            "subtitle_requested": True,
            "voiceover_requested": False,
            "bgm_requested": False,
        }
        resp = await client.post("/api/v1/jobs", json={"project_id": project_id, "goal": goal, "asset_ids": []})
        assert resp.status_code == 201
        job = resp.json()
        job_id = job["id"]
        assert job["status"] == "queued"

        # Get job
        resp = await client.get(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

        # List jobs
        resp = await client.get(f"/api/v1/jobs/project/{project_id}")
        assert resp.status_code == 200
        jobs = resp.json()
        assert any(j["id"] == job_id for j in jobs)

        # Cancel job
        resp = await client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_job_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_job_output_not_found(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": "Output Test"})
        project_id = resp.json()["id"]
        goal = {"prompt": "test", "platform": "douyin", "style": "lively", "target_duration": 10, "aspect_ratio": "9:16"}
        resp = await client.post("/api/v1/jobs", json={"project_id": project_id, "goal": goal, "asset_ids": []})
        job_id = resp.json()["id"]
        resp = await client.get(f"/api/v1/jobs/{job_id}/output")
        assert resp.status_code == 404


class TestModelEndpoints:
    """Model provider and route endpoints."""

    @pytest.mark.asyncio
    async def test_list_models(self, client: AsyncClient):
        resp = await client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        resp = await client.get("/metrics")
        assert resp.status_code == 200


class TestAssetEndpoints:
    """Asset upload and management."""

    @pytest.mark.asyncio
    async def test_list_assets_empty(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": "Asset Test"})
        project_id = resp.json()["id"]
        resp = await client.get(f"/api/v1/assets/project/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["assets"] == []

    @pytest.mark.asyncio
    async def test_upload_invalid_type(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": "Upload Test"})
        project_id = resp.json()["id"]
        resp = await client.post(
            f"/api/v1/assets/project/{project_id}/upload",
            files={"file": ("test.txt", b"not a video", "text/plain")},
        )
        assert resp.status_code == 400


class TestSSEEndpoint:
    """SSE event streaming."""

    @pytest.mark.asyncio
    async def test_events_endpoint_exists(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": "SSE Test"})
        project_id = resp.json()["id"]
        goal = {"prompt": "test", "platform": "douyin", "style": "lively", "target_duration": 10, "aspect_ratio": "9:16"}
        resp = await client.post("/api/v1/jobs", json={"project_id": project_id, "goal": goal, "asset_ids": []})
        job_id = resp.json()["id"]
        # Just verify the endpoint exists and returns streaming response
        resp = await client.get(f"/api/v1/jobs/{job_id}/events")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
