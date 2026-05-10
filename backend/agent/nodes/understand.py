from __future__ import annotations

from backend.harness.model_call import call_model
from backend.harness.validator import validate_schema
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.clip_metadata import ClipMetadata

logger = get_logger(__name__)


async def understand_node(state: AgentState, registry=None) -> AgentState:
    with span("understand_node"):
        if registry is not None:
            from backend.agent.agents.understand_agent import understand_agent
            try:
                metadata = await understand_agent(state, registry)
                for asset_id, meta in metadata.items():
                    try:
                        validate_schema(ClipMetadata, meta.model_dump())
                    except Exception:
                        logger.warning("understand_validation_failed", asset_id=asset_id)
                        metadata[asset_id] = ClipMetadata(asset_id=asset_id, scene_summary="Validation failed")
                state.clip_metadata = {**state.clip_metadata, **metadata}
                for asset_id, meta in metadata.items():
                    logger.info("understand_asset", asset_id=asset_id, scene_summary=meta.scene_summary[:60])
            except Exception as exc:
                logger.error("understand_agent_failed", error=str(exc))
                for asset in state.assets:
                    if asset.id not in state.clip_metadata or not state.clip_metadata[asset.id].scene_summary:
                        state.clip_metadata[asset.id] = ClipMetadata(asset_id=asset.id, scene_summary="Analysis unavailable")
        else:
            for asset in state.assets:
                if asset.id not in state.clip_metadata or not state.clip_metadata[asset.id].scene_summary:
                    state.clip_metadata[asset.id] = ClipMetadata(asset_id=asset.id, scene_summary="Pending analysis")
        state.node_outputs["understand"] = {
            "asset_count": len(state.assets),
            "metadata_count": len(state.clip_metadata),
        }
        logger.info("understand_node_complete", job_id=state.job_id, asset_count=len(state.assets))
    return state