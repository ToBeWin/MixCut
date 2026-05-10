from __future__ import annotations

from pathlib import Path

from backend.config import get_settings
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState

logger = get_logger(__name__)


async def tts_agent(state: AgentState) -> str | None:
    if not state.user_goal.voiceover_requested:
        return None
    if not state.edit_script or not state.edit_script.voiceover_script:
        logger.info("tts_no_script", job_id=state.job_id)
        return None
    settings = get_settings()
    storage_root = Path(settings.storage_root)
    output_dir = storage_root / "tts" / state.job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "voiceover.mp3"
    tts_provider = None
    if settings.minimax_api_key and settings.minimax_group_id:
        from backend.tools.tts.minimax import MiniMaxTTSProvider

        tts_provider = MiniMaxTTSProvider(
            api_key=settings.minimax_api_key,
            group_id=settings.minimax_group_id,
        )
    elif settings.volcengine_tts_app_id and settings.volcengine_tts_access_token:
        from backend.tools.tts.volcengine import VolcengineTTSProvider

        tts_provider = VolcengineTTSProvider(
            app_id=settings.volcengine_tts_app_id,
            access_token=settings.volcengine_tts_access_token,
        )
    if tts_provider is None:
        logger.warning("tts_no_provider", job_id=state.job_id)
        return None
    with span("tts_synthesize", {"provider": tts_provider.name}):
        try:
            voice_id = "male-qn-qingse" if tts_provider.name == "minimax" else "BV001_stream"
            result = await tts_provider.synthesize(
                text=state.edit_script.voiceover_script,
                voice_id=voice_id,
                output_path=output_path,
            )
            logger.info("tts_complete", job_id=state.job_id, path=result.audio_path, provider=tts_provider.name)
            return result.audio_path
        except Exception as exc:
            logger.error("tts_failed", job_id=state.job_id, error=str(exc))
            return None