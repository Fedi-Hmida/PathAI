from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.agents.errors import AgentOutputValidationError
from app.repositories.errors import DuplicateRecordError

ModelT = TypeVar("ModelT", bound=BaseModel)


def validate_agent_output(
    *,
    agent_name: str,
    schema: type[ModelT],
    payload: object,
) -> ModelT:
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise AgentOutputValidationError(agent_name) from exc


def create_or_get(
    *,
    create: Callable[[ModelT], ModelT],
    get: Callable[[str], ModelT],
    record: ModelT,
    record_id: str,
) -> ModelT:
    try:
        return create(record)
    except DuplicateRecordError:
        return get(record_id)


def create_or_replace(
    *,
    create: Callable[[ModelT], ModelT],
    save: Callable[[ModelT], ModelT],
    record: ModelT,
) -> ModelT:
    """Create a record under its (possibly caller-chosen) ID, or overwrite it
    in place if that ID is already taken - unlike `create_or_get`, which
    discards the newly built record in favor of whatever already exists.
    Fits per-user regeneration: the first call mints a fresh ID (create), a
    repeat call reuses the goal's existing ID and must persist the newly
    regenerated content (save), not silently keep the stale one."""
    try:
        return create(record)
    except DuplicateRecordError:
        return save(record)
