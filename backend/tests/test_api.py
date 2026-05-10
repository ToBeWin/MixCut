from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.database import Base, _session_factory_holder
from backend.main import create_app


@pytest_asyncio.fixture(scope="module")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    _session_factory_holder.set(factory)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestProjectsAPI:
    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient):
        response = await client.post("/api/v1/projects", json={"name": "Test Project", "description": "A test"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)

    @pytest.mark.asyncio
    async def test_get_project(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/projects", json={"name": "GetTest"})
        project_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "GetTest"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/projects/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/projects", json={"name": "ToUpdate"})
        project_id = create_resp.json()["id"]
        response = await client.patch(f"/api/v1/projects/{project_id}", json={"name": "Updated", "description": "New desc"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_project(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/projects", json={"name": "ToDelete"})
        project_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204
        get_resp = await client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 404


class TestModelsAPI:
    @pytest.mark.asyncio
    async def test_list_models(self, client: AsyncClient):
        response = await client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200