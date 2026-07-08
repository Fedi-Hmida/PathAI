from __future__ import annotations

import pytest

from app.llm import (
    FakeLLMClient,
    FakeLLMScenario,
    LLMOutputParseError,
    LLMOutputValidationError,
    LLMProviderError,
    LLMTimeoutError,
    StructuredOutputRequest,
)
from app.schemas.llm_spike import MiniKnowledgeMapOutput


@pytest.mark.asyncio
async def test_fake_client_returns_valid_structured_output() -> None:
    client = FakeLLMClient()
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    result = await client.generate_structured(request, MiniKnowledgeMapOutput)

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    assert client.call_count == 1


@pytest.mark.asyncio
async def test_fake_client_supports_fenced_json_response() -> None:
    client = FakeLLMClient(scenario=FakeLLMScenario.FENCED_JSON)
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    result = await client.generate_structured(request, MiniKnowledgeMapOutput)

    assert result.summary


@pytest.mark.asyncio
async def test_fake_client_invalid_json_is_rejected() -> None:
    client = FakeLLMClient(scenario=FakeLLMScenario.INVALID_JSON)
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    with pytest.raises(LLMOutputParseError):
        await client.generate_structured(request, MiniKnowledgeMapOutput)


@pytest.mark.asyncio
async def test_fake_client_schema_invalid_json_is_rejected() -> None:
    client = FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON)
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    with pytest.raises(LLMOutputValidationError):
        await client.generate_structured(request, MiniKnowledgeMapOutput)


@pytest.mark.asyncio
async def test_fake_client_timeout_and_provider_error_are_sanitized() -> None:
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    with pytest.raises(LLMTimeoutError):
        await FakeLLMClient(scenario=FakeLLMScenario.TIMEOUT).generate(request)
    with pytest.raises(LLMProviderError):
        await FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR).generate(request)
