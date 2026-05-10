from __future__ import annotations

from backend.agent.graph import determine_rerun_nodes, should_run_subtitle, should_run_tts, review_decision
from backend.schemas.correction import CorrectionScope


class TestConditionalRouting:
    def test_subtitle_requested(self):
        state = {"user_goal": type("G", (), {"subtitle_requested": True})()}
        assert should_run_subtitle(state) == "subtitle"

    def test_subtitle_not_requested(self):
        state = {"user_goal": type("G", (), {"subtitle_requested": False})()}
        assert should_run_subtitle(state) == "skip"

    def test_no_goal(self):
        state = {}
        assert should_run_subtitle(state) == "skip"

    def test_tts_requested(self):
        state = {"user_goal": type("G", (), {"voiceover_requested": True})()}
        assert should_run_tts(state) == "tts"

    def test_tts_not_requested(self):
        state = {"user_goal": type("G", (), {"voiceover_requested": False})()}
        assert should_run_tts(state) == "skip"

    def test_review_export_when_no_correction(self):
        assert review_decision({"pending_human_input": False}) == "export"

    def test_review_correct_when_correction_text(self):
        assert review_decision({"correction_text": "fix this"}) == "correct"

    def test_review_default_export(self):
        assert review_decision({}) == "export"


class TestDetermineRerunNodes:
    def test_execute_scope_includes_subtitle_tts(self):
        result = determine_rerun_nodes([CorrectionScope.EXECUTE])
        assert "execute" in result
        assert "subtitle" in result
        assert "tts" in result

    def test_understand_scope_adds_plan_execute(self):
        result = determine_rerun_nodes([CorrectionScope.UNDERSTAND])
        assert "understand" in result
        assert "plan" in result
        assert "execute" in result

    def test_plan_scope_adds_execute(self):
        result = determine_rerun_nodes([CorrectionScope.PLAN])
        assert "plan" in result
        assert "execute" in result

    def test_subtitle_scope_only(self):
        result = determine_rerun_nodes([CorrectionScope.SUBTITLE])
        assert "subtitle" in result
        assert "execute" not in result

    def test_tts_scope_only(self):
        result = determine_rerun_nodes([CorrectionScope.TTS])
        assert "tts" in result
        assert "execute" not in result

    def test_string_scopes(self):
        result = determine_rerun_nodes(["plan"])
        assert "plan" in result

    def test_empty_defaults_to_plan_execute(self):
        result = determine_rerun_nodes([])
        assert "plan" in result
        assert "execute" in result
