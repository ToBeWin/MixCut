"""LangGraph-based agent graph for MixCut video editing pipeline.

Replaces the previous hand-written sequential execution with a proper
StateGraph featuring:
- Conditional edges for subtitle/tts branching
- Send API for parallel understand fan-out
- interrupt() for human review suspend/resume
- Checkpointing for state persistence
"""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Send

from backend.agent.state import GraphState
from backend.harness.config import get_timeout
from backend.harness.cost_tracker import CostTracker, current_node
from backend.harness.timeout import NodeTimeoutError, run_with_timeout
from backend.harness.validator import validate_edit_script, validate_schema
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.clip_metadata import ClipMetadata

logger = get_logger(__name__)

# Global checkpointer - initialized lazily from config
_checkpointer = None


def _get_checkpointer():
    """Get or create the LangGraph checkpointer from config."""
    global _checkpointer
    if _checkpointer is None:
        from backend.agent.checkpointer import create_langgraph_checkpointer
        from backend.config import get_settings
        settings = get_settings()
        _checkpointer = create_langgraph_checkpointer(settings.database_url)
    return _checkpointer


def set_checkpointer(checkpointer) -> None:
    global _checkpointer
    _checkpointer = checkpointer


# ── Node wrappers ──────────────────────────────────────────────────────────

async def _understand_single_asset_node(state: GraphState, asset_id: str) -> dict[str, Any]:
    """Understand a single asset. Used with Send API for parallel fan-out."""
    from backend.config import get_settings
    from backend.model.registry import build_runtime_registry
    from backend.agent.agents.understand_agent import _understand_single_asset
    from backend.model.base import ModelMessage
    from backend.agent.prompts.understand import UNDERSTAND_SYSTEM_PROMPT, UNDERSTAND_USER_TEMPLATE

    token = current_node.set("understand")
    try:
        settings = get_settings()
        registry = await build_runtime_registry(settings)
        storage_root = Path(settings.storage_root)

        asset = next((a for a in state.get("assets", []) if a.id == asset_id), None)
        if asset is None:
            return {"clip_metadata": {asset_id: ClipMetadata(asset_id=asset_id, scene_summary="Asset not found")}}

        provider = registry.provider_for_task("multimodal_understanding")
        aid, metadata = await _understand_single_asset(asset, _state_obj(state), registry, storage_root, provider)
        return {"clip_metadata": {aid: metadata}}
    except Exception as exc:
        logger.error("understand_asset_failed", asset_id=asset_id, error=str(exc))
        return {"clip_metadata": {asset_id: ClipMetadata(asset_id=asset_id, scene_summary=f"Failed: {exc}")}}
    finally:
        current_node.reset(token)


def _state_obj(state: GraphState):
    """Create a minimal state object for agents that expect Pydantic AgentState."""
    from backend.schemas.agent_state import AgentState
    return AgentState(
        project_id=state.get("project_id", ""),
        job_id=state.get("job_id", ""),
        assets=state.get("assets", []),
        user_goal=state.get("user_goal"),
        clip_metadata=state.get("clip_metadata", {}),
    )


def understand_router(state: GraphState) -> list[Send]:
    """Route to parallel understand nodes via Send API, one per asset."""
    assets = state.get("assets", [])
    already_understood = set(state.get("clip_metadata", {}).keys())
    sends = []
    for asset in assets:
        if asset.id not in already_understood:
            sends.append(Send("understand_asset", {"state": state, "asset_id": asset.id}))
    if not sends:
        # All assets already understood, skip to plan
        return [Send("plan", state)]
    return sends


async def understand_asset(state: dict) -> dict:
    """Wrapper node for single-asset understanding (called via Send)."""
    inner_state = state.get("state", state)
    asset_id = state.get("asset_id", "")
    return await _understand_single_asset_node(inner_state, asset_id)


async def understand_merge(state: GraphState) -> dict:
    """Merge node after all understand tasks complete. Currently a no-op."""
    return {}


