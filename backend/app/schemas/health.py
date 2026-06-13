from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"] = "ready"
    service: str
    version: str
    environment: str
    checks: dict[str, str] = Field(default_factory=dict)
    message: str | None = None
