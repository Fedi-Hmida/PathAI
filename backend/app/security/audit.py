from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.security.redaction import redact_mapping


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1, max_length=120)
    request_id: str = Field(min_length=1, max_length=120)
    route: str = Field(min_length=1, max_length=500)
    method: str = Field(min_length=1, max_length=20)
    status_code: int = Field(ge=100, le=599)
    actor: str = Field(default="anonymous_demo", min_length=1, max_length=120)
    metadata: dict[str, object] = Field(default_factory=dict)
    timestamp: datetime


def build_audit_event(
    *,
    event_type: str,
    request_id: str,
    route: str,
    method: str,
    status_code: int,
    metadata: dict[str, object] | None = None,
    timestamp: datetime,
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        request_id=request_id,
        route=route,
        method=method,
        status_code=status_code,
        metadata=redact_mapping(metadata or {}),
        timestamp=timestamp,
    )


def audit_event_to_log_extra(event: AuditEvent) -> dict[str, Any]:
    return {
        "event_type": event.event_type,
        "request_id": event.request_id,
        "route": event.route,
        "method": event.method,
        "status_code": event.status_code,
        "actor": event.actor,
        "metadata": event.metadata,
        "timestamp": event.timestamp.isoformat(),
    }
