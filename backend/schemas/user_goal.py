"""User intent and output preferences."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.schemas.base import StrictBaseModel


Platform = Literal["douyin", "xiaohongshu", "taobao", "bilibili", "custom"]
AspectRatio = Literal["9:16", "1:1", "16:9"]
EditStyle = Literal["lively", "professional", "storytelling", "minimalist", "custom"]


class UserGoal(StrictBaseModel):
    prompt: str = Field(default="", description="Natural language editing request.")
    platform: Platform = "custom"
    aspect_ratio: AspectRatio = "9:16"
    style: EditStyle = "professional"
    target_duration: int = Field(default=30, ge=1, le=3600)
    selling_points: str | None = None
    product_name: str | None = None
    voiceover_requested: bool = False
    subtitle_requested: bool = True
    bgm_requested: bool = False

