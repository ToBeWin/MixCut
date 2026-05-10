from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.graph import determine_rerun_nodes, run_correction
from backend.database import get_db
from backend.models.correction import CorrectionHistory
from backend.models.job import RenderJob
from backend.observability.logging import get_logger
from backend.schemas.agent_state import AgentState
from backend.schemas.correction import CorrectionIntent, CorrectionRequest, CorrectionScope
from backend.sanitize import sanitize_user_text
from backend.workers.progress import ProgressEvent, publish_event

logger = get_logger(__name__)

router = APIRouter()


async def _parse_correction_intent(project_id: str, job_id: str, raw_text: str, state: AgentState) -> CorrectionIntent:
    try:
        from backend.config import get_settings
        from backend.model.registry import build_runtime_registry
        from backend.agent.agents.correct_agent import correct_agent

        settings = get_settings()
        registry = await build_runtime_registry(settings)
        intent = await correct_agent(state, registry, raw_text)
        intent.id = str(uuid4())
        intent.project_id = project_id
        intent.job_id = job_id
        return intent
    except Exception as exc:
        logger.error("correction_agent_failed", error=str(exc))
        return CorrectionIntent(
            id=str(uuid4()),
            project_id=project_id,
            job_id=job_id,
            raw_text=raw_text,
            affected_nodes=[CorrectionScope.PLAN, CorrectionScope.EXECUTE],
            patch={},
            confidence=0.0,
        )


@router.post("/corrections", response_model=CorrectionIntent, status_code=201)
async def submit_correction(payload: CorrectionRequest, db: AsyncSession = Depends(get_db)) -> CorrectionIntent:
    payload.message = sanitize_user_text(payload.message)
    job = await db.get(RenderJob, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    goal_data = job.goal if isinstance(job.goal, dict) else {}
    from backend.schemas.user_goal import UserGoal

    state = AgentState(project_id=payload.project_id, job_id=payload.job_id, user_goal=UserGoal(**goal_data))

    intent = await _parse_correction_intent(payload.project_id, payload.job_id, payload.message, state)

    correction = CorrectionHistory(
        id=intent.id,
        project_id=payload.project_id,
        job_id=payload.job_id,
        raw_text=payload.message,
        operations=[intent.patch] if intent.patch else [],
        affected_nodes=[n.value for n in intent.affected_nodes],
        confidence=intent.confidence,
    )
    db.add(correction)
    await db.flush()

    publish_event(ProgressEvent(job_id=payload.job_id, event="correction", progress=0.3, message=f"Correction: {payload.message[:80]}", node="correct"))
    return intent


@router.get("/corrections", response_model=list[CorrectionIntent])
async def list_corrections(
    project_id: str,
    job_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[CorrectionIntent]:
    query = select(CorrectionHistory).where(CorrectionHistory.project_id == project_id)
    if job_id:
        query = query.where(CorrectionHistory.job_id == job_id)
    result = await db.execute(query.order_by(CorrectionHistory.created_at.desc()))
    corrections = result.scalars().all()
    return [
        CorrectionIntent(
            id=c.id,
            project_id=c.project_id,
            job_id=c.job_id,
            raw_text=c.raw_text,
            affected_nodes=[CorrectionScope(n) for n in (c.affected_nodes or [])],
            patch=c.operations[0] if c.operations else {},
            confidence=c.confidence,
        )
        for c in corrections
    ]


@router.post("/{job_id}/resume", response_model=CorrectionIntent)
async def resume_with_correction(
    job_id: str, payload: CorrectionRequest, db: AsyncSession = Depends(get_db)
) -> CorrectionIntent:
    job = await db.get(RenderJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    goal_data = job.goal if isinstance(job.goal, dict) else {}
    from backend.schemas.user_goal import UserGoal

    state = AgentState(project_id=payload.project_id, job_id=job_id, user_goal=UserGoal(**goal_data))

    intent = await _parse_correction_intent(payload.project_id, job_id, payload.message, state)

    correction = CorrectionHistory(
        id=intent.id,
        project_id=payload.project_id,
        job_id=job_id,
        raw_text=payload.message,
        operations=[intent.patch] if intent.patch else [],
        affected_nodes=[n.value for n in intent.affected_nodes],
        confidence=intent.confidence,
    )
    db.add(correction)
    await db.flush()

    affected_node_names = determine_rerun_nodes(intent.affected_nodes)
    publish_event(ProgressEvent(job_id=job_id, event="correction", progress=0.3, message=f"Re-running: {', '.join(affected_node_names)}", node="correct"))

    import asyncio

    async def _run_correction_background() -> None:
        from backend.database import _get_session_factory

        session_factory = _get_session_factory()
        try:
            refreshed_state = await run_correction(state, affected_node_names)
            async with session_factory() as db2:
                j = await db2.get(RenderJob, job_id)
                if j is not None:
                    j.status = "pending_review" if refreshed_state.pending_human_input else "succeeded"
                    j.output_path = refreshed_state.final_output_path or refreshed_state.current_output_path
                    await db2.commit()
            publish_event(ProgressEvent(job_id=job_id, event="completed" if not refreshed_state.pending_human_input else "waiting_review", progress=1.0, message="Correction applied", node="correct"))
        except Exception as exc:
            logger.exception("correction_background_error", job_id=job_id)
            publish_event(ProgressEvent(job_id=job_id, event="failed", progress=0.0, message=str(exc), node="correct"))

    asyncio.create_task(_run_correction_background())
    return intent
