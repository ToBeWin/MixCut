from __future__ import annotations

from pathlib import Path

from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.edit_script import EditScript
from backend.tools.ffmpeg.commands import concat, resize, speed, trim
from backend.tools.ffmpeg.runner import run_ffmpeg

logger = get_logger(__name__)


async def execute_agent(state: AgentState, storage_root: Path) -> str:
    if state.edit_script is None or not state.edit_script.segments:
        logger.warning("execute_no_script", project_id=state.project_id)
        return ""
    script = state.edit_script
    output_dir = storage_root / "temp" / state.job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    segment_files: list[str] = []
    for i, segment in enumerate(script.segments):
        with span("execute_segment", {"segment_id": segment.asset_id, "index": i}):
            try:
                asset_path = str(storage_root / f"assets/{state.project_id}/{segment.asset_id}")
                seg_output = str(output_dir / f"seg_{i:03d}.mp4")
                cmd = trim(asset_path, seg_output, segment.in_point, segment.out_point)
                await run_ffmpeg(cmd)
                if segment.speed != 1.0:
                    speed_output = str(output_dir / f"seg_{i:03d}_speed.mp4")
                    cmd = speed(seg_output, speed_output, segment.speed)
                    await run_ffmpeg(cmd)
                    seg_output = speed_output
                target_w, target_h = _target_dimensions(script.aspect_ratio)
                cmd = resize(seg_output, str(output_dir / f"seg_{i:03d}_resized.mp4"), target_w, target_h)
                await run_ffmpeg(cmd)
                segment_files.append(str(output_dir / f"seg_{i:03d}_resized.mp4"))
                logger.info("segment_complete", segment_index=i, asset_id=segment.asset_id)
            except Exception as exc:
                logger.error("segment_failed", segment_index=i, error=str(exc))
                continue
    if not segment_files:
        logger.error("execute_no_segments", job_id=state.job_id)
        return ""
    concat_file = str(output_dir / "concat_list.txt")
    with open(concat_file, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
    output_path = str(storage_root / "outputs" / state.project_id / f"draft_{state.job_id}.mp4")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with span("execute_concat"):
        cmd = concat(concat_file, output_path)
        await run_ffmpeg(cmd)
    logger.info("execute_complete", output_path=output_path)
    return output_path


def _target_dimensions(aspect_ratio: str) -> tuple[int, int]:
    ratios = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080)}
    return ratios.get(aspect_ratio, (1080, 1920))