async def plan_node(state: GraphState) -> dict:
    """Plan edit script from clip metadata."""
    from backend.config import get_settings
    from backend.model.registry import build_runtime_registry
    from backend.agent.agents.plan_agent import plan_agent

    token = current_node.set("plan")
    try:
        settings = get_settings()
        registry = await build_runtime_registry(settings)
        agent_state = _state_obj(state)

        if not state.get("clip_metadata"):
            logger.warning("plan_no_metadata", job_id=state.get("job_id"))
            return {"node_outputs": {"plan": {"error": "no_metadata"}}}

        script = await plan_agent(agent_state, registry)
        known_ids = {a.id for a in state.get("assets", [])} or None
        try:
            script = validate_edit_script(script, known_asset_ids=known_ids)
        except Exception as exc:
            logger.warning("plan_validation_failed", error=str(exc))

        return {
            "edit_script": script,
            "node_outputs": {"plan": {"segment_count": len(script.segments)}},
        }
    except Exception as exc:
        logger.error("plan_failed", error=str(exc))
        return {"node_errors": {"plan": [str(exc)]}}
    finally:
        current_node.reset(token)


async def execute_node(state: GraphState) -> dict:
    """Execute FFmpeg operations to produce draft video."""
    from backend.config import get_settings
    from backend.agent.nodes.execute import execute_node as _execute

    token = current_node.set("execute")
    try:
        settings = get_settings()
        agent_state = _state_obj(state)
        agent_state.edit_script = state.get("edit_script")
        agent_state.current_output_path = state.get("current_output_path")

        result = await _execute(agent_state, storage_root=Path(settings.storage_root))
        return {
            "current_output_path": result.current_output_path,
            "node_outputs": {"execute": result.node_outputs.get("execute", {})},
        }
    except Exception as exc:
        logger.error("execute_failed", error=str(exc))
        return {"node_errors": {"execute": [str(exc)]}}
    finally:
        current_node.reset(token)


async def subtitle_node(state: GraphState) -> dict:
    """Transcribe and burn subtitles."""
    from backend.config import get_settings
    from backend.agent.nodes.subtitle import subtitle_node as _subtitle

    token = current_node.set("subtitle")
    try:
        settings = get_settings()
        agent_state = _state_obj(state)
        agent_state.current_output_path = state.get("current_output_path")
        agent_state.edit_script = state.get("edit_script")

        result = await _subtitle(agent_state, storage_root=Path(settings.storage_root))
        return {
            "subtitle_path": result.subtitle_path,
            "current_output_path": result.current_output_path,
            "node_outputs": {"subtitle": result.node_outputs.get("subtitle", {})},
        }
    except Exception as exc:
        logger.error("subtitle_failed", error=str(exc))
        return {"node_errors": {"subtitle": [str(exc)]}}
    finally:
        current_node.reset(token)


async def tts_node(state: GraphState) -> dict:
    """Generate and mix voiceover."""
    from backend.config import get_settings
    from backend.model.registry import build_runtime_registry
    from backend.agent.nodes.tts import tts_node as _tts

    token = current_node.set("tts")
    try:
        settings = get_settings()
        registry = await build_runtime_registry(settings)
        agent_state = _state_obj(state)
        agent_state.current_output_path = state.get("current_output_path")
        agent_state.edit_script = state.get("edit_script")

        result = await _tts(agent_state, registry=registry, storage_root=Path(settings.storage_root))
        return {
            "current_output_path": result.current_output_path,
            "node_outputs": {"tts": result.node_outputs.get("tts", {})},
        }
    except Exception as exc:
        logger.error("tts_failed", error=str(exc))
        return {"node_errors": {"tts": [str(exc)]}}
    finally:
        current_node.reset(token)


