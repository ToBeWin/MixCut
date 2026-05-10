"""AgentState context trimming for long-running correction sessions."""

from __future__ import annotations

from backend.schemas.agent_state import AgentState

MAX_NODE_OUTPUTS_ENTRIES = 20
MAX_CORRECTION_HISTORY = 10


def trim_agent_state(state: AgentState) -> AgentState:
    """Trim stale data from AgentState to prevent unbounded growth.

    Called before each correction re-run to keep the state manageable.
    """
    # Keep only the most recent node_outputs entries
    if len(state.node_outputs) > MAX_NODE_OUTPUTS_ENTRIES:
        keys = list(state.node_outputs.keys())
        for key in keys[:-MAX_NODE_OUTPUTS_ENTRIES]:
            del state.node_outputs[key]

    # Keep only recent correction history
    if len(state.correction_history) > MAX_CORRECTION_HISTORY:
        state.correction_history = state.correction_history[-MAX_CORRECTION_HISTORY:]

    # Prune empty error lists
    state.node_errors = {k: v for k, v in state.node_errors.items() if v}

    return state
