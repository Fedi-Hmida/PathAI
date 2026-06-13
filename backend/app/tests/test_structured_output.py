import pytest

from app.llm.errors import InvalidJSONError, SchemaValidationError
from app.llm.mock import MockLLMClient
from app.llm.structured import generate_structured, parse_structured_output
from app.llm.types import LLMHealthCheckOutput, LLMMessage


@pytest.mark.asyncio
async def test_generate_structured_success_with_mock_client() -> None:
    client = MockLLMClient(
        responses=['{"status":"ok","message":"structured output works","model":"mock"}']
    )

    output = await generate_structured(
        client=client,
        messages=[LLMMessage(role="user", content="return json")],
        output_model=LLMHealthCheckOutput,
    )

    assert output.status == "ok"
    assert output.model == "mock"


def test_structured_output_invalid_json_raises_clear_error() -> None:
    with pytest.raises(InvalidJSONError):
        parse_structured_output("not json", LLMHealthCheckOutput)


def test_structured_output_schema_mismatch_raises_clear_error() -> None:
    with pytest.raises(SchemaValidationError):
        parse_structured_output('{"status":"bad","message":"wrong"}', LLMHealthCheckOutput)


def test_structured_output_accepts_fenced_json() -> None:
    output = parse_structured_output(
        '```json\n{"status":"ok","message":"inside fence"}\n```',
        LLMHealthCheckOutput,
    )

    assert output.status == "ok"
