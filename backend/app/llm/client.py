from typing import Protocol, TypeVar

from pydantic import BaseModel

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class StructuredOutputRequest(BaseModel):
    prompt: str
    schema_name: str


class StructuredOutputResponse(BaseModel):
    provider: str
    model: str
    parsed: BaseModel
    raw_text: str | None = None


class LLMClient(Protocol):
    async def generate_structured(
        self,
        request: StructuredOutputRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        ...

