from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from backend.harness.model_call import call_vision_model
from backend.model.base import ModelMessage
from backend.model.registry import ModelRegistry
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.clip_metadata import ClipMetadata
from backend.agent.prompts.understand import UNDERSTAND_SYSTEM_PROMPT, UNDERSTAND_USER_TEMPLATE

logger = get_logger(__name__)


def _asset_visual_input_path(asset) -> str:
    if asset.poster_path:
        return asset.poster_path
    return asset.storage_path


async def _understand_single_asset(
    asset,
    state: AgentState,
    registry: ModelRegistry,
    storage_root: Path,
    provider,
) -> tuple[str, ClipMetadata]:
    """Understand a single asset. Returns (asset_id, metadata)."""
    if asset.id in state.clip_metadata and state.clip_metadata[asset.id].scene_summary:
        return asset.id, state.clip_metadata[asset.id]

    with span("understand_asset", {"asset_id": asset.id, "provider": provider.name}):
        prompt = UNDERSTAND_USER_TEMPLATE.format(
            asset_id=asset.id,
            media_type="image" if asset.content_type.startswith("image/") else "video",
            duration=asset.duration_seconds or 0,
            resolution=f"{asset.width or 0}x{asset.height or 0}",
            platform=state.user_goal.platform,
            style=state.user_goal.style,
        )
        messages = [ModelMessage(role="user", content=prompt)]
        try:
            media_path = storage_root / _asset_visual_input_path(asset)
            media_bytes = media_path.read_bytes()
            response = await call_vision_model(
                registry,
                "multimodal_understanding",
                messages,
                images_b64=[base64.b64encode(media_bytes).decode("utf-8")],
                system=UNDERSTAND_SYSTEM_PROMPT,
                max_tokens=2048,
            )
            metadata = ClipMetadata(asset_id=asset.id, scene_summary=response[:80], raw_model_output={"response": response})
            logger.info("understand_complete", asset_id=asset.id, provider=provider.name)
            return asset.id, metadata
        except Exception as exc:
            registry.record_failure(provider.name)
            logger.error("understand_failed", asset_id=asset.id, error=str(exc))
            return asset.id, ClipMetadata(asset_id=asset.id, scene_summary=f"Analysis failed: {exc}")


async def understand_agent(state: AgentState, registry: ModelRegistry) -> dict[str, ClipMetadata]:
    from backend.config import get_settings

    provider = registry.provider_for_task("multimodal_understanding")
    storage_root = Path(get_settings().storage_root)

    tasks = [
        _understand_single_asset(asset, state, registry, storage_root, provider)
        for asset in state.assets
    ]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results: dict[str, ClipMetadata] = {}
    for item in results_list:
        if isinstance(item, Exception):
            logger.error("understand_asset_gather_error", error=str(item))
            continue
        asset_id, metadata = item
        results[asset_id] = metadata
    return results
