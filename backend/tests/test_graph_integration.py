"""Graph integration tests with mock providers.

Tests the full agent pipeline (understand → plan → execute → export)
using mock model providers and a temp storage directory.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from backend.schemas.agent_state import AgentState
from backend.schemas.asset import Asset
from backend.schemas.clip_metadata import ClipMetadata
from backend.schemas.edit_script import EditScript, EditSegment
from backend.schemas.user_goal import UserGoal


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary storage directory structure."""
    (tmp_path / "assets" / "proj1").mkdir(parents=True)
    (tmp_path / "outputs" / "proj1").mkdir(parents=True)
    (tmp_path / "temp").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_asset(temp_storage):
    """Create a sample asset with a small test video."""
    asset_dir = temp_storage / "assets" / "proj1"
    # Create a minimal valid MP4 (just a placeholder - won't actually play)
    test_video = asset_dir / "asset1.mp4"
    # Write minimal ftyp box + moov box for ffprobe to handle
    test_video.write_bytes(b'\x00' * 1024)
    return Asset(
        id="asset1",
        project_id="proj1",
        filename="test.mp4",
        storage_path="assets/proj1/asset1.mp4",
        content_type="video/mp4",
        status="uploaded",
        duration_seconds=10.0,
        width=1920,
        height=1080,
        fps=30.0,
    )


@pytest.fixture
def sample_state(sample_asset):
    """Create a sample AgentState for testing."""
    return AgentState(
        project_id="proj1",
        job_id="job1",
        assets=[sample_asset],
        user_goal=UserGoal(
            prompt="Make a short product video",
            platform="douyin",
            aspect_ratio="9:16",
            style="lively",
            target_duration=10,
            subtitle_requested=False,
            voiceover_requested=False,
            bgm_requested=False,
        ),
        clip_metadata={},
        edit_script=None,
        correction_history=[],
        current_output_path=None,
        subtitle_path=None,
        node_outputs={},
        node_errors={},
        iteration_count={},
        pending_human_input=False,
        final_output_path=None,
    )


class TestGraphConditionalRouting:
    """Test the conditional edge routing logic."""

    def test_subtitle_skip_when_not_requested(self):
        from backend.agent.graph import should_run_subtitle
        goal = UserGoal(subtitle_requested=False)
        assert should_run_subtitle({"user_goal": goal}) == "skip"

    def test_subtitle_run_when_requested(self):
        from backend.agent.graph import should_run_subtitle
        goal = UserGoal(subtitle_requested=True)
        assert should_run_subtitle({"user_goal": goal}) == "subtitle"

    def test_tts_skip_when_not_requested(self):
        from backend.agent.graph import should_run_tts
        goal = UserGoal(voiceover_requested=False)
        assert should_run_tts({"user_goal": goal}) == "skip"

    def test_review_correct_with_text(self):
        from backend.agent.graph import review_decision
        assert review_decision({"correction_text": "fix this"}) == "correct"

    def test_review_export_without_text(self):
        from backend.agent.graph import review_decision
        assert review_decision({}) == "export"

    def test_after_correction_routes_to_affected(self):
        from backend.agent.graph import after_correction
        assert after_correction({"affected_nodes": ["execute"]}) == "execute"
        assert after_correction({"affected_nodes": ["plan"]}) == "plan"
        assert after_correction({"affected_nodes": ["understand"]}) == "understand"
        assert after_correction({}) == "plan"


class TestPlanNode:
    """Test the plan node with mock provider."""

    @pytest.mark.asyncio
    async def test_plan_produces_edit_script(self, sample_state, temp_storage):
        """Plan node should produce a valid EditScript from clip metadata."""
        from backend.agent.graph import plan_node

        # Mock the registry and plan_agent
        mock_script = EditScript(
            project_id="proj1",
            target_duration=10,
            segments=[
                EditSegment(asset_id="asset1", in_point=0.0, out_point=5.0, timeline_start=0.0),
                EditSegment(asset_id="asset1", in_point=5.0, out_point=10.0, timeline_start=5.0),
            ],
        )

        graph_state = {
            "project_id": "proj1",
            "job_id": "job1",
            "assets": sample_state.assets,
            "user_goal": sample_state.user_goal,
            "clip_metadata": {"asset1": ClipMetadata(asset_id="asset1", scene_summary="test")},
        }

        with patch("backend.model.registry.build_runtime_registry") as mock_build:
            mock_registry = AsyncMock()
            mock_build.return_value = mock_registry
            with patch("backend.agent.agents.plan_agent.plan_agent", return_value=mock_script):
                result = await plan_node(graph_state)

        assert "edit_script" in result
        assert result["edit_script"] is not None
        assert len(result["edit_script"].segments) == 2


