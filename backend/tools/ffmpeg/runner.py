from __future__ import annotations

import asyncio
import logging
import time

from backend.tools.ffmpeg.commands import FFmpegCommand
from backend.tools.ffmpeg.errors import FFmpegError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 300


def _detect_command_type(args: list[str]) -> str:
    """Infer command type from FFmpeg args for metrics labeling."""
    args_str = " ".join(args)
    if "concat" in args_str:
        return "concat"
    if "setpts" in args_str or "atempo" in args_str:
        return "speed"
    if "xfade" in args_str:
        return "fade"
    if "drawtext" in args_str:
        return "text_overlay"
    if "subtitles" in args_str:
        return "burn_subtitle"
    if "amix" in args_str:
        return "audio_mix"
    if "loudnorm" in args_str:
        return "audio_normalize"
    if "libx264" in args_str:
        return "final_render"
    if "-ss" in args and "-to" in args:
        return "trim"
    if "scale" in args_str:
        return "resize"
    if "vframes" in args_str:
        return "poster"
    return "other"


async def run_ffmpeg(command: FFmpegCommand, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    args = command.as_subprocess_args()
    command_type = _detect_command_type(args)
    logger.debug("ffmpeg_command", extra={"args": args, "command_type": command_type})

    start = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        _record_metrics(command_type, time.monotonic() - start, success=False)
        raise FFmpegError(f"FFmpeg command timed out after {timeout}s")
    if process.returncode != 0:
        stderr_text = stderr.decode("utf-8", errors="replace")
        _record_metrics(command_type, time.monotonic() - start, success=False)
        raise FFmpegError(f"FFmpeg exited with code {process.returncode}: {stderr_text[-2000:]}")

    _record_metrics(command_type, time.monotonic() - start, success=True)
    return args[-1]


def _record_metrics(command_type: str, duration: float, success: bool) -> None:
    try:
        from backend.observability.metrics import ffmpeg_command_duration_seconds, ffmpeg_errors_total
        ffmpeg_command_duration_seconds.labels(command_type=command_type).observe(duration)
        if not success:
            ffmpeg_errors_total.labels(command_type=command_type).inc()
    except (ImportError, Exception):
        pass


async def run_ffmpeg_dry_run(command: FFmpegCommand) -> list[str]:
    return command.as_subprocess_args()