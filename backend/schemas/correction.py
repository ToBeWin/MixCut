"""Natural language correction schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from backend.schemas.base import JsonDict, StrictBaseModel


class CorrectionScope(str, Enum):
    UNDERSTAND = "understand"
    PLAN = "plan"
    EXECUTE = "execute"
    SUBTITLE = "subtitle"
    TTS = "tts"
    CORRECT = "correct"


class CorrectionRequest(StrictBaseModel):
    project_id: str
    job_id: str
    message: str


class CorrectionIntent(StrictBaseModel):
    id: str
    project_id: str
    job_id: str
    raw_text: str
    affected_nodes: list[CorrectionScope] = Field(default_factory=list)
    patch: JsonDict = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0, le=1)