async def human_review_node(state: GraphState) -> dict:
    """Suspend graph execution and wait for human input via interrupt().

    When the graph hits interrupt(), execution pauses and the value passed
    to interrupt() is returned to the caller. The graph resumes when
    the caller invokes Command(resume=value).
    """
    cost_summary = CostTracker.instance().to_dict()
    review_data = interrupt({
        "job_id": state.get("job_id"),
        "output_path": state.get("current_output_path"),
        "edit_script": state.get("edit_script"),
        "cost_summary": cost_summary,
    })

    # review_data comes from Command(resume=...)
    if isinstance(review_data, dict):
        if review_data.get("action") == "approve":
            return {
                "pending_human_input": False,
                "final_output_path": state.get("current_output_path"),
                "cost_summary": cost_summary,
            }
        elif review_data.get("action") == "correct":
            return {
                "pending_human_input": False,
                "correction_text": review_data.get("text", ""),
                "cost_summary": cost_summary,
            }

    return {"pending_human_input": False, "cost_summary": cost_summary}


async def correct_node(state: GraphState) -> dict:
    """Parse correction intent and determine affected nodes."""
    from backend.config import get_settings
    from backend.model.registry import build_runtime_registry
    from backend.agent.nodes.correct import correct_node as _correct

    token = current_node.set("correct")
    try:
        settings = get_settings()
        registry = await build_runtime_registry(settings)
        agent_state = _state_obj(state)
        agent_state.edit_script = state.get("edit_script")
        agent_state.correction_history = state.get("correction_history", [])

        correction_text = state.get("correction_text", "")
        result = await _correct(agent_state, registry=registry, correction_text=correction_text)

        affected = []
        if result.correction_history:
            latest = result.correction_history[-1]
            affected = [s.value if hasattr(s, "value") else str(s) for s in latest.affected_nodes]

        return {
            "correction_history": result.correction_history,
            "affected_nodes": affected,
            "node_outputs": {"correct": result.node_outputs.get("correct", {})},
        }
    except Exception as exc:
        logger.error("correct_failed", error=str(exc))
        return {"node_errors": {"correct": [str(exc)]}}
    finally:
        current_node.reset(token)


async def export_node(state: GraphState) -> dict:
    """Final render and export."""
    from backend.config import get_settings
    from backend.tools.ffmpeg.commands import final_render
    from backend.tools.ffmpeg.runner import run_ffmpeg

    token = current_node.set("export")
    try:
        current_output = state.get("current_output_path")
        if not current_output:
            return {"node_outputs": {"export": {"error": "no_video"}}}

        settings = get_settings()
        project_id = state.get("project_id", "")
        job_id = state.get("job_id", "")
        user_goal = state.get("user_goal")
        platform = getattr(user_goal, "platform", "douyin") if user_goal else "douyin"

        output_dir = Path(settings.storage_root) / "outputs" / project_id
        output_dir.mkdir(parents=True, exist_ok=True)
        final_path = str(output_dir / f"final_{job_id}.mp4")

        cmd = final_render(current_output, final_path, platform=platform)
        await run_ffmpeg(cmd, timeout=600)

        return {
            "final_output_path": final_path,
            "node_outputs": {"export": {"final_path": final_path}},
        }
    except Exception as exc:
        logger.error("export_failed", error=str(exc))
        return {"node_errors": {"export": [str(exc)]}}
    finally:
        current_node.reset(token)


# ── Conditional edge functions ─────────────────────────────────────────────

def should_run_subtitle(state: GraphState) -> str:
    goal = state.get("user_goal")
    if goal and getattr(goal, "subtitle_requested", False):
        return "subtitle"
    return "skip"


def should_run_tts(state: GraphState) -> str:
    goal = state.get("user_goal")
    if goal and getattr(goal, "voiceover_requested", False):
        return "tts"
    return "skip"


def after_media_processing(state: GraphState) -> str:
    """Route to human review after subtitle/tts."""
    return "human_review"


def review_decision(state: GraphState) -> str:
    """Route after human review based on correction_text presence."""
    if state.get("correction_text"):
        return "correct"
    return "export"


