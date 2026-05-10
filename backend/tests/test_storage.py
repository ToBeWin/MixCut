"""Tests for storage backends."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import pytest

from backend.tools.storage import LocalStorageBackend, S3StorageBackend, build_storage_backend


class TestLocalStorageBackend:
    @pytest.mark.asyncio
    async def test_write_and_read(self, tmp_path: Path):
        backend = LocalStorageBackend(root=tmp_path)
        with patch("backend.tools.storage.anyio") as mock_anyio:
            mock_anyio.run_sync_in_worker_thread = AsyncMock(side_effect=lambda fn, *args, **kwargs: fn(*args))
            await backend.write("test.txt", b"hello world")
            data = await backend.read("test.txt")
            assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_write_file(self, tmp_path: Path):
        backend = LocalStorageBackend(root=tmp_path)
        src = tmp_path / "source.txt"
        src.write_bytes(b"source data")
        with patch("backend.tools.storage.anyio") as mock_anyio:
            mock_anyio.run_sync_in_worker_thread = AsyncMock(side_effect=lambda fn, *args, **kwargs: fn(*args))
            await backend.write_file("dest.txt", src)
            assert (tmp_path / "dest.txt").read_bytes() == b"source data"

    @pytest.mark.asyncio
    async def test_read_file(self, tmp_path: Path):
        backend = LocalStorageBackend(root=tmp_path)
        (tmp_path / "src.txt").write_bytes(b"file data")
        dest = tmp_path / "output" / "dest.txt"
        with patch("backend.tools.storage.anyio") as mock_anyio:
            mock_anyio.run_sync_in_worker_thread = AsyncMock(side_effect=lambda fn, *args, **kwargs: fn(*args))
            result = await backend.read_file("src.txt", dest)
            assert result == dest
            assert dest.read_bytes() == b"file data"

    @pytest.mark.asyncio
    async def test_delete(self, tmp_path: Path):
        backend = LocalStorageBackend(root=tmp_path)
        with patch("backend.tools.storage.anyio") as mock_anyio:
            mock_anyio.run_sync_in_worker_thread = AsyncMock(side_effect=lambda fn, *args, **kwargs: fn(*args))
            await backend.write("to_delete.txt", b"delete me")
            assert await backend.exists("to_delete.txt")
            await backend.delete("to_delete.txt")
            assert not await backend.exists("to_delete.txt")

    @pytest.mark.asyncio
    async def test_get_url_returns_path(self, tmp_path: Path):
        backend = LocalStorageBackend(root=tmp_path)
        url = await backend.get_url("test.txt")
        assert "test.txt" in url

    @pytest.mark.asyncio
    async def test_exists(self, tmp_path: Path):
        backend = LocalStorageBackend(root=tmp_path)
        with patch("backend.tools.storage.anyio") as mock_anyio:
            mock_anyio.run_sync_in_worker_thread = AsyncMock(side_effect=lambda fn, *args, **kwargs: fn(*args))
            assert not await backend.exists("missing.txt")
            await backend.write("present.txt", b"data")
            assert await backend.exists("present.txt")


class TestS3StorageBackend:
    @pytest.fixture
    def s3_backend(self):
        mock_aioboto3 = MagicMock()
        with patch.dict("sys.modules", {"aioboto3": mock_aioboto3}):
            return S3StorageBackend(
                endpoint="http://localhost:9000",
                bucket="test-bucket",
                access_key="test",
                secret_key="test",
                region="us-east-1",
            )

    def test_init_requires_aioboto3(self):
        with patch.dict("sys.modules", {"aioboto3": None}):
            with pytest.raises(RuntimeError, match="aioboto3 is required"):
                S3StorageBackend(
                    endpoint="http://localhost:9000",
                    bucket="test",
                    access_key="test",
                    secret_key="test",
                )

    def test_build_storage_backend_local(self):
        settings = MagicMock(storage_backend="local", storage_root=Path("/tmp/test"))
        backend = build_storage_backend(settings)
        assert isinstance(backend, LocalStorageBackend)

    def test_build_storage_backend_s3(self):
        settings = MagicMock(
            storage_backend="s3",
            s3_endpoint="http://localhost:9000",
            s3_bucket="test",
            s3_access_key="key",
            s3_secret_key="secret",
            s3_region="us-east-1",
        )
        mock_aioboto3 = MagicMock()
        with patch.dict("sys.modules", {"aioboto3": mock_aioboto3}):
            backend = build_storage_backend(settings)
            assert isinstance(backend, S3StorageBackend)

    def test_build_storage_backend_s3_missing_keys(self):
        settings = MagicMock(
            storage_backend="s3",
            s3_access_key=None,
            s3_secret_key=None,
        )
        with pytest.raises(ValueError, match="S3 storage requires"):
            build_storage_backend(settings)
