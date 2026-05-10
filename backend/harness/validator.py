"""Schema and semantic validation helpers for node boundaries."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from backend.schemas.edit_script import EditScript


TModel = TypeVar("TModel", bound=BaseModel)


class SemanticValidationError(ValueError):
    """Raised when an object is structurally valid but semantically unusable."""


def validate_schema(model_type: type[TModel], payload: Any) -> TModel:
    return model_type.model_validate(payload)


def validate_edit_script(script: EditScript, known_asset_ids: set[str] | None = None) -> EditScript:
    if known_asset_ids is not None:
        missing = {segment.asset_id for segment in script.segments if segment.asset_id not in known_asset_ids}
        if missing:
            raise SemanticValidationError(f"EditScript references unknown assets: {sorted(missing)}")
    if not script.segments or script.estimated_duration <= 0:
        raise SemanticValidationError("EditScript estimated duration must be greater than zero")
    return script


def validation_error_text(exc: ValidationError | SemanticValidationError) -> str:
    if isinstance(exc, ValidationError):
        return exc.json()
    return str(exc)

