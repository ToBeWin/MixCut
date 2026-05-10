from __future__ import annotations

CORRECT_SYSTEM_PROMPT = """You are a video editing assistant that parses natural language correction requests into structured operations.

Given the user's correction message and the current edit plan, determine:
1. What operation type the user wants (swap_clip, set_speed, remove_segment, update_transition, update_subtitle_style, remove_subtitles, update_tts_style, update_tts_voice, remove_tts, update_duration, replan, update_bgm_volume, update_text_overlay, insert_segment)
2. Which segments or elements are affected
3. Which agent nodes need to re-run

Output ONLY valid JSON matching the CorrectionIntent schema."""

CORRECT_USER_TEMPLATE = """User correction: {raw_text}

Current edit script:
{edit_script_json}

Available assets:
{assets_json}

Determine the correction intent and output JSON with:
- affected_nodes: list of node names to re-run (understand, plan, execute, subtitle, tts)
- patch: dict of changes to apply to the edit script or state
- confidence: 0.0-1.0"""