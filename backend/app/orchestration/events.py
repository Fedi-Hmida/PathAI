from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.base import WorkflowError, WorkflowWarning
from app.schemas.enums import NodeResultStatus
from app.schemas.ids import RunId
from app.schemas.orchestration import WorkflowNodeEvent


def node_completed_event(
    *,
    run_id: RunId,
    node_name: str,
    message: str | None = None,
    warnings: list[WorkflowWarning] | None = None,
    created_at: datetime | None = None,
) -> WorkflowNodeEvent:
    return WorkflowNodeEvent(
        run_id=run_id,
        node_name=node_name,
        status=NodeResultStatus.SUCCESS,
        message=message,
        created_at=created_at or _now(),
        warnings=warnings or [],
    )


def node_failed_event(
    *,
    run_id: RunId,
    node_name: str,
    error: WorkflowError,
    message: str | None = None,
    created_at: datetime | None = None,
) -> WorkflowNodeEvent:
    return WorkflowNodeEvent(
        run_id=run_id,
        node_name=node_name,
        status=NodeResultStatus.FAILED,
        message=message or "orchestration node failed",
        created_at=created_at or _now(),
        errors=[error],
    )


def safe_workflow_error(node_name: str) -> WorkflowError:
    return WorkflowError(
        error_code="orchestration_node_failed",
        message=f"Node failed: {node_name}",
        category="orchestration",
        retryable=False,
    )


def safe_agent_workflow_error(agent_name: str) -> WorkflowError:
    return WorkflowError(
        error_code="agent_step_failed",
        message=f"Agent step failed: {agent_name}",
        category="agent",
        retryable=False,
        metadata={"agent_name": agent_name},
    )


def _now() -> datetime:
    return datetime.now(tz=UTC)
