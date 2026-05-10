"""Job API endpoints - thin layer over job_service."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import NotFoundError
from backend.models.asset import VideoAsset
from backend.models.job import RenderJob
from backend.observability.logging import get_logger
from backend.schemas.asset import Asset as AssetSchema
from backend.schemas.job import Job as JobSchema, JobCreate, JobStatus
from backend.schemas.user_goal import UserGoal
from backend.services import job_service
from backend.workers.progress import ProgressEvent, publish_event, progress_event_stream

logger = get_logger(__name__)

router = APIRouter()


async def _run_job_background(job_id: str, project_id: str, goal: UserGoal, asset_ids: list[str]) -> None:
    from backend.database import _get_session_factory
    from backend.schemas.agent_state import AgentState
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
    return await job_service.list_jobs(db, project_id)


@router.post("", response_model=JobSchema, status_code=201)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)) -> JobSchema:
    return await job_service.create_job(db, payload.project_id, payload.goal, payload.asset_ids)


@router.get("/{job_id}", response_model=JobSchema)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    return await job_service.get_job(db, job_id)


@router.post("/{job_id}/pause", response_model=JobSchema)
async def pause_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    return await job_service.pause_job(db, job_id)


@router.post("/{job_id}/resume", response_model=JobSchema)
async def resume_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    return await job_service.resume_job(db, job_id)


@router.post("/{job_id}/correct", response_model=JobSchema)
async def correct_job(job_id: str, correction_text: str = "", db: AsyncSession = Depends(get_db)) -> JobSchema:
    return await job_service.correct_job(db, job_id, correction_text)


@router.post("/{job_id}/cancel", response_model=JobSchema)
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSchema:
    return await job_service.cancel_job(db, job_id)


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(progress_event_stream(job_id), media_type="text/event-stream")


@router.get("/{job_id}/output")
async def get_job_output(job_id: str, db: AsyncSession = Depends(get_db)):
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
