from __future__ import annotations

import pytest

from app.llm import (
    FakeLLMClient,
    FakeLLMScenario,
    LLMRetryLimitExceeded,
    LLMRetryPolicy,
    StructuredOutputRequest,
    generate_structured_with_retry,
)
from app.llm.observability.sinks import CountingObserver
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


def _request() -> StructuredOutputRequest:
    return StructuredOutputRequest(prompt="demo", schema_name=MiniKnowledgeMapOutput.__name__)


@pytest.mark.asyncio
async def test_provider_error_records_attempt_per_try_and_one_retry_exhausted() -> None:
    client = FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR)
    observer = CountingObserver()
    policy = LLMRetryPolicy(max_attempts=3)

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client,
            _request(),
            MiniKnowledgeMapOutput,
            policy=policy,
            observer=observer,
        )

    summary = observer.safe_summary()
    counts = summary["counts_by_event_type"]
    assert counts == {"attempt_started": 3, "attempt_failed": 3, "retry_exhausted": 1}
    assert client.call_count == 3


@pytest.mark.asyncio
async def test_fail_then_succeed_records_one_failed_and_one_succeeded() -> None:
    client = FakeLLMClient(
        scripted_responses=[
            "not valid JSON {",
            VALID_KNOWLEDGE_MAP_JSON,
        ],
    )
    observer = CountingObserver()

    result = await generate_structured_with_retry(
        client,
        _request(),
        MiniKnowledgeMapOutput,
        policy=LLMRetryPolicy(max_attempts=2),
        observer=observer,
    )

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    summary = observer.safe_summary()
    assert summary["counts_by_event_type"] == {
        "attempt_started": 2,
        "attempt_failed": 1,
        "succeeded": 1,
    }


@pytest.mark.asyncio
async def test_retry_limit_exceeded_contract_unchanged_with_observer() -> None:
    policy = LLMRetryPolicy(max_attempts=2)

    with pytest.raises(LLMRetryLimitExceeded) as exc_without_observer:
        await generate_structured_with_retry(
            FakeLLMClient(scripted_responses=["not valid JSON {"]),
            _request(),
            MiniKnowledgeMapOutput,
            policy=policy,
        )

    with pytest.raises(LLMRetryLimitExceeded) as exc_with_observer:
        await generate_structured_with_retry(
            FakeLLMClient(scripted_responses=["not valid JSON {"]),
            _request(),
            MiniKnowledgeMapOutput,
            policy=policy,
            observer=CountingObserver(),
        )

    assert str(exc_without_observer.value) == str(exc_with_observer.value)


@pytest.mark.asyncio
async def test_default_no_observer_path_is_unaffected() -> None:
    client = FakeLLMClient(
        scripted_responses=[
            "not valid JSON {",
            VALID_KNOWLEDGE_MAP_JSON,
        ],
    )

    result = await generate_structured_with_retry(
        client,
        _request(),
        MiniKnowledgeMapOutput,
        policy=LLMRetryPolicy(max_attempts=2),
    )

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    assert client.call_count == 2
