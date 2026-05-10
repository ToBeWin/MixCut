from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.deps import StorageBackendDep
from backend.errors import NotFoundError, StorageError, ValidationError
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
        raise NotFoundError("Job", payload.job_id)
    if not job.output_path:
        raise ValidationError("Job has no output to export")
    if job.status not in (JobStatus.SUCCEEDED.value, JobStatus.PENDING_REVIEW.value):
        raise ValidationError("Job is not in a completable state")
    try:
        url = await storage.get_url(job.output_path)
    except Exception as exc:
        logger.error("export_storage_error", job_id=payload.job_id, error=str(exc))
        raise StorageError("Failed to generate download URL") from exc
    if payload.quality == "draft":
        return ExportResponse(job_id=payload.job_id, status="completed", download_url=url)
    output_key = f"outputs/{job.project_id}/final_{job.id}.mp4"
    try:
        source_path = Path(job.output_path)
        if not source_path.exists():
            raise NotFoundError("Output file", job.output_path)
        await storage.write_file(output_key, source_path, content_type="video/mp4")
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
        raise NotFoundError("Job", job_id)
    if not job.output_path:
        raise ValidationError("No output available")
    url = await storage.get_url(job.output_path)
    return {"download_url": url}