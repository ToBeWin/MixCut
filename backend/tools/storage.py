"""Storage abstraction: local filesystem and S3-compatible backends."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
import anyio

if TYPE_CHECKING:
    pass

log = structlog.get_logger()


class StorageBackend(ABC):
    @abstractmethod
    async def write(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...

    @abstractmethod
    async def write_file(self, key: str, source_path: Path, content_type: str = "application/octet-stream") -> str: ...

    @abstractmethod
    async def read(self, key: str) -> bytes: ...

    @abstractmethod
    async def read_file(self, key: str, dest_path: Path) -> Path: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def write(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._resolve(key)
        await anyio.run_sync_in_worker_thread(path.write_bytes, data)
        log.debug("storage.local.write", key=key, size=len(data))
        return key

    async def write_file(self, key: str, source_path: Path, content_type: str = "application/octet-stream") -> str:
        path = self._resolve(key)
        await anyio.run_sync_in_worker_thread(shutil.copy2, str(source_path), str(path))
        log.debug("storage.local.write_file", key=key, source=str(source_path))
        return key

    async def read(self, key: str) -> bytes:
        path = self.root / key
        data = await anyio.run_sync_in_worker_thread(path.read_bytes)
        log.debug("storage.local.read", key=key, size=len(data))
        return data

    async def read_file(self, key: str, dest_path: Path) -> Path:
        src = self.root / key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        await anyio.run_sync_in_worker_thread(shutil.copy2, str(src), str(dest_path))
        log.debug("storage.local.read_file", key=key, dest=str(dest_path))
        return dest_path

    async def delete(self, key: str) -> None:
        path = self.root / key
        try:
            await anyio.run_sync_in_worker_thread(path.unlink, missing_ok=True)
        except FileNotFoundError:
            pass
        log.debug("storage.local.delete", key=key)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        return str((self.root / key).resolve())

    async def exists(self, key: str) -> bool:
        path = self.root / key
        return await anyio.run_sync_in_worker_thread(path.exists)


class S3StorageBackend(StorageBackend):
    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ) -> None:
        try:
            import aioboto3  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "aioboto3 is required for S3StorageBackend. Install with: pip install mixcut-backend[s3]"
            ) from exc
        self.endpoint = endpoint
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self._session = None

    def _get_session(self):
        import aioboto3

        if self._session is None:
            self._session = aioboto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
        return self._session

    async def write(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            await s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        log.debug("storage.s3.write", key=key, size=len(data))
        return key

    async def write_file(self, key: str, source_path: Path, content_type: str = "application/octet-stream") -> str:
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            await s3.upload_file(str(source_path), self.bucket, key, ExtraArgs={"ContentType": content_type})
        log.debug("storage.s3.write_file", key=key, source=str(source_path))
        return key

    async def read(self, key: str) -> bytes:
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            resp = await s3.get_object(Bucket=self.bucket, Key=key)
            data = await resp["Body"].read()
        log.debug("storage.s3.read", key=key, size=len(data))
        return data

    async def read_file(self, key: str, dest_path: Path) -> Path:
        session = self._get_session()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            await s3.download_file(self.bucket, key, str(dest_path))
        log.debug("storage.s3.read_file", key=key, dest=str(dest_path))
        return dest_path

    async def delete(self, key: str) -> None:
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
        log.debug("storage.s3.delete", key=key)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        return url

    async def exists(self, key: str) -> bool:
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint) as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except s3.exceptions.ClientError:
                return False


def build_storage_backend(settings) -> StorageBackend:
    if settings.storage_backend == "s3":
        if not settings.s3_access_key or not settings.s3_secret_key:
            raise ValueError("S3 storage requires s3_access_key and s3_secret_key")
        return S3StorageBackend(
            endpoint=settings.s3_endpoint or "",
            bucket=settings.s3_bucket,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region=settings.s3_region,
        )
    return LocalStorageBackend(root=settings.storage_root)