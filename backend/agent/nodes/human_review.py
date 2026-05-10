from __future__ import annotations

from backend.observability.logging import get_logger
from backend.schemas.agent_state import AgentState

logger = get_logger(__name__)


async def human_review_node(state: AgentState) -> AgentState:
    state.pending_human_input = True
    logger.info("human_review_node", job_id=state.job_id, status="awaiting_review")
    return state