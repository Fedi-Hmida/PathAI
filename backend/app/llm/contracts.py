from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, Field

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class LLMModelMetadata(BaseModel):
    provider: str = Field(default="fake", min_length=1, max_length=80)
    model: str = Field(default="deterministic-fake", min_length=1, max_length=120)
    mode: str = Field(default="fake", min_length=1, max_length=40)


class LLMTimeoutPolicy(BaseModel):
    timeout_seconds: int = Field(default=45, ge=1, le=300)


class LLMRetryPolicy(BaseModel):
    max_attempts: int = Field(default=2, ge=1, le=5)
    retry_on_timeout: bool = True
    retry_on_provider_error: bool = True
    retry_on_parse_error: bool = True
    backoff_seconds: float = Field(default=0.0, ge=0.0, le=30.0)


class StructuredOutputRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    schema_name: str = Field(min_length=1, max_length=160)
    request_id: str | None = Field(default=None, max_length=120)
    metadata: LLMModelMetadata = Field(default_factory=LLMModelMetadata)
    timeout: LLMTimeoutPolicy = Field(default_factory=LLMTimeoutPolicy)
    max_output_tokens: int = Field(default=2048, ge=1, le=32000)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class RawLLMResponse(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    text: str = Field(default="", max_length=120000)
    request_id: str | None = Field(default=None, max_length=120)
    finish_reason: str | None = Field(default=None, max_length=80)
    usage: dict[str, int] = Field(default_factory=dict)


class StructuredOutputResponse(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    parsed: BaseModel
    raw_text: str | None = Field(default=None, max_length=120000)


@runtime_checkable
class LLMClient(Protocol):
    async def generate(self, request: StructuredOutputRequest) -> RawLLMResponse:
        ...

    async def generate_structured(
        self,
        request: StructuredOutputRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        ...
