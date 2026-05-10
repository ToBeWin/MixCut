from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.deps import SettingsDep, StorageBackendDep
from backend.models.asset import VideoAsset
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.asset import Asset as AssetSchema
from backend.schemas.asset import AssetList, AssetStatus
from backend.tools.ffmpeg.commands import FFmpegCommand, poster_thumbnail
from backend.tools.ffmpeg.probe import probe_video
from backend.tools.ffmpeg.runner import run_ffmpeg

logger = get_logger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/x-matroska",
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.get("/project/{project_id}", response_model=AssetList)
async def list_project_assets(project_id: str, db: AsyncSession = Depends(get_db)) -> AssetList:
    result = await db.execute(select(VideoAsset).where(VideoAsset.project_id == project_id))
    assets = result.scalars().all()
    return AssetList(project_id=project_id, assets=[AssetSchema.model_validate(a.__dict__) for a in assets])


@router.post("/project/{project_id}/upload", response_model=AssetSchema, status_code=201)
async def upload_asset(
    project_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    settings: SettingsDep = ...,
    storage: StorageBackendDep = ...,
) -> AssetSchema:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {file.content_type}")
    is_image = bool(file.content_type and file.content_type.startswith("image/"))
    asset_id = str(uuid.uuid4())
    ext = Path(file.filename or ("image.jpg" if is_image else "video.mp4")).suffix
    storage_key = f"assets/{project_id}/{asset_id}{ext}"
    content = await file.read()
    await storage.write(storage_key, content, content_type=file.content_type or ("image/jpeg" if is_image else "video/mp4"))
    temp_dir = Path(settings.storage_root) / "temp" / asset_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / f"original{ext}"
    temp_file.write_bytes(content)
    with span("probe_video", {"asset_id": asset_id}):
        try:
            probe = await probe_video(str(temp_file))
        except Exception:
            logger.warning("probe_failed", asset_id=asset_id)
            probe = None
    poster_key = f"assets/{project_id}/{asset_id}_poster.jpg"
    poster_path_value: str | None = storage_key if is_image else None
    if not is_image:
        with span("poster_thumbnail", {"asset_id": asset_id}):
            try:
                poster_cmd = poster_thumbnail(str(temp_file), str(temp_dir / "poster.jpg"))
                await run_ffmpeg(poster_cmd)
                poster_data = (temp_dir / "poster.jpg").read_bytes()
                await storage.write(poster_key, poster_data, content_type="image/jpeg")
                poster_path_value = poster_key
            except Exception:
                logger.warning("poster_failed", asset_id=asset_id)
    proxy_key: str | None = None
    if not is_image:
        with span("proxy_generation", {"asset_id": asset_id}):
            try:
                proxy_cmd = FFmpegCommand(["-i", str(temp_file), "-vf", "scale=-2:240", "-an", "-c:v", "libx264", "-crf", "28", str(temp_dir / "proxy.mp4")])
                await run_ffmpeg(proxy_cmd, timeout=120)
                proxy_data = (temp_dir / "proxy.mp4").read_bytes()
                proxy_key = f"proxies/{asset_id}_240p.mp4"
                await storage.write(proxy_key, proxy_data, content_type="video/mp4")
            except Exception:
                logger.warning("proxy_failed", asset_id=asset_id)
        with span("keyframe_extraction", {"asset_id": asset_id}):
            try:
                from backend.tools.keyframe import extract_keyframes

                keyframe_dir = settings.storage_root / "keyframes" / asset_id
                await extract_keyframes(str(temp_file), str(keyframe_dir), interval_seconds=2.0, max_frames=30)
            except Exception:
                logger.warning("keyframe_extraction_failed", asset_id=asset_id)
    shutil.rmtree(temp_dir, ignore_errors=True)
    asset = VideoAsset(
        id=asset_id,
        project_id=project_id,
        filename=file.filename or f"{asset_id}{ext}",
        storage_path=storage_key,
        content_type=file.content_type or "video/mp4",
        status=AssetStatus.UPLOADED.value,
        duration_seconds=probe.duration_seconds if probe else None,
        width=probe.width if probe else None,
        height=probe.height if probe else None,
        fps=probe.fps if probe else None,
        codec=probe.video_codec if probe else None,
        audio_present=probe.audio_present if probe else False,
        audio_codec=probe.audio_codec if probe else None,
        poster_path=poster_path_value,
        proxy_path=proxy_key,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return AssetSchema.model_validate(asset.__dict__)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: str, db: AsyncSession = Depends(get_db)) -> None:
    asset = await db.get(VideoAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(asset)


@router.get("/{asset_id}/poster")
async def get_asset_poster(asset_id: str, db: AsyncSession = Depends(get_db), settings: SettingsDep = ...):
    """Serve the poster/thumbnail image for an asset."""
    from fastapi.responses import Response

    asset = await db.get(VideoAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Try to read from storage
    if asset.poster_path:
        poster_file = Path(settings.storage_root) / asset.poster_path
        if poster_file.exists():
            return Response(poster_file.read_bytes(), media_type="image/jpeg")

    # Fallback: extract frame at t=0
    storage_path = Path(settings.storage_root) / asset.storage_path
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Asset file not found")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = poster_thumbnail(str(storage_path), tmp_path, timestamp=0.0, width=320)
        await run_ffmpeg(cmd, timeout=30)
        data = Path(tmp_path).read_bytes()
        return Response(data, media_type="image/jpeg")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to extract frame")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/{asset_id}/frame")
async def get_asset_frame(asset_id: str, time: float = 0.0, db: AsyncSession = Depends(get_db), settings: SettingsDep = ...):
    """Extract a frame at a specific timestamp. Returns JPEG."""
    from fastapi.responses import Response
    import hashlib

    asset = await db.get(VideoAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    storage_path = Path(settings.storage_root) / asset.storage_path
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Asset file not found")

    # Check cache
    cache_key = hashlib.md5(f"{asset_id}:{time:.1f}".encode()).hexdigest()
    cache_dir = Path(settings.storage_root) / "temp" / "frames"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{cache_key}.jpg"

    if cache_path.exists():
        return Response(cache_path.read_bytes(), media_type="image/jpeg")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = poster_thumbnail(str(storage_path), tmp_path, timestamp=time, width=320)
        await run_ffmpeg(cmd, timeout=30)
        data = Path(tmp_path).read_bytes()
        cache_path.write_bytes(data)
        return Response(data, media_type="image/jpeg")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to extract frame")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
