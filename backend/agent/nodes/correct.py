from __future__ import annotations

from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.correction import CorrectionScope

logger = get_logger(__name__)


async def correct_node(state: AgentState, registry=None, correction_text: str = "") -> AgentState:
    with span("correct_node"):
        state.iteration_count["correct"] = state.iteration_count.get("correct", 0) + 1
        if registry is not None and correction_text:
            from backend.agent.agents.correct_agent import correct_agent
            try:
                intent = await correct_agent(state, registry, correction_text)
                affected = [s.value if isinstance(s, CorrectionScope) else str(s) for s in intent.affected_nodes]
                state.correction_history.append(intent)
                logger.info("correct_intent_parsed", raw_text=correction_text[:80], affected_nodes=affected)
            except Exception as exc:
                logger.error("correct_agent_failed", error=str(exc))
                state.node_errors.setdefault("correct", []).append(str(exc))
        state.node_outputs["correct"] = {
            "correction_text": correction_text,
            "iteration": state.iteration_count["correct"],
        }
        logger.info("correct_node_complete", job_id=state.job_id, iteration=state.iteration_count["correct"])
    return state