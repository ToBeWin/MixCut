from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from backend.harness.retry import retry_async, RetryPolicy
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.tools.ffmpeg.commands import (
    concat,
    resize,
    speed,
    text_overlay,
    trim,
)
from backend.tools.ffmpeg.runner import run_ffmpeg
from backend.tools.ffmpeg.errors import FFmpegError

logger = get_logger(__name__)

_FFMPEG_RETRY_POLICY = RetryPolicy(attempts=2, base_delay_seconds=0.5, multiplier=2.0, max_delay_seconds=10.0, jitter_ratio=0.1)


def _target_dimensions(aspect_ratio: str) -> tuple[int, int]:
    ratios = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080)}
    return ratios.get(aspect_ratio, (1080, 1920))


def _overlay_position(position: str, width: int, height: int) -> tuple[int, int]:
    margin = 20
    positions = {
        "top": (margin, margin),
        "bottom": (margin, height - 80),
        "center": (width // 2 - 100, height // 2 - 20),
        "top_left": (margin, margin),
        "bottom_right": (width - 300, height - 80),
    }
    return positions.get(position, (margin, height - 80))


@retry_async(policy=_FFMPEG_RETRY_POLICY, retry_on=(FFmpegError, OSError))
async def _run_ffmpeg_with_retry(cmd) -> None:
    await run_ffmpeg(cmd, timeout=300)


def _resolve_asset_path(storage_root: Path, project_id: str, asset_id: str, asset_paths: dict[str, str]) -> str:
    storage_key = asset_paths.get(asset_id)
    if storage_key:
        return str(storage_root / storage_key)

    candidates: Iterable[Path] = (storage_root / "assets" / project_id).glob(f"{asset_id}.*")
    first_candidate = next(iter(candidates), None)
    if first_candidate is not None:
        return str(first_candidate)

    return str(storage_root / "assets" / project_id / asset_id)


async def execute_node(state: AgentState, storage_root: Path | None = None) -> AgentState:
    if storage_root is None:
        from backend.config import get_settings
        storage_root = Path(get_settings().storage_root)
    with span("execute_node"):
        if state.edit_script is None or not state.edit_script.segments:
            logger.warning("execute_no_script", job_id=state.job_id)
            state.current_output_path = None
            state.node_outputs["execute"] = {"error": "no_edit_script"}
            return state
        script = state.edit_script
        target_w, target_h = _target_dimensions(script.aspect_ratio)
        output_dir = storage_root / "temp" / state.job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (storage_root / "outputs" / state.project_id).mkdir(parents=True, exist_ok=True)
        segment_files: list[str] = []
        asset_paths = {asset.id: asset.storage_path for asset in state.assets}
        segments_output_dir = output_dir / "segments"
        segments_output_dir.mkdir(parents=True, exist_ok=True)
        for i, segment in enumerate(script.segments):
            seg_label = f"segment_{i:03d}"
            with span("execute_segment", {"segment_id": seg_label, "asset_id": segment.asset_id}):
                try:
                    asset_path = _resolve_asset_path(storage_root, state.project_id, segment.asset_id, asset_paths)
                    seg_output = str(segments_output_dir / f"seg_{i:03d}_trimmed.mp4")
                    cmd = trim(asset_path, seg_output, segment.in_point, segment.out_point)
                    await _run_ffmpeg_with_retry(cmd)
                    current = seg_output
                    if segment.speed != 1.0:
                        speed_output = str(segments_output_dir / f"seg_{i:03d}_speed.mp4")
                        cmd = speed(current, speed_output, segment.speed)
                        await _run_ffmpeg_with_retry(cmd)
                        current = speed_output
                    resized = str(segments_output_dir / f"seg_{i:03d}_resized.mp4")
                    cmd = resize(current, resized, target_w, target_h)
                    await _run_ffmpeg_with_retry(cmd)
                    current = resized
                    if segment.text_overlays:
                        for overlay in segment.text_overlays:
                            x, y = _overlay_position(overlay.position, target_w, target_h)
                            overlayed = str(segments_output_dir / f"seg_{i:03d}_overlay.mp4")
                            cmd = text_overlay(current, overlayed, overlay.text, x=x, y=y)
                            await _run_ffmpeg_with_retry(cmd)
                            current = overlayed
                    segment_files.append(current)
                    logger.info("segment_complete", segment=i, asset_id=segment.asset_id)
                except Exception as exc:
                    logger.error("segment_failed", segment=i, error=str(exc))
                    continue
        if not segment_files:
            logger.error("execute_no_segments", job_id=state.job_id)
            state.current_output_path = None
            state.node_outputs["execute"] = {"error": "no_segments_rendered"}
            return state
        concat_file = str(output_dir / "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")
        output_path = str(storage_root / "outputs" / state.project_id / f"draft_{state.job_id}.mp4")
        with span("execute_concat"):
            cmd = concat(concat_file, output_path)
            await _run_ffmpeg_with_retry(cmd)
        current = output_path

        # BGM mixing
        if script.bgm_path:
            from backend.tools.ffmpeg.commands import audio_mix
            bgm_full = str(storage_root / script.bgm_path) if not script.bgm_path.startswith("/") else script.bgm_path
            if Path(bgm_full).exists():
                bgm_output = str(storage_root / "outputs" / state.project_id / f"draft_bgm_{state.job_id}.mp4")
                with span("execute_bgm_mix"):
                    cmd = audio_mix(current, bgm_full, bgm_output, video_volume=1.0, audio_volume=0.3)
                    await _run_ffmpeg_with_retry(cmd)
                current = bgm_output

        # Audio normalization
        from backend.tools.ffmpeg.commands import audio_normalize
        norm_output = str(storage_root / "outputs" / state.project_id / f"draft_norm_{state.job_id}.mp4")
        with span("execute_normalize"):
            cmd = audio_normalize(current, norm_output)
            await _run_ffmpeg_with_retry(cmd)
        current = norm_output

        state.current_output_path = current
        state.node_outputs["execute"] = {
            "output_path": current,
            "segment_count": len(segment_files),
            "total_segments": len(script.segments),
            "bgm_applied": bool(script.bgm_path),
        }
        logger.info("execute_complete", job_id=state.job_id, output_path=current, segments=len(segment_files))
    return state
