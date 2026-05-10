"""Celery task definitions for MixCut background jobs.

Jobs are dispatched to Celery workers via Redis broker.
Each task publishes progress events via Redis pub/sub for SSE streaming.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from backend.config import get_settings
from backend.harness.cost_tracker import CostTracker
from backend.observability.logging import get_logger
from backend.schemas.agent_state import AgentState
from backend.workers.progress import ProgressEvent, publish_event

logger = get_logger(__name__)


async def _run_node(state: AgentState, node_name: str, coro_func, **kwargs) -> AgentState:
    """Run a single agent node with progress tracking."""
    publish_event(ProgressEvent(job_id=state.job_id, event="node_start", progress=0.0, message=f"Starting {node_name}", node=node_name))
    try:
        state = await coro_func
        progress_map = {"understand": 0.2, "plan": 0.4, "execute": 0.6, "subtitle": 0.75, "tts": 0.85, "correct": 0.5}
        progress = progress_map.get(node_name, 0.5)
        publish_event(ProgressEvent(job_id=state.job_id, event="node_complete", progress=progress, message=f"Completed {node_name}", node=node_name))
        return state
    except Exception as exc:
        if node_name not in state.node_errors:
            state.node_errors[node_name] = []
        state.node_errors[node_name].append(str(exc))
        publish_event(ProgressEvent(job_id=state.job_id, event="node_error", progress=0.0, message=str(exc), node=node_name))
        raise


def run_edit_job_sync(job_id: str, project_id: str, goal_dict: dict, asset_ids: list[str]) -> None:
    """Synchronous entry point for Celery task.

    Wraps the async graph execution in an event loop since Celery tasks
    are synchronous by default.
    """
    asyncio.run(_run_edit_job_async(job_id, project_id, goal_dict, asset_ids))


async def _run_edit_job_async(job_id: str, project_id: str, goal_dict: dict, asset_ids: list[str]) -> None:
    """Async implementation of the edit job."""
    import time

    from backend.database import _get_session_factory
    from backend.schemas.agent_state import AgentState
    from backend.schemas.asset import Asset as AssetSchema
    from backend.schemas.user_goal import UserGoal
    from backend.schemas.job import JobStatus
    from backend.models.job import RenderJob
    from backend.models.asset import VideoAsset
    from sqlalchemy import select

    session_factory = _get_session_factory()
    job_start = time.monotonic()

    # Prometheus: track active jobs
    try:
        from backend.observability.metrics import active_jobs
        active_jobs.inc()
    except (ImportError, Exception):
        pass

    try:
        # Mark job as running
        async with session_factory() as db:
            job = await db.get(RenderJob, job_id)
            if job is None:
                return
            job.status = JobStatus.RUNNING.value
            job.current_step = "understand"
            await db.commit()

        publish_event(ProgressEvent(job_id=job_id, event="node_start", progress=0.05, message="Loading assets", node="understand"))

        # Load assets
        async with session_factory() as db:
            query = select(VideoAsset).where(VideoAsset.project_id == project_id)
            if asset_ids:
                query = query.where(VideoAsset.id.in_(asset_ids))
            assets_result = await db.execute(query)
            assets = assets_result.scalars().all()
            asset_schemas = [AssetSchema.model_validate(a.__dict__) for a in assets]

        goal = UserGoal(**goal_dict)

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

        # Run the LangGraph pipeline
        from backend.agent.graph import run_graph_once
        state = await run_graph_once(state)

        output_path = state.final_output_path or state.current_output_path

        # Update job status
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
        cost_summary = CostTracker.instance().to_dict()
        publish_event(ProgressEvent(job_id=job_id, event=final_event, progress=1.0, message="Job completed", node="supervisor", cost=cost_summary))

        # Prometheus: record job success
        try:
            from backend.observability.metrics import jobs_total, job_duration_seconds
            jobs_total.labels(status="succeeded").inc()
            job_duration_seconds.observe(time.monotonic() - job_start)
        except (ImportError, Exception):
            pass

    except Exception:
        logger.exception("job_failed", job_id=job_id)
        async with session_factory() as db:
            job = await db.get(RenderJob, job_id)
            if job is not None:
                job.status = JobStatus.FAILED.value
                job.current_step = "failed"
                await db.commit()
        publish_event(ProgressEvent(job_id=job_id, event="failed", progress=0.0, message="Job failed", node="supervisor"))

        # Prometheus: record job failure
        try:
            from backend.observability.metrics import jobs_total, job_duration_seconds
            jobs_total.labels(status="failed").inc()
            job_duration_seconds.observe(time.monotonic() - job_start)
        except (ImportError, Exception):
            pass

    finally:
        # Prometheus: decrement active jobs
        try:
            from backend.observability.metrics import active_jobs
            active_jobs.dec()
        except (ImportError, Exception):
            pass


# Celery task wrapper
run_edit_job_task = None

try:
    from backend.workers import celery_app

    if celery_app is not None:
        @celery_app.task(bind=True, name="mixcut.run_edit_job", queue="mixcut_jobs")
        def run_edit_job_task(self, job_id: str, project_id: str, goal_dict: dict, asset_ids: list[str]) -> None:
            """Celery task for running an edit job."""
            logger.info("celery_task_started", job_id=job_id, task_id=self.request.id)
            run_edit_job_sync(job_id, project_id, goal_dict, asset_ids)
            logger.info("celery_task_completed", job_id=job_id, task_id=self.request.id)

except (ImportError, AttributeError):
    # Celery not available - tasks will be run directly
    pass
