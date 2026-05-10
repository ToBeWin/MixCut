"""Semantic understanding output for source clips."""

from __future__ import annotations

from pydantic import Field

from backend.schemas.base import JsonDict, StrictBaseModel


class HighlightSegment(StrictBaseModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    score: float = Field(default=0.5, ge=0, le=1)
    reason: str | None = None


class ClipMetadata(StrictBaseModel):
    asset_id: str
    scene_summary: str = ""
    subjects: list[str] = Field(default_factory=list)
    emotions: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.5, ge=0, le=1)
    highlight_segments: list[HighlightSegment] = Field(default_factory=list)
    transcript: str | None = None
    raw_model_output: JsonDict = Field(default_factory=dict)

