"""Job business logic - extracted from API layer."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.errors import NotFoundError, RateLimitError, ValidationError
from backend.models.job import RenderJob
from backend.observability.logging import get_logger
from backend.schemas.job import Job as JobSchema, JobStatus
from backend.schemas.user_goal import UserGoal
from backend.workers.progress import ProgressEvent, publish_event

logger = get_logger(__name__)


def _to_schema(job: RenderJob) -> JobSchema:
    goal_data = job.goal if isinstance(job.goal, dict) else {}
    return JobSchema(
        id=job.id,
        project_id=job.project_id,
        goal=UserGoal(**goal_data),
        status=JobStatus(job.status),
        progress=job.progress,
        current_step=job.current_step,
        output_path=job.output_path,
        edit_script=job.edit_script,
        error=job.error,
    )


async def create_job(db: AsyncSession, project_id: str, goal: UserGoal, asset_ids: list[str]) -> JobSchema:
    from backend.config import get_settings

    settings = get_settings()

    running_count = await db.execute(
        select(RenderJob).where(
            RenderJob.project_id == project_id,
            RenderJob.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]),
        )
    )
    active_jobs = running_count.scalars().all()
    if len(active_jobs) >= settings.max_concurrent_jobs_per_user:
        raise RateLimitError(
            f"Too many active jobs ({len(active_jobs)}/{settings.max_concurrent_jobs_per_user}). "
            "Please wait for existing jobs to complete or cancel one."
        )

    goal_data = goal.model_dump()
    job = RenderJob(
        id=str(uuid4()),
        project_id=project_id,
        goal=goal_data,
        status=JobStatus.QUEUED.value,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    try:
        from backend.workers.tasks import run_edit_job_task
        if run_edit_job_task is not None:
            run_edit_job_task.delay(job.id, project_id, goal.model_dump(), asset_ids)
            logger.info("job_dispatched_celery", job_id=job.id)
        else:
            raise ImportError
    except ImportError:
        logger.info("job_dispatched_asyncio", job_id=job.id)
        from backend.api.jobs import _run_job_background
        asyncio.create_task(_run_job_background(job.id, project_id, goal, asset_ids))

    return _to_schema(job)


async def get_job(db: AsyncSession, job_id: str) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    return _to_schema(job)


async def list_jobs(db: AsyncSession, project_id: str) -> list[JobSchema]:
    query = select(RenderJob).where(RenderJob.project_id == project_id).order_by(RenderJob.created_at.desc())
    result = await db.execute(query)
    jobs = result.scalars().all()
    return [_to_schema(j) for j in jobs]


async def cancel_job(db: AsyncSession, job_id: str) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    job.status = JobStatus.CANCELED.value
    job.current_step = "canceled"
    await db.flush()
    await db.refresh(job)
    publish_event(ProgressEvent(job_id=job.id, event="canceled", progress=0.0, message="Job canceled"))
    return _to_schema(job)


async def pause_job(db: AsyncSession, job_id: str) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    job.status = JobStatus.PENDING_REVIEW.value
    await db.flush()
    await db.refresh(job)
    return _to_schema(job)


async def resume_job(db: AsyncSession, job_id: str) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    if job.status != JobStatus.PENDING_REVIEW.value:
        raise ValidationError("Job is not pending review")

    async def _resume():
        from backend.database import _get_session_factory
        from backend.agent.graph import resume_graph

        sf = _get_session_factory()
        try:
            result = await resume_graph(job_id, action="approve")
            output_path = result.get("final_output_path") or result.get("current_output_path")
            async with sf() as db2:
                j = await db2.get(RenderJob, job_id)
                if j is None:
                    return
                j.status = JobStatus.SUCCEEDED.value
                j.progress = 1.0
                j.current_step = "completed"
                j.output_path = output_path
                await db2.commit()
            publish_event(ProgressEvent(job_id=job_id, event="approved", progress=1.0, message="Job approved and exported"))
        except Exception:
            logger.exception("resume_failed", job_id=job_id)
            async with sf() as db2:
                j = await db2.get(RenderJob, job_id)
                if j is not None:
                    j.status = JobStatus.FAILED.value
                    j.current_step = "failed"
                    await db2.commit()
            publish_event(ProgressEvent(job_id=job_id, event="failed", progress=0.0, message="Resume failed"))

    asyncio.create_task(_resume())

    job.status = JobStatus.RUNNING.value
    job.current_step = "resuming"
    await db.flush()
    await db.refresh(job)
    return _to_schema(job)


async def correct_job(db: AsyncSession, job_id: str, correction_text: str) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    if job.status != JobStatus.PENDING_REVIEW.value:
        raise ValidationError("Job is not pending review")

    async def _correct():
        from backend.database import _get_session_factory
        from backend.agent.graph import resume_graph

        sf = _get_session_factory()
        try:
            result = await resume_graph(job_id, action="correct", correction_text=correction_text)
            output_path = result.get("final_output_path") or result.get("current_output_path")
            pending = result.get("pending_human_input", False)

            async with sf() as db2:
                j = await db2.get(RenderJob, job_id)
                if j is None:
                    return
                j.status = JobStatus.PENDING_REVIEW.value if pending else JobStatus.SUCCEEDED.value
                j.progress = 1.0
                j.current_step = "completed" if not pending else "review"
                j.output_path = output_path
                if result.get("edit_script"):
                    es = result["edit_script"]
                    j.edit_script = es.model_dump() if hasattr(es, 'model_dump') else es
                await db2.commit()

            final_event = "waiting_review" if pending else "completed"
            publish_event(ProgressEvent(job_id=job_id, event=final_event, progress=1.0, message="Correction applied"))
        except Exception:
            logger.exception("correct_failed", job_id=job_id)
            async with sf() as db2:
                j = await db2.get(RenderJob, job_id)
                if j is not None:
                    j.status = JobStatus.FAILED.value
                    j.current_step = "failed"
                    await db2.commit()
            publish_event(ProgressEvent(job_id=job_id, event="failed", progress=0.0, message="Correction failed"))

    asyncio.create_task(_correct())

    job.status = JobStatus.RUNNING.value
    job.current_step = "correcting"
    await db.flush()
    await db.refresh(job)
    return _to_schema(job)
