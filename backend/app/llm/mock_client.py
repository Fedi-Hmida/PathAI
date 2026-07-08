from __future__ import annotations

from pydantic import BaseModel

from app.llm.contracts import StructuredModel, StructuredOutputRequest
from app.llm.fake_client import FakeLLMClient, fake_payload_for_schema


class MockLLMClient(FakeLLMClient):
    def __init__(self) -> None:
        super().__init__(provider="mock", model="deterministic-spike")

    async def generate_structured(
        self,
        request: StructuredOutputRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        return await super().generate_structured(request, output_schema)

    def _payload_for_schema(self, output_schema: type[BaseModel]) -> dict[str, object]:
        return fake_payload_for_schema(output_schema)
