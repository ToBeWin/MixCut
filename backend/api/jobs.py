from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import NotFoundError, RateLimitError, ValidationError
from backend.models.asset import VideoAsset
from backend.models.job import RenderJob
from backend.observability.logging import get_logger
from backend.schemas.asset import Asset as AssetSchema
from backend.schemas.job import Job as JobSchema
from backend.schemas.job import JobCreate, JobStatus
from backend.schemas.user_goal import UserGoal
from backend.workers.progress import ProgressEvent, publish_event, progress_event_stream

logger = get_logger(__name__)

router = APIRouter()


async def _run_job_background(job_id: str, project_id: str, goal: UserGoal, asset_ids: list[str]) -> None:
    from backend.database import _get_session_factory
    from backend.schemas.agent_state import AgentState
    from backend.schemas.clip_metadata import ClipMetadata
    from backend.agent.graph import run_graph_once

    session_factory = _get_session_factory()

    try:
        async with session_factory() as db:
            job = await db.get(RenderJob, job_id)
            if job is None:
                return
            job.status = JobStatus.RUNNING.value
            job.current_step = "understand"
            await db.commit()

        publish_event(ProgressEvent(job_id=job_id, event="node_start", progress=0.05, message="Loading assets", node="understand"))

        async with session_factory() as db:
            query = select(VideoAsset).where(VideoAsset.project_id == project_id)
            if asset_ids:
                query = query.where(VideoAsset.id.in_(asset_ids))
            assets_result = await db.execute(query)
            assets = assets_result.scalars().all()
            asset_schemas = [AssetSchema.model_validate(a.__dict__) for a in assets]

        state = AgentState(
            project_id=project_id,
            job_id=job_id,
            assets=asset_schemas,
            user_goal=goal,
            clip_metadata={},
            edit_script=None,
            correction_history=[],
            current_output_path=None,
            subtitle_path=None,
            node_outputs={},
            node_errors={},
            iteration_count={},
            pending_human_input=False,
            final_output_path=None,
        )

        state = await run_graph_once(state)

        output_path = state.final_output_path or state.current_output_path

        async with session_factory() as db:
            job = await db.get(RenderJob, job_id)
            if job is None:
                return
            job.status = JobStatus.PENDING_REVIEW.value if state.pending_human_input else JobStatus.SUCCEEDED.value
            job.progress = 1.0
            job.current_step = "completed"
            job.output_path = output_path
            if state.edit_script is not None:
                job.edit_script = state.edit_script.model_dump() if hasattr(state.edit_script, 'model_dump') else state.edit_script
            await db.commit()

        final_event = "waiting_review" if state.pending_human_input else "completed"
        publish_event(ProgressEvent(job_id=job_id, event=final_event, progress=1.0, message="Job completed", node="supervisor"))

    except Exception:
        logger.exception("job_failed", job_id=job_id)
        async with session_factory() as db:
            job = await db.get(RenderJob, job_id)
            if job is not None:
                job.status = JobStatus.FAILED.value
                job.current_step = "failed"
                await db.commit()
        publish_event(ProgressEvent(job_id=job_id, event="failed", progress=0.0, message="Job failed", node="supervisor"))


@router.get("/project/{project_id}", response_model=list[JobSchema])
async def list_jobs(project_id: str, db: AsyncSession = Depends(get_db)) -> list[JobSchema]:
    """List all jobs for a project."""
    query = select(RenderJob).where(RenderJob.project_id == project_id).order_by(RenderJob.created_at.desc())
    result = await db.execute(query)
    jobs = result.scalars().all()
    return [
        JobSchema(
            id=j.id,
            project_id=j.project_id,
            goal=UserGoal(**(j.goal if isinstance(j.goal, dict) else {})),
            status=JobStatus(j.status),
            progress=j.progress,
            current_step=j.current_step,
            output_path=j.output_path,
            edit_script=j.edit_script,
            error=j.error,
        )
        for j in jobs
    ]


@router.post("", response_model=JobSchema, status_code=201)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)) -> JobSchema:
    from backend.config import get_settings
    settings = get_settings()

    # Check per-project concurrent job limit
    running_count = await db.execute(
        select(RenderJob).where(
            RenderJob.project_id == payload.project_id,
            RenderJob.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]),
        )
    )
    active_jobs = running_count.scalars().all()
    if len(active_jobs) >= settings.max_concurrent_jobs_per_user:
        raise RateLimitError(
            f"Too many active jobs ({len(active_jobs)}/{settings.max_concurrent_jobs_per_user}). "
            "Please wait for existing jobs to complete or cancel one."
        )

    goal_data = payload.goal.model_dump()
    job = RenderJob(
        id=str(uuid4()),
        project_id=payload.project_id,
        goal=goal_data,
        status=JobStatus.QUEUED.value,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    try:
        from backend.workers.tasks import run_edit_job_task
        if run_edit_job_task is not None:
            run_edit_job_task.delay(job.id, payload.project_id, payload.goal.model_dump(), payload.asset_ids)
            logger.info("job_dispatched_celery", job_id=job.id)
        else:
            raise ImportError
    except ImportError:
        logger.info("job_dispatched_asyncio", job_id=job.id)
        asyncio.create_task(
            _run_job_background(job.id, payload.project_id, payload.goal, payload.asset_ids)
        )

    return JobSchema(
        id=job.id,
        project_id=job.project_id,
        goal=UserGoal(**(job.goal if isinstance(job.goal, dict) else {})),
        status=JobStatus(job.status),
        progress=job.progress,
        current_step=job.current_step,
        output_path=job.output_path,
        edit_script=job.edit_script,
        error=job.error,
    )


@router.get("/{job_id}", response_model=JobSchema)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
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


@router.post("/{job_id}/pause", response_model=JobSchema)
async def pause_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    job.status = JobStatus.PENDING_REVIEW.value
    await db.flush()
    await db.refresh(job)
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


@router.post("/{job_id}/resume", response_model=JobSchema)
async def resume_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    """Approve and resume a job that is pending review."""
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    if job.status != JobStatus.PENDING_REVIEW.value:
        raise ValidationError("Job is not pending review")

    # Resume graph in background
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


@router.post("/{job_id}/correct", response_model=JobSchema)
async def correct_job(job_id: str, correction_text: str = "", db: AsyncSession = Depends(get_db)) -> JobSchema:
    """Submit a correction for a job that is pending review."""
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    if job.status != JobStatus.PENDING_REVIEW.value:
        raise ValidationError("Job is not pending review")

    # Resume graph with correction in background
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


@router.post("/{job_id}/cancel", response_model=JobSchema)
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    job.status = JobStatus.CANCELED.value
    job.current_step = "canceled"
    await db.flush()
    await db.refresh(job)
    goal_data = job.goal if isinstance(job.goal, dict) else {}
    publish_event(ProgressEvent(job_id=job.id, event="canceled", progress=0.0, message="Job canceled"))
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


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    from fastapi.responses import StreamingResponse

    return StreamingResponse(progress_event_stream(job_id), media_type="text/event-stream")


@router.get("/{job_id}/output")
async def get_job_output(job_id: str, db: AsyncSession = Depends(get_db)):
    """Serve the output video file for a completed job."""
    from pathlib import Path
    from fastapi.responses import FileResponse

    job = await db.get(RenderJob, job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    if not job.output_path:
        raise NotFoundError("Job output", job_id)
    output_path = Path(job.output_path)
    if not output_path.exists():
        raise NotFoundError("Output file", job.output_path)
    return FileResponse(output_path, media_type="video/mp4", filename=f"mixcut_{job_id[:8]}.mp4")
