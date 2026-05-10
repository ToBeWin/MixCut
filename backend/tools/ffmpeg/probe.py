from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from backend.tools.ffmpeg.errors import FFprobeError

logger = logging.getLogger(__name__)


class VideoProbe(BaseModel):
    path: str
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    video_codec: str | None = None
    audio_codec: str | None = None
    audio_present: bool = False
    bit_rate: int | None = None


async def probe_video(path: str | Path, ffprobe_bin: str = "ffprobe") -> VideoProbe:
    path = str(path)
    args = [
        ffprobe_bin, "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        path,
    ]
    logger.debug("ffprobe_command", extra={"args": args})
    try:
        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
    except asyncio.TimeoutError:
        raise FFprobeError(f"ffprobe timed out for {path}")
    if process.returncode != 0:
        stderr_text = stderr.decode("utf-8", errors="replace")
        raise FFprobeError(f"ffprobe failed for {path}: {stderr_text[:1000]}")
    data = json.loads(stdout.decode("utf-8"))

    video_info: dict = {}
    audio_info: dict = {}
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and not video_info:
            video_info = stream
        elif stream.get("codec_type") == "audio" and not audio_info:
            audio_info = stream

    format_info = data.get("format", {})

    duration = None
    if "duration" in format_info:
        duration = float(format_info["duration"])
    elif video_info.get("duration"):
        duration = float(video_info["duration"])

    fps = None
    if "r_frame_rate" in video_info:
        parts = video_info["r_frame_rate"].split("/")
        if len(parts) == 2 and int(parts[1]) != 0:
            fps = int(parts[0]) / int(parts[1])

    bit_rate = None
    if "bit_rate" in format_info:
        bit_rate = int(format_info["bit_rate"])

    return VideoProbe(
        path=path,
        duration_seconds=duration,
        width=video_info.get("width"),
        height=video_info.get("height"),
        fps=fps,
        video_codec=video_info.get("codec_name"),
        audio_codec=audio_info.get("codec_name"),
        audio_present=bool(audio_info),
        bit_rate=bit_rate,
    )