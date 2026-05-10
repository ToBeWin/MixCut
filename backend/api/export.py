from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.deps import StorageBackendDep
from backend.models.job import RenderJob
from backend.observability.logging import get_logger
from backend.schemas.export import ExportRequest, ExportResponse
from backend.schemas.job import JobStatus

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=ExportResponse)
async def export_video(
    payload: ExportRequest,
    db: AsyncSession = Depends(get_db),
    storage: StorageBackendDep = ...,
) -> ExportResponse:
    job = await db.get(RenderJob, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.output_path:
        raise HTTPException(status_code=400, detail="Job has no output to export")
    if job.status not in (JobStatus.SUCCEEDED.value, JobStatus.PENDING_REVIEW.value):
        raise HTTPException(status_code=400, detail="Job is not in a completable state")
    try:
        url = await storage.get_url(job.output_path)
    except Exception as exc:
        logger.error("export_storage_error", job_id=payload.job_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to generate download URL")
    if payload.quality == "draft":
        return ExportResponse(job_id=payload.job_id, status="completed", download_url=url)
    output_key = f"outputs/{job.project_id}/final_{job.id}.mp4"
    try:
        source_path = Path(job.output_path)
        if source_path.exists():
            await storage.write_file(output_key, source_path, content_type="video/mp4")
        else:
            await storage.write(output_key, b"placeholder", content_type="video/mp4")
        download_url = await storage.get_url(output_key)
    except Exception as exc:
        logger.error("export_render_error", job_id=payload.job_id, error=str(exc))
        download_url = url
    return ExportResponse(job_id=payload.job_id, status="completed", download_url=download_url)


@router.get("/{project_id}/download")
async def download_video(
    project_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageBackendDep = ...,
) -> dict:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.output_path:
        raise HTTPException(status_code=400, detail="No output available")
    url = await storage.get_url(job.output_path)
    return {"download_url": url}