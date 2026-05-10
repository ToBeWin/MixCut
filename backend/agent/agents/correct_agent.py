from __future__ import annotations

import json

from backend.harness.model_call import call_model
from backend.model.base import ModelMessage
from backend.model.registry import ModelRegistry
from backend.observability.logging import get_logger
from backend.observability.tracing import span
from backend.schemas.agent_state import AgentState
from backend.schemas.correction import CorrectionIntent, CorrectionScope
from backend.agent.prompts.correct import CORRECT_SYSTEM_PROMPT, CORRECT_USER_TEMPLATE

logger = get_logger(__name__)

_MAX_CORRECTION_ATTEMPTS = 3


async def correct_agent(state: AgentState, registry: ModelRegistry, raw_text: str) -> CorrectionIntent:
    edit_script_json = state.edit_script.model_dump_json(indent=2) if state.edit_script else "{}"
    assets_json = json.dumps([{"id": a.id, "filename": a.filename} for a in state.assets], ensure_ascii=False)
    prompt = CORRECT_USER_TEMPLATE.format(
        raw_text=raw_text,
        edit_script_json=edit_script_json,
        assets_json=assets_json,
    )
    messages = [ModelMessage(role="user", content=prompt)]

    last_error: str | None = None
    for attempt in range(_MAX_CORRECTION_ATTEMPTS):
        current_prompt = prompt
        if last_error:
            current_prompt = f"{prompt}\n\nYour previous output was invalid. Error:\n{last_error}\n\nPlease fix only the invalid parts and return the corrected JSON."

        with span("correct_intent", {"attempt": attempt + 1}):
            try:
                response = await call_model(registry, "correction_intent", messages, system=CORRECT_SYSTEM_PROMPT, temperature=0.2, max_tokens=2048)
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                intent = CorrectionIntent.model_validate_json(response_text)
                logger.info("correct_intent_parsed", raw_text=raw_text, affected_nodes=[n.value for n in intent.affected_nodes], attempt=attempt + 1)
                return intent

            except Exception as exc:
                last_error = str(exc)
                logger.warning("correct_intent_parse_failed", attempt=attempt + 1, error=last_error)
                if attempt >= _MAX_CORRECTION_ATTEMPTS - 1:
                    logger.error("correct_max_retries_exceeded", raw_text=raw_text, error=last_error)
                    return CorrectionIntent(
                        id="",
                        project_id=state.project_id,
                        job_id=state.job_id,
                        raw_text=raw_text,
                        affected_nodes=[CorrectionScope.PLAN, CorrectionScope.EXECUTE],
                        patch={},
                        confidence=0.0,
                    )

    return CorrectionIntent(
        id="",
        project_id=state.project_id,
        job_id=state.job_id,
        raw_text=raw_text,
        affected_nodes=[CorrectionScope.PLAN, CorrectionScope.EXECUTE],
        patch={},
        confidence=0.0,
    )