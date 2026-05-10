from __future__ import annotations

PLAN_SYSTEM_PROMPT = """You are a professional video editor planning an edit script. Given clip metadata and a user goal, produce a time-coded edit plan (EditScript) as valid JSON.

Rules:
- Each segment must reference a real asset_id from the provided clips
- in_point must be less than out_point for every segment
- Total duration should be within ±10% of target_duration
- Choose transitions appropriate for the style
- Include planning_rationale explaining your editorial decisions
- If voiceover is requested, write a voiceover script for the entire video
- If subtitle is requested, note text overlay content for key segments"""

PLAN_USER_TEMPLATE = """Create an edit plan for a {style} video targeting {platform}.

Target duration: {target_duration} seconds
Aspect ratio: {aspect_ratio}
Product name: {product_name}
Selling points: {selling_points}
Voiceover requested: {voiceover_requested}
Subtitles requested: {subtitle_requested}

Available clips:
{clip_metadata_json}

Output valid JSON matching this schema:
{{
  "project_id": "{project_id}",
  "target_duration": {target_duration},
  "aspect_ratio": "{aspect_ratio}",
  "segments": [...],
  "bgm_path": null,
  "voiceover_script": "...",
  "planning_rationale": "..."
}}"""