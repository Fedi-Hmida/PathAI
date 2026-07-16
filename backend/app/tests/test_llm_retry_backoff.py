from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.llm import (
    FakeLLMClient,
    FakeLLMScenario,
    LLMRetryLimitExceeded,
    LLMRetryPolicy,
    StructuredOutputRequest,
    generate_structured_with_retry,
)
from app.schemas.llm_spike import MiniKnowledgeMapOutput


def _request() -> StructuredOutputRequest:
    return StructuredOutputRequest(prompt="demo", schema_name=MiniKnowledgeMapOutput.__name__)


@pytest.mark.asyncio
async def test_backoff_sleeps_between_retries_not_after_final_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    client = FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR)
    policy = LLMRetryPolicy(max_attempts=3, backoff_seconds=2.0)

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client, _request(), MiniKnowledgeMapOutput, policy=policy,
        )

    assert sleep_mock.await_count == 2
    for call in sleep_mock.await_args_list:
        assert call.args == (2.0,)


@pytest.mark.asyncio
async def test_zero_backoff_never_sleeps(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    client = FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR)
    policy = LLMRetryPolicy(max_attempts=3, backoff_seconds=0.0)

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client, _request(), MiniKnowledgeMapOutput, policy=policy,
        )

    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_retryable_error_does_not_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    client = FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON)
    # With self-correction disabled, a schema-invalid (validation) error is
    # genuinely non-retryable: a single call, no backoff sleep. (Self-correction
    # ON is covered in test_llm_self_correction.py.)
    policy = LLMRetryPolicy(
        max_attempts=3,
        backoff_seconds=5.0,
        self_correct_on_validation_error=False,
    )

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client, _request(), MiniKnowledgeMapOutput, policy=policy,
        )

    sleep_mock.assert_not_awaited()
    assert client.call_count == 1
