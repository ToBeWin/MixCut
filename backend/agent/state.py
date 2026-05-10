"""LangGraph graph state definition using TypedDict.

This is the internal state used by the LangGraph StateGraph.
The Pydantic AgentState in schemas/agent_state.py is used for API I/O.
"""

from __future__ import annotations

from typing import Any, TypedDict

from backend.schemas.asset import Asset
from backend.schemas.clip_metadata import ClipMetadata
from backend.schemas.correction import CorrectionIntent
from backend.schemas.edit_script import EditScript
from backend.schemas.user_goal import UserGoal


class GraphState(TypedDict, total=False):
    """State schema for the LangGraph agent graph.

    All fields are optional (total=False) because LangGraph merges
    partial updates from each node back into the shared state.
    """
    project_id: str
    job_id: str
    assets: list[Asset]
    user_goal: UserGoal
    clip_metadata: dict[str, ClipMetadata]
    edit_script: EditScript | None
    correction_history: list[CorrectionIntent]
    current_output_path: str | None
    subtitle_path: str | None
    node_outputs: dict[str, dict[str, Any]]
    node_errors: dict[str, list[str]]
    iteration_count: dict[str, int]
    pending_human_input: bool
    final_output_path: str | None
    # Correction-specific fields
    correction_text: str
    affected_nodes: list[str]
    # Cost tracking
    cost_summary: dict[str, Any]
