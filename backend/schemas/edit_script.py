"""Time-coded editing plan schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from backend.schemas.base import JsonDict, StrictBaseModel


class TransitionType(str, Enum):
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"


class TextOverlay(StrictBaseModel):
    text: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    position: str = "bottom"


class EditSegment(StrictBaseModel):
    asset_id: str
    in_point: float = Field(ge=0)
    out_point: float = Field(gt=0)
    timeline_start: float = Field(ge=0)
    transition: TransitionType = TransitionType.CUT
    speed: float = Field(default=1.0, gt=0)
    text_overlays: list[TextOverlay] = Field(default_factory=list)
    rationale: str | None = None

    @model_validator(mode="after")
    def validate_points(self) -> "EditSegment":
        if self.in_point >= self.out_point:
            raise ValueError("in_point must be less than out_point")
        return self

    @property
    def duration(self) -> float:
        return (self.out_point - self.in_point) / self.speed


class EditScript(StrictBaseModel):
    project_id: str
    target_duration: int = Field(ge=1)
    aspect_ratio: str = "9:16"
    segments: list[EditSegment] = Field(default_factory=list)
    bgm_path: str | None = None
    voiceover_script: str | None = None
    planning_rationale: str | None = None
    metadata: JsonDict = Field(default_factory=dict)

    @property
    def estimated_duration(self) -> float:
        return sum(segment.duration for segment in self.segments)

