from __future__ import annotations

from pathlib import Path

from backend.harness.retry import retry_async, RetryPolicy
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.tools.ffmpeg.commands import burn_subtitle
from backend.tools.ffmpeg.runner import run_ffmpeg
from backend.tools.ffmpeg.errors import FFmpegError
from backend.tools.whisper import transcribe_audio, WhisperConfig

logger = get_logger(__name__)

_WHISPER_RETRY = RetryPolicy(attempts=2, base_delay_seconds=2.0, multiplier=2.0, max_delay_seconds=30.0, jitter_ratio=0.2)
_FFMPEG_RETRY = RetryPolicy(attempts=2, base_delay_seconds=1.0, multiplier=2.0, max_delay_seconds=15.0, jitter_ratio=0.15)


@retry_async(policy=_WHISPER_RETRY, retry_on=(Exception,))
async def _transcribe_with_retry(video_path: str) -> list:
    config = WhisperConfig()
    result = await transcribe_audio(video_path, config)
    return result.segments


@retry_async(policy=_FFMPEG_RETRY, retry_on=(FFmpegError, OSError))
async def _burn_subtitle_with_retry(video_path: str, ass_path: str, output_path: str) -> None:
    cmd = burn_subtitle(video_path, ass_path, output_path)
    await run_ffmpeg(cmd, timeout=180)


async def subtitle_node(state: AgentState, storage_root: Path | None = None) -> AgentState:
    with span("subtitle_node"):
        if not state.user_goal.subtitle_requested:
            logger.info("subtitle_node_skipped", job_id=state.job_id)
            state.node_outputs["subtitle"] = {"subtitle_requested": False}
            return state
        if not state.current_output_path:
            logger.warning("subtitle_no_video", job_id=state.job_id)
            state.node_outputs["subtitle"] = {"error": "no_video"}
            return state
        if storage_root is None:
            from backend.config import get_settings
            storage_root = Path(get_settings().storage_root)
        try:
            segments = await _transcribe_with_retry(state.current_output_path)
            logger.info("subtitle_transcribe_complete", segment_count=len(segments))
        except Exception as exc:
            logger.error("subtitle_transcribe_failed", error=str(exc))
            state.node_outputs["subtitle"] = {"subtitle_requested": True, "error": f"transcription_failed: {exc}"}
            return state
        ass_path = str(storage_root / "temp" / state.job_id / "subtitles.ass")
        _write_ass_file(ass_path, segments)
        output_path = str(storage_root / "outputs" / state.project_id / f"draft_sub_{state.job_id}.mp4")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            await _burn_subtitle_with_retry(state.current_output_path, ass_path, output_path)
            state.current_output_path = output_path
            state.subtitle_path = output_path
            logger.info("subtitle_burn_complete", output_path=output_path)
        except Exception as exc:
            logger.error("subtitle_burn_failed", error=str(exc))
        state.node_outputs["subtitle"] = {"subtitle_requested": True, "subtitle_path": state.subtitle_path, "output_path": state.current_output_path}
    return state


def _write_ass_file(path: str, segments: list[dict]) -> None:
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for seg in segments:
        start = _format_ass_time(seg.get("start", 0))
        end = _format_ass_time(seg.get("end", 0))
        text = seg.get("text", "").replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"