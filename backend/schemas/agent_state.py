"""Agent graph state schema."""

from __future__ import annotations

from pydantic import Field

from backend.schemas.asset import Asset
from backend.schemas.base import JsonDict, StrictBaseModel
from backend.schemas.clip_metadata import ClipMetadata
from backend.schemas.correction import CorrectionIntent
from backend.schemas.edit_script import EditScript
from backend.schemas.user_goal import UserGoal


class AgentState(StrictBaseModel):
    project_id: str
    job_id: str
    assets: list[Asset] = Field(default_factory=list)
    user_goal: UserGoal = Field(default_factory=UserGoal)
    clip_metadata: dict[str, ClipMetadata] = Field(default_factory=dict)
    edit_script: EditScript | None = None
    correction_history: list[CorrectionIntent] = Field(default_factory=list)
    current_output_path: str | None = None
    subtitle_path: str | None = None
    node_outputs: dict[str, JsonDict] = Field(default_factory=dict)
    node_errors: dict[str, list[str]] = Field(default_factory=dict)
    iteration_count: dict[str, int] = Field(default_factory=dict)
    pending_human_input: bool = False
    final_output_path: str | None = None

