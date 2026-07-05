from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

Score: TypeAlias = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveScore: TypeAlias = Annotated[float, Field(gt=0.0, le=1.0)]
NonEmptyString: TypeAlias = Annotated[str, Field(min_length=1)]
SchemaVersion: TypeAlias = Annotated[str, Field(pattern=r"^\d+\.\d+$")]


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TimestampedDTO(BaseSchema):
    created_at: datetime
    updated_at: datetime


class VersionedDTO(BaseSchema):
    schema_version: SchemaVersion = "1.0"


class TraceMetadata(BaseSchema):
    request_id: str | None = Field(default=None, max_length=120)
    run_id: str | None = Field(default=None, max_length=120)
    node_name: str | None = Field(default=None, max_length=120)


class WorkflowError(BaseSchema):
    error_code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)
    category: str = Field(min_length=1, max_length=80)
    retryable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowWarning(BaseSchema):
    warning_code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
