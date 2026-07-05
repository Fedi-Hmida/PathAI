from __future__ import annotations

from typing import TypeVar, cast

from pydantic import BaseModel

from app.agents.errors import ControlledAgentFailure

ModelT = TypeVar("ModelT", bound=BaseModel)


def deterministic_output(
    *,
    agent_name: str,
    output: ModelT,
    fail: bool = False,
    malformed: bool = False,
) -> ModelT:
    if fail:
        raise ControlledAgentFailure(agent_name)
    if malformed:
        return cast(ModelT, {"invalid": "payload"})
    return output.model_copy(deep=True)
