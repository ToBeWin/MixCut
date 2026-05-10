from __future__ import annotations

import pytest

from backend.schemas.edit_script import EditScript, EditSegment, TransitionType, TextOverlay
from backend.schemas.user_goal import UserGoal
from backend.schemas.correction import CorrectionIntent, CorrectionScope, CorrectionRequest
from backend.schemas.agent_state import AgentState
from backend.harness.validator import validate_edit_script, SemanticValidationError


class TestEditSegment:
    def test_valid_segment(self):
        seg = EditSegment(asset_id="a1", in_point=0.0, out_point=5.0, timeline_start=0.0)
        assert seg.duration == 5.0

    def test_in_point_must_be_less_than_out_point(self):
        with pytest.raises(ValueError):
            EditSegment(asset_id="a1", in_point=5.0, out_point=5.0)

    def test_speed_affects_duration(self):
        seg = EditSegment(asset_id="a1", in_point=0.0, out_point=10.0, timeline_start=0.0, speed=2.0)
        assert seg.duration == 5.0

    def test_text_overlays(self):
        seg = EditSegment(
            asset_id="a1",
            in_point=0.0,
            out_point=10.0,
            timeline_start=0.0,
            text_overlays=[TextOverlay(text="Hello", start=1.0, end=4.0)],
        )
        assert len(seg.text_overlays) == 1
        assert seg.text_overlays[0].text == "Hello"


class TestEditScript:
    def test_valid_script(self):
        script = EditScript(
            project_id="p1",
            target_duration=30,
            segments=[
                EditSegment(asset_id="a1", in_point=0.0, out_point=15.0, timeline_start=0.0),
                EditSegment(asset_id="a2", in_point=0.0, out_point=15.0, timeline_start=15.0),
            ],
        )
        assert script.estimated_duration == 30.0

    def test_estimated_duration_empty(self):
        script = EditScript(project_id="p1", target_duration=30)
        assert script.estimated_duration == 0.0

    def test_validate_script_with_known_assets(self):
        script = EditScript(
            project_id="p1",
            target_duration=30,
            segments=[
                EditSegment(asset_id="a1", in_point=0.0, out_point=10.0, timeline_start=0.0),
                EditSegment(asset_id="missing", in_point=0.0, out_point=10.0, timeline_start=10.0),
            ],
        )
        with pytest.raises(SemanticValidationError, match="unknown assets"):
            validate_edit_script(script, known_asset_ids={"a1"})

    def test_validate_script_duration_positive(self):
        script = EditScript(project_id="p1", target_duration=30)
        with pytest.raises(SemanticValidationError, match="greater than zero"):
            validate_edit_script(script)


class TestUserGoal:
    def test_defaults(self):
        goal = UserGoal()
        assert goal.platform == "custom"
        assert goal.aspect_ratio == "9:16"
        assert goal.style == "professional"
        assert goal.target_duration == 30
        assert goal.subtitle_requested is True
        assert goal.voiceover_requested is False

    def test_custom_values(self):
        goal = UserGoal(
            prompt="Make it viral",
            platform="douyin",
            aspect_ratio="9:16",
            style="lively",
            target_duration=15,
            selling_points="fast delivery",
        )
        assert goal.platform == "douyin"
        assert goal.target_duration == 15

    def test_invalid_platform(self):
        with pytest.raises(Exception):
            UserGoal(platform="invalid_platform")


class TestCorrectionIntent:
    def test_valid_intent(self):
        intent = CorrectionIntent(
            id="c1",
            project_id="p1",
            job_id="j1",
            raw_text="Make the opening faster",
            affected_nodes=[CorrectionScope.EXECUTE],
        )
        assert intent.affected_nodes == [CorrectionScope.EXECUTE]

    def test_correction_request(self):
        req = CorrectionRequest(project_id="p1", job_id="j1", message="Add subtitles")
        assert req.message == "Add subtitles"


class TestAgentState:
    def test_defaults(self):
        state = AgentState(project_id="p1", job_id="j1")
        assert state.assets == []
        assert state.clip_metadata == {}
        assert state.edit_script is None
        assert state.pending_human_input is False

    def test_with_goal(self):
        state = AgentState(
            project_id="p1",
            job_id="j1",
            user_goal=UserGoal(prompt="Make a product video", platform="douyin"),
        )
        assert state.user_goal.platform == "douyin"