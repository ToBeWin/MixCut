from __future__ import annotations

import json

from backend.errors import ModelOutputError
from backend.harness.config import get_correction_loop_policy
from backend.harness.loop import LoopMode, MaxIterationsExceeded, run_agent_loop
from backend.harness.model_call import call_model
from backend.harness.validator import SemanticValidationError, validate_edit_script, validation_error_text
from backend.model.base import ModelMessage
from backend.model.registry import ModelRegistry
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.edit_script import EditScript
from backend.agent.prompts.plan import PLAN_SYSTEM_PROMPT, PLAN_USER_TEMPLATE

logger = get_logger(__name__)

_MAX_CORRECTION_ATTEMPTS = 3


async def plan_agent(state: AgentState, registry: ModelRegistry) -> EditScript:
    clip_metadata_json = json.dumps(
        {aid: meta.model_dump() for aid, meta in state.clip_metadata.items()},
        ensure_ascii=False,
        default=str,
    )
    prompt = PLAN_USER_TEMPLATE.format(
        style=state.user_goal.style,
        platform=state.user_goal.platform,
        target_duration=state.user_goal.target_duration,
        aspect_ratio=state.user_goal.aspect_ratio,
        product_name=state.user_goal.product_name or "未指定",
        selling_points=state.user_goal.selling_points or "未指定",
        voiceover_requested=state.user_goal.voiceover_requested,
        subtitle_requested=state.user_goal.subtitle_requested,
        clip_metadata_json=clip_metadata_json,
        project_id=state.project_id,
    )
    messages = [ModelMessage(role="user", content=prompt)]

    with span("plan_edit", {"provider": registry.provider_for_task("edit_planning").name}):
        last_error: str | None = None
        for attempt in range(_MAX_CORRECTION_ATTEMPTS):
            current_prompt = prompt
            if last_error:
                current_prompt = f"{prompt}\n\nYour previous output was invalid. Error:\n{last_error}\n\nPlease fix only the invalid parts and return the corrected JSON."

            try:
                response = await call_model(registry, "edit_planning", messages, system=PLAN_SYSTEM_PROMPT, temperature=0.4, max_tokens=4096)
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                script = EditScript.model_validate_json(response_text)

                known_ids = {a.id for a in state.assets} if state.assets else None
                script = validate_edit_script(script, known_asset_ids=known_ids)

                logger.info("plan_complete", project_id=state.project_id, segments=len(script.segments), attempt=attempt + 1)
                return script

            except Exception as exc:
                last_error = str(exc)
                logger.warning("plan_parse_failed", attempt=attempt + 1, error=last_error)
                if attempt >= _MAX_CORRECTION_ATTEMPTS - 1:
                    logger.error("plan_max_retries_exceeded", project_id=state.project_id, error=last_error)
                    return EditScript(
                        project_id=state.project_id,
                        target_duration=state.user_goal.target_duration,
                        aspect_ratio=state.user_goal.aspect_ratio,
                        planning_rationale=f"Planning failed after {_MAX_CORRECTION_ATTEMPTS} attempts: {last_error}",
                    )

        return EditScript(project_id=state.project_id, target_duration=state.user_goal.target_duration, aspect_ratio=state.user_goal.aspect_ratio)