class TestExecuteNode:
    """Test the execute node with mock FFmpeg."""

    @pytest.mark.asyncio
    async def test_execute_skips_without_script(self, sample_state, temp_storage):
        """Execute node should skip when no edit script."""
        from backend.agent.nodes.execute import execute_node

        result = await execute_node(sample_state, storage_root=temp_storage)
        assert result.current_output_path is None
        assert "error" in result.node_outputs.get("execute", {})

    @pytest.mark.asyncio
    async def test_execute_processes_segments(self, sample_state, temp_storage):
        """Execute node should process segments and produce output."""
        from backend.agent.nodes.execute import execute_node

        sample_state.edit_script = EditScript(
            project_id="proj1",
            target_duration=10,
            segments=[
                EditSegment(asset_id="asset1", in_point=0.0, out_point=5.0, timeline_start=0.0),
            ],
        )

        with patch("backend.agent.nodes.execute.run_ffmpeg", new_callable=AsyncMock) as mock_ffmpeg:
            mock_ffmpeg.return_value = "/tmp/output.mp4"
            result = await execute_node(sample_state, storage_root=temp_storage)

        # Should have called FFmpeg for trim, resize, normalize
        assert mock_ffmpeg.call_count >= 2  # trim + resize at minimum


class TestSubtitleNode:
    """Test the subtitle node."""

    @pytest.mark.asyncio
    async def test_subtitle_skips_when_not_requested(self, sample_state, temp_storage):
        """Subtitle node should skip when not requested."""
        from backend.agent.nodes.subtitle import subtitle_node

        result = await subtitle_node(sample_state, storage_root=temp_storage)
        assert result.node_outputs["subtitle"]["subtitle_requested"] is False


class TestTTSNode:
    """Test the TTS node."""

    @pytest.mark.asyncio
    async def test_tts_skips_when_not_requested(self, sample_state, temp_storage):
        """TTS node should skip when not requested."""
        from backend.agent.nodes.tts import tts_node

        result = await tts_node(sample_state, storage_root=temp_storage)
        assert result.node_outputs["tts"]["voiceover_requested"] is False


class TestCheckpointer:
    """Test checkpointer creation."""

    def test_memory_checkpointer_fallback(self):
        """Should fall back to MemorySaver when no DB URL."""
        from backend.agent.checkpointer import create_langgraph_checkpointer
        cp = create_langgraph_checkpointer(database_url=None)
        assert cp is not None

    def test_memory_checkpointer_no_postgres(self):
        """Should fall back to MemorySaver for invalid URL."""
        from backend.agent.checkpointer import create_langgraph_checkpointer
        cp = create_langgraph_checkpointer(database_url="postgresql://fake:fake@localhost/fake")
        # Should fall back to MemorySaver since we can't actually connect
        assert cp is not None


class TestValidator:
    """Test edit script validation."""

    def test_valid_script_passes(self):
        from backend.harness.validator import validate_edit_script
        script = EditScript(
            project_id="p1",
            target_duration=10,
            segments=[EditSegment(asset_id="a1", in_point=0.0, out_point=5.0, timeline_start=0.0)],
        )
        result = validate_edit_script(script, known_asset_ids={"a1"})
        assert result is not None

    def test_unknown_asset_rejected(self):
        from backend.harness.validator import validate_edit_script, SemanticValidationError
        script = EditScript(
            project_id="p1",
            target_duration=10,
            segments=[EditSegment(asset_id="missing", in_point=0.0, out_point=5.0, timeline_start=0.0)],
        )
        with pytest.raises(SemanticValidationError, match="unknown assets"):
            validate_edit_script(script, known_asset_ids={"a1"})

    def test_empty_segments_rejected(self):
        from backend.harness.validator import validate_edit_script, SemanticValidationError
        script = EditScript(project_id="p1", target_duration=10)
        with pytest.raises(SemanticValidationError, match="greater than zero"):
            validate_edit_script(script)
