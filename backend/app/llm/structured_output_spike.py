from __future__ import annotations

from app.core.settings import Settings
from app.llm.contracts import StructuredModel, StructuredOutputRequest
from app.llm.live_client import run_live_structured_output_smoke
from app.llm.mock_client import MockLLMClient


async def run_mock_structured_output_spike(
    output_schema: type[StructuredModel],
) -> StructuredModel:
    client = MockLLMClient()
    request = StructuredOutputRequest(
        prompt="Return a tiny valid JSON object for the requested schema.",
        schema_name=output_schema.__name__,
    )
    return await client.generate_structured(request, output_schema)


async def run_optional_live_structured_output_spike(
    settings: Settings,
    output_schema: type[StructuredModel],
) -> StructuredModel:
    return await run_live_structured_output_smoke(settings, output_schema)


def parse_structured_payload(
    payload: object,
    output_schema: type[StructuredModel],
) -> StructuredModel:
    return output_schema.model_validate(payload)
