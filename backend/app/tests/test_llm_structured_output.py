from __future__ import annotations

import pytest

from app.llm import (
    FakeLLMClient,
    LLMOutputParseError,
    LLMOutputValidationError,
    LLMRetryLimitExceeded,
    LLMRetryPolicy,
    StructuredOutputRequest,
    extract_json_text,
    generate_structured_with_retry,
    parse_structured_output,
)
from app.schemas.llm_spike import MiniKnowledgeMapOutput

VALID_KNOWLEDGE_MAP_JSON = """
{
  "concepts": [
    {
      "concept_id": "retrieval_evaluation",
      "label": "Retrieval evaluation",
      "mastery_score": 0.35,
      "classification": "weak"
    }
  ],
  "summary": "Needs retrieval evaluation practice."
}
"""


def test_parser_accepts_plain_json() -> None:
    result = parse_structured_output(VALID_KNOWLEDGE_MAP_JSON, MiniKnowledgeMapOutput)

    assert result.concepts[0].classification == "weak"


def test_parser_accepts_fenced_json_and_extra_text() -> None:
    raw = f"Use this object:\n```json\n{VALID_KNOWLEDGE_MAP_JSON}\n```\nDone."

    result = parse_structured_output(raw, MiniKnowledgeMapOutput)

    assert result.summary.startswith("Needs")


def test_parser_extracts_balanced_json_from_extra_text() -> None:
    raw = f"prefix {VALID_KNOWLEDGE_MAP_JSON} suffix"

    extracted = extract_json_text(raw)

    assert extracted.strip().startswith("{")


def test_parser_rejects_missing_or_malformed_json() -> None:
    with pytest.raises(LLMOutputParseError):
        parse_structured_output("no json here", MiniKnowledgeMapOutput)
    with pytest.raises(LLMOutputParseError):
        parse_structured_output('{"concepts": [}', MiniKnowledgeMapOutput)


def test_parser_rejects_schema_invalid_json() -> None:
    with pytest.raises(LLMOutputValidationError):
        parse_structured_output('{"concepts": [], "summary": ""}', MiniKnowledgeMapOutput)


@pytest.mark.asyncio
async def test_retry_policy_retries_fake_parse_failure_then_succeeds() -> None:
    client = FakeLLMClient(
        scripted_responses=[
            "not valid JSON {",
            VALID_KNOWLEDGE_MAP_JSON,
        ],
    )
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    result = await generate_structured_with_retry(
        client,
        request,
        MiniKnowledgeMapOutput,
        policy=LLMRetryPolicy(max_attempts=2),
    )

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    assert client.call_count == 2


@pytest.mark.asyncio
async def test_retry_policy_fails_closed_after_limit() -> None:
    client = FakeLLMClient(scripted_responses=["not valid JSON {"])
    request = StructuredOutputRequest(
        prompt="demo",
        schema_name=MiniKnowledgeMapOutput.__name__,
    )

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client,
            request,
            MiniKnowledgeMapOutput,
            policy=LLMRetryPolicy(max_attempts=2),
        )
