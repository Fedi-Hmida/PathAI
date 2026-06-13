from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorPayload


class MessageResponse(BaseModel):
    message: str
