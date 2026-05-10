from __future__ import annotations

from pathlib import Path

from backend.harness.retry import retry_async, RetryPolicy
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState

logger = get_logger(__name__)

_TTS_RETRY = RetryPolicy(attempts=2, base_delay_seconds=2.0, multiplier=2.0, max_delay_seconds=30.0, jitter_ratio=0.2)


@retry_async(policy=_TTS_RETRY, retry_on=(Exception,))
async def _synthesize_with_retry(tts_provider, text: str, voice_id: str, output_path: Path) -> str:
    result = await tts_provider.synthesize(text=text, voice_id=voice_id, output_path=output_path)
    return result.audio_path


async def tts_node(state: AgentState, registry=None, storage_root=None) -> AgentState:
    with span("tts_node"):
        if not state.user_goal.voiceover_requested:
            logger.info("tts_node_skipped", job_id=state.job_id)
            state.node_outputs["tts"] = {"voiceover_requested": False}
            return state
        if not state.edit_script or not state.edit_script.voiceover_script:
            logger.info("tts_no_script", job_id=state.job_id)
            state.node_outputs["tts"] = {"voiceover_requested": True, "error": "no_script"}
            return state
        if registry is None:
            from backend.config import get_settings
            from backend.model.registry import build_runtime_registry
            registry = await build_runtime_registry(get_settings())
        if storage_root is None:
            from backend.config import get_settings as _get_settings
            storage_root = Path(_get_settings().storage_root)

        from backend.config import get_settings
        settings = get_settings()
        output_dir = Path(settings.storage_root) / "tts" / state.job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "voiceover.mp3"

        tts_provider = None
        if settings.minimax_api_key and settings.minimax_group_id:
            from backend.tools.tts.minimax import MiniMaxTTSProvider
            tts_provider = MiniMaxTTSProvider(api_key=settings.minimax_api_key, group_id=settings.minimax_group_id)
        elif settings.volcengine_tts_app_id and settings.volcengine_tts_access_token:
            from backend.tools.tts.volcengine import VolcengineTTSProvider
            tts_provider = VolcengineTTSProvider(app_id=settings.volcengine_tts_app_id, access_token=settings.volcengine_tts_access_token)

        if tts_provider is None:
            logger.warning("tts_no_provider", job_id=state.job_id)
            state.node_outputs["tts"] = {"voiceover_requested": True, "error": "no_provider"}
            return state

        try:
            voice_id = "male-qn-qingse" if tts_provider.name == "minimax" else "BV001_stream"
            result_path = await _synthesize_with_retry(tts_provider, state.edit_script.voiceover_script, voice_id, output_path)
            logger.info("tts_complete", job_id=state.job_id, path=result_path, provider=tts_provider.name)

            # Mix voiceover with video
            if state.current_output_path and Path(result_path).exists():
                from backend.tools.ffmpeg.commands import audio_mix
                from backend.tools.ffmpeg.runner import run_ffmpeg as _run_ffmpeg
                mix_output = str(storage_root / "outputs" / state.project_id / f"draft_vo_{state.job_id}.mp4")
                Path(mix_output).parent.mkdir(parents=True, exist_ok=True)
                cmd = audio_mix(state.current_output_path, result_path, mix_output, video_volume=0.8, audio_volume=1.0)
                await _run_ffmpeg(cmd, timeout=300)
                state.current_output_path = mix_output
                state.node_outputs["tts"] = {"voiceover_requested": True, "mixed": True, "path": mix_output}
            else:
                state.node_outputs["tts"] = {"voiceover_requested": True, "mixed": False}
        except Exception as exc:
            logger.error("tts_failed", job_id=state.job_id, error=str(exc))
            state.node_outputs["tts"] = {"voiceover_requested": True, "error": str(exc)}
    return state
