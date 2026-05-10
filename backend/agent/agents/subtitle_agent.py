from __future__ import annotations

from pathlib import Path

from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.tools.ffmpeg.commands import burn_subtitle
from backend.tools.ffmpeg.runner import run_ffmpeg
from backend.tools.whisper import transcribe_audio, WhisperConfig

logger = get_logger(__name__)


async def subtitle_agent(state: AgentState, storage_root: Path) -> str | None:
    if not state.user_goal.subtitle_requested or not state.current_output_path:
        return None
    with span("subtitle_transcribe"):
        try:
            result = await transcribe_audio(state.current_output_path, WhisperConfig())
            logger.info("subtitle_transcribe_complete", segment_count=len(result.segments))
        except Exception as exc:
            logger.error("subtitle_transcribe_failed", error=str(exc))
            return None
    ass_path = str(storage_root / "temp" / state.job_id / "subtitles.ass")
    _write_ass_file(ass_path, result.segments)
    with span("subtitle_burn"):
        try:
            output_path = str(storage_root / "outputs" / state.project_id / f"draft_sub_{state.job_id}.mp4")
            cmd = burn_subtitle(state.current_output_path, ass_path, output_path)
            await run_ffmpeg(cmd)
            logger.info("subtitle_burn_complete", output_path=output_path)
            return output_path
        except Exception as exc:
            logger.error("subtitle_burn_failed", error=str(exc))
            return None


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