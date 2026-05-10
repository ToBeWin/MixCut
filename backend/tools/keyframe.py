from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from backend.tools.ffmpeg.commands import FFmpegCommand
from backend.tools.ffmpeg.runner import run_ffmpeg

logger = logging.getLogger(__name__)


async def extract_keyframes(
    video_path: str | Path,
    output_dir: str | Path,
    interval_seconds: float = 2.0,
    max_frames: int = 30,
    quality: int = 85,
) -> list[Path]:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = str(output_dir / "frame_%04d.jpg")
    fps = 1.0 / interval_seconds
    cmd = FFmpegCommand([
        "-i", str(video_path),
        "-vf", f"fps={fps:.4f}",
        "-frames:v", str(max_frames),
        "-q:v", str(31 - quality),
        output_pattern,
    ])
    await run_ffmpeg(cmd)
    frames = sorted(output_dir.glob("frame_*.jpg"))
    logger.info("keyframe_extraction_complete", extra={"video": str(video_path), "frame_count": len(frames)})
    return frames