def after_correction(state: GraphState) -> str:
    """Route after correction: re-run affected nodes."""
    affected = state.get("affected_nodes", [])
    if not affected:
        return "plan"
    # Determine which node to re-enter based on affected_nodes
    if "understand" in affected:
        return "understand"
    if "plan" in affected:
        return "plan"
    if "execute" in affected:
        return "execute"
    return "plan"


# ── Graph construction ─────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the MixCut pipeline."""
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("understand_asset", understand_asset)
    graph.add_node("understand_merge", understand_merge)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("subtitle", subtitle_node)
    graph.add_node("tts", tts_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("correct", correct_node)
    graph.add_node("export", export_node)

    # Entry: parallel understand fan-out via Send
    graph.add_conditional_edges(START, understand_router, ["understand_asset", "plan"])
    graph.add_edge("understand_asset", "understand_merge")
    graph.add_edge("understand_merge", "plan")

    # Plan → Execute
    graph.add_edge("plan", "execute")

    # Execute → conditional subtitle/tts → human_review
    graph.add_conditional_edges("execute", should_run_subtitle, {
        "subtitle": "subtitle",
        "skip": "after_subtitle_check",
    })
    graph.add_node("after_subtitle_check", lambda s: {})  # passthrough
    graph.add_conditional_edges("after_subtitle_check", should_run_tts, {
        "tts": "tts",
        "skip": "human_review",
    })
    graph.add_edge("subtitle", "after_tts_check")
    graph.add_node("after_tts_check", lambda s: {})  # passthrough
    graph.add_conditional_edges("after_tts_check", should_run_tts, {
        "tts": "tts",
        "skip": "human_review",
    })
    graph.add_edge("tts", "human_review")

    # Human review → approve or correct
    graph.add_conditional_edges("human_review", review_decision, {
        "export": "export",
        "correct": "correct",
    })

    # Correct → loop back
    graph.add_conditional_edges("correct", after_correction, {
        "understand": "understand_asset",
        "plan": "plan",
        "execute": "execute",
    })

    # Export → END
    graph.add_edge("export", END)

    return graph


def compile_graph():
    """Compile the graph with checkpointing."""
    graph = build_graph()
    return graph.compile(checkpointer=_get_checkpointer())


# Keep backward-compatible run_graph_once for existing callers
async def run_graph_once(state) -> Any:
    """Run the full graph once (backward compatibility wrapper).

    For new code, use compile_graph() and invoke directly with proper
    checkpointing and interrupt handling.
    """
    from backend.schemas.agent_state import AgentState as PydanticAgentState

    # Convert Pydantic state to TypedDict
    graph_state: GraphState = {
        "project_id": state.project_id,
        "job_id": state.job_id,
        "assets": state.assets,
        "user_goal": state.user_goal,
        "clip_metadata": state.clip_metadata or {},
        "edit_script": state.edit_script,
        "correction_history": state.correction_history or [],
        "current_output_path": state.current_output_path,
        "subtitle_path": state.subtitle_path,
        "node_outputs": state.node_outputs or {},
        "node_errors": state.node_errors or {},
        "iteration_count": state.iteration_count or {},
        "pending_human_input": state.pending_human_input,
        "final_output_path": state.final_output_path,
    }

    compiled = compile_graph()
    config = {"configurable": {"thread_id": state.job_id}}

    from langgraph.errors import GraphInterrupt
    try:
        result = await compiled.ainvoke(graph_state, config=config)
    except GraphInterrupt:
        # Graph hit interrupt() - state is saved in checkpointer
        # Return with pending_human_input=True so caller knows to wait
        logger.info("graph_interrupted", job_id=state.job_id)
        state.pending_human_input = True
        return state
    except Exception as exc:
        logger.error("graph_error", job_id=state.job_id, error=str(exc))
        raise

    # Convert back to Pydantic state
    state.clip_metadata = {**state.clip_metadata, **(result.get("clip_metadata") or {})}
    state.edit_script = result.get("edit_script") or state.edit_script
    state.current_output_path = result.get("current_output_path") or state.current_output_path
    state.subtitle_path = result.get("subtitle_path") or state.subtitle_path
    state.node_outputs = {**state.node_outputs, **(result.get("node_outputs") or {})}
    state.node_errors = {**state.node_errors, **(result.get("node_errors") or {})}
    state.correction_history = result.get("correction_history") or state.correction_history
    state.final_output_path = result.get("final_output_path") or state.final_output_path
    state.pending_human_input = result.get("pending_human_input", state.pending_human_input)

    return state


async def resume_graph(job_id: str, action: str, correction_text: str = "") -> dict[str, Any]:
    """Resume a graph that was interrupted for human review.

    Args:
        job_id: The thread_id for the checkpointed graph
        action: "approve" to finalize, "correct" to apply correction
        correction_text: The correction instruction (only for action="correct")

    Returns:
        The final graph state after resumption
    """
    from langgraph.types import Command

    compiled = compile_graph()
    config = {"configurable": {"thread_id": job_id}}

    resume_value = {"action": action, "text": correction_text} if action == "correct" else {"action": "approve"}

    result = await compiled.ainvoke(Command(resume=resume_value), config=config)
    return result


def determine_rerun_nodes(affected: list) -> list[str]:
    """Determine which nodes need re-run based on correction scope."""
    from backend.schemas.correction import CorrectionScope

    node_map = {
        "understand": ["understand"],
        CorrectionScope.UNDERSTAND: ["understand"],
        "plan": ["plan"],
        CorrectionScope.PLAN: ["plan"],
        "execute": ["execute"],
        CorrectionScope.EXECUTE: ["execute"],
        "subtitle": ["subtitle"],
        CorrectionScope.SUBTITLE: ["subtitle"],
        "tts": ["tts"],
        CorrectionScope.TTS: ["tts"],
    }
    downstream: dict[str, list[str]] = {
        "understand": ["plan", "execute"],
        "plan": ["execute"],
        "execute": ["subtitle", "tts"],
        "subtitle": [],
        "tts": [],
    }
    rerun: set[str] = set()
    for scope in affected:
        for node in node_map.get(scope, []):
            rerun.add(node)
            for _ in range(3):
                for parent, children in downstream.items():
                    if parent in rerun:
                        rerun.update(children)
    return list(rerun) or ["plan", "execute"]


# Keep run_correction for backward compatibility
async def run_correction(state, affected_nodes: list[str]):
    """Re-run affected nodes (backward compatibility wrapper)."""
    from backend.harness.context_trimmer import trim_agent_state

    state = trim_agent_state(state)

    compiled = compile_graph()
    config = {"configurable": {"thread_id": state.job_id}}

    graph_state: GraphState = {
        "project_id": state.project_id,
        "job_id": state.job_id,
        "assets": state.assets,
        "user_goal": state.user_goal,
        "clip_metadata": state.clip_metadata or {},
        "edit_script": state.edit_script,
        "correction_history": state.correction_history or [],
        "current_output_path": state.current_output_path,
        "subtitle_path": state.subtitle_path,
        "node_outputs": state.node_outputs or {},
        "node_errors": state.node_errors or {},
        "iteration_count": state.iteration_count or {},
        "pending_human_input": False,
        "affected_nodes": affected_nodes,
    }

    try:
        result = await compiled.ainvoke(graph_state, config=config)
    except Exception as exc:
        logger.info("correction_graph_interrupt", job_id=state.job_id, error=str(exc))
        result = graph_state

    state.clip_metadata = {**state.clip_metadata, **(result.get("clip_metadata") or {})}
    state.edit_script = result.get("edit_script") or state.edit_script
    state.current_output_path = result.get("current_output_path") or state.current_output_path
    state.subtitle_path = result.get("subtitle_path") or state.subtitle_path
    state.node_outputs = {**state.node_outputs, **(result.get("node_outputs") or {})}
    state.node_errors = {**state.node_errors, **(result.get("node_errors") or {})}
    state.correction_history = result.get("correction_history") or state.correction_history
    state.final_output_path = result.get("final_output_path") or state.final_output_path

    return state
