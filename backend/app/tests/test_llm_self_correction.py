"""Rebuild-31: bounded in-band self-correction for schema-invalid LLM output.

On a validation error the retry loop issues ONE additional repair attempt whose
prompt carries a secret-free field-level hint, budgeted INDEPENDENTLY of the
transient (timeout/provider/parse) `max_attempts` budget. Once the self-
correction budget is exhausted it still fails loud (Rebuild-30). Fully offline.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.agents.llm.retry_policy_selection import resolve_retry_policy
from app.core.settings import Settings
from app.llm import (
    FakeLLMClient,
    FakeLLMScenario,
    LLMRetryLimitExceeded,
    LLMRetryPolicy,
    StructuredOutputRequest,
    generate_structured_with_retry,
)
from app.llm.errors import LLMOutputValidationError
from app.llm.observability.budget import RunBudget, RunScopedBudgetObserver
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.structured_output import _build_validation_repair_hint, build_repair_request
from app.schemas.llm_spike import MiniKnowledgeMapOutput

_SCHEMA_INVALID_JSON = json.dumps({"unexpected": []})

_VALID_KNOWLEDGE_MAP_JSON = json.dumps(
    {
        "concepts": [
            {
                "concept_id": "retrieval_evaluation",
                "label": "Retrieval evaluation",
                "mastery_score": 0.35,
                "classification": "weak",
            }
        ],
        "summary": "Needs retrieval evaluation practice.",
    }
)


class _RecordingFakeClient(FakeLLMClient):
    """FakeLLMClient that also records every request it is asked to generate."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.requests: list[StructuredOutputRequest] = []

    async def generate(self, request: StructuredOutputRequest):
        self.requests.append(request)
        return await super().generate(request)


class _EventRecorder:
    def __init__(self) -> None:
        self.events: list[LLMReliabilityEvent] = []

    def record(self, event: LLMReliabilityEvent) -> None:
        self.events.append(event)


def _request() -> StructuredOutputRequest:
    return StructuredOutputRequest(prompt="demo", schema_name=MiniKnowledgeMapOutput.__name__)


@pytest.mark.asyncio
async def test_self_corrects_validation_error_then_succeeds() -> None:
    # max_attempts=1 => zero transient retries: the second attempt exists ONLY
    # because self-correction is budgeted independently.
    client = _RecordingFakeClient(
        scripted_responses=[_SCHEMA_INVALID_JSON, _VALID_KNOWLEDGE_MAP_JSON],
    )

    result = await generate_structured_with_retry(
        client,
        _request(),
        MiniKnowledgeMapOutput,
        policy=LLMRetryPolicy(max_attempts=1),
    )

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    assert client.call_count == 2
    # The repair request is a genuinely different prompt: it appends the
    # self-correction instruction plus the field-level hint (the missing field).
    repair_prompt = client.requests[1].prompt
    assert "previous response was invalid" in repair_prompt
    assert "concepts" in repair_prompt
    # Temperature nudged up only on the repair attempt.
    assert client.requests[0].temperature == 0.0
    assert client.requests[1].temperature == pytest.approx(0.2)


@pytest.mark.asyncio
async def test_repaired_attempt_records_self_correction_reason_code() -> None:
    recorder = _EventRecorder()
    client = _RecordingFakeClient(
        scripted_responses=[_SCHEMA_INVALID_JSON, _VALID_KNOWLEDGE_MAP_JSON],
    )

    await generate_structured_with_retry(
        client,
        _request(),
        MiniKnowledgeMapOutput,
        policy=LLMRetryPolicy(max_attempts=1),
        observer=recorder,
    )

    started = [
        e for e in recorder.events if e.event_type == LLMReliabilityEventType.ATTEMPT_STARTED
    ]
    succeeded = [e for e in recorder.events if e.event_type == LLMReliabilityEventType.SUCCEEDED]
    assert started[0].reason_code is None
    assert started[1].reason_code == "self_correction_repair"
    assert succeeded[0].reason_code == "self_correction_repair"


@pytest.mark.asyncio
async def test_always_invalid_exhausts_self_correction_and_fails_loud() -> None:
    client = FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON)

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client,
            _request(),
            MiniKnowledgeMapOutput,
            policy=LLMRetryPolicy(max_attempts=1),
        )

    # One initial call + exactly one bounded self-correction, then fail loud.
    assert client.call_count == 2


@pytest.mark.asyncio
async def test_self_correction_is_immediate_without_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    client = _RecordingFakeClient(
        scripted_responses=[_SCHEMA_INVALID_JSON, _VALID_KNOWLEDGE_MAP_JSON],
    )

    result = await generate_structured_with_retry(
        client,
        _request(),
        MiniKnowledgeMapOutput,
        policy=LLMRetryPolicy(max_attempts=1, backoff_seconds=5.0),
    )

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    # A repair is a fresh-prompt in-band retry — no transient backoff delay.
    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_self_correction_disabled_makes_validation_non_retryable() -> None:
    client = FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON)

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client,
            _request(),
            MiniKnowledgeMapOutput,
            policy=LLMRetryPolicy(max_attempts=3, self_correct_on_validation_error=False),
        )

    assert client.call_count == 1


@pytest.mark.asyncio
async def test_self_correction_cannot_exceed_run_budget() -> None:
    # A run ceiling of one call: the first attempt exhausts it, so the bounded
    # self-correction (Rebuild-22 budget) may not add a second call.
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1))
    client = FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON)

    with pytest.raises(LLMRetryLimitExceeded):
        await generate_structured_with_retry(
            client,
            _request(),
            MiniKnowledgeMapOutput,
            policy=LLMRetryPolicy(max_attempts=1),
            observer=observer,
        )

    assert client.call_count == 1


def test_repair_hint_is_secret_free_and_drops_input_values() -> None:
    sentinel = "topsecretanswer"  # short enough to survive redaction if present
    try:
        MiniKnowledgeMapOutput.model_validate({"concepts": sentinel, "summary": "ok"})
    except ValidationError as exc:
        hint = _build_validation_repair_hint(exc)
    else:  # pragma: no cover - the payload is deliberately invalid
        raise AssertionError("expected a ValidationError")

    # The hint names the failing field and error, but never echoes the offending
    # input value (pydantic include_input=False) that could carry user content.
    assert "concepts" in hint
    assert sentinel not in hint

    error = LLMOutputValidationError("invalid", repair_hint=hint)
    repair = build_repair_request(_request(), error, temperature=0.2)
    assert sentinel not in repair.prompt


def test_reliability_event_stays_content_free() -> None:
    # The reliability event schema must not have any field that could carry a
    # prompt / raw output / repair hint — only a bounded reason_code string.
    event = LLMReliabilityEvent(
        event_type=LLMReliabilityEventType.ATTEMPT_STARTED,
        schema_name=MiniKnowledgeMapOutput.__name__,
        attempt=2,
        max_attempts=2,
        reason_code="self_correction_repair",
    )
    field_names = set(type(event).model_fields)
    assert "prompt" not in field_names
    assert "repair_hint" not in field_names
    assert "raw_text" not in field_names


def test_resolve_retry_policy_defaults_self_correction_on() -> None:
    policy = resolve_retry_policy(Settings())

    assert policy.self_correct_on_validation_error is True
    assert policy.max_self_corrections == 1
    assert policy.self_correction_temperature == pytest.approx(0.2)
