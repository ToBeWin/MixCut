from __future__ import annotations

from backend.harness.validator import validate_edit_script
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.edit_script import EditScript

logger = get_logger(__name__)


async def plan_node(state: AgentState, registry=None) -> AgentState:
    with span("plan_node"):
        if registry is not None and state.clip_metadata:
            from backend.agent.agents.plan_agent import plan_agent
            try:
                script = await plan_agent(state, registry)
                if script.segments:
                    known_ids = {a.id for a in state.assets} if state.assets else None
                    script = validate_edit_script(script, known_asset_ids=known_ids)
                    state.edit_script = script
                    logger.info("plan_agent_success", project_id=state.project_id, segments=len(script.segments))
                else:
                    logger.warning("plan_agent_empty_result", project_id=state.project_id)
            except Exception as exc:
                logger.error("plan_agent_failed", error=str(exc))
        if state.edit_script is None or not state.edit_script.segments:
            state.edit_script = EditScript(
                project_id=state.project_id,
                target_duration=state.user_goal.target_duration,
                aspect_ratio=state.user_goal.aspect_ratio,
            )
        state.node_outputs["plan"] = {"segment_count": len(state.edit_script.segments)}
        logger.info("plan_node_complete", job_id=state.job_id, segments=len(state.edit_script.segments))
    return state