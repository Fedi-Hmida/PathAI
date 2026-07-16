from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

from app.llm.contracts import LLMClient, LLMRetryPolicy, StructuredModel, StructuredOutputRequest
from app.llm.errors import (
    LLMError,
    LLMOutputParseError,
    LLMOutputValidationError,
    LLMProviderError,
    LLMRetryLimitExceeded,
    LLMRunBudgetExhaustedError,
    LLMTimeoutError,
)
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.observability.observer import LLMReliabilityObserver, NullObserver
from app.llm.structured_output import build_repair_request

_SELF_CORRECTION_REASON = "self_correction_repair"


@runtime_checkable
class _ExhaustionAwareObserver(Protocol):
    """Structural marker for an observer that can report a run-level ceiling.

    Deliberately not part of `LLMReliabilityObserver` itself — every sink
    (`NullObserver`, `CountingObserver`, `LoggingObserver`) only records
    events and has no notion of exhaustion. Only `RunScopedBudgetObserver`
    (Rebuild-22) satisfies this structurally.
    """

    def exhausted(self) -> bool: ...


async def generate_structured_with_retry(
    client: LLMClient,
    request: StructuredOutputRequest,
    output_schema: type[StructuredModel],
    *,
    policy: LLMRetryPolicy | None = None,
    observer: LLMReliabilityObserver | None = None,
) -> StructuredModel:
    retry_policy = policy or LLMRetryPolicy()
    reliability_observer = observer or NullObserver()
    schema_name = output_schema.__name__
    provider = request.metadata.provider
    mode = request.metadata.mode

    if (
        isinstance(reliability_observer, _ExhaustionAwareObserver)
        and reliability_observer.exhausted()
    ):
        # A skipped call is not an attempt — bail before the loop starts, so
        # no ATTEMPT_STARTED is recorded for a call that was never made.
        raise LLMRunBudgetExhaustedError(
            "Run-level LLM call budget exhausted before this call could start.",
            provider=provider,
        )

    # Transient retries (timeout/provider/parse) and validation self-corrections
    # are budgeted independently: the effective attempt ceiling is the sum, so a
    # validation repair is never stolen from — or blocked by — the transient
    # retry budget (or vice versa).
    effective_ceiling = retry_policy.max_attempts + retry_policy.max_self_corrections
    last_error: LLMError | None = None
    reason_code: str | None = None
    transient_retries_used = 0
    self_corrections_used = 0
    attempt = 0
    while True:
        attempt += 1
        reliability_observer.record(
            LLMReliabilityEvent(
                event_type=LLMReliabilityEventType.ATTEMPT_STARTED,
                schema_name=schema_name,
                attempt=attempt,
                max_attempts=effective_ceiling,
                provider=provider,
                mode=mode,
                reason_code=reason_code,
            ),
        )
        try:
            result = await client.generate_structured(request, output_schema)
        except LLMError as exc:
            last_error = exc
            reliability_observer.record(
                LLMReliabilityEvent(
                    event_type=LLMReliabilityEventType.ATTEMPT_FAILED,
                    schema_name=schema_name,
                    attempt=attempt,
                    max_attempts=effective_ceiling,
                    error_code=exc.error_code,
                    provider=provider,
                    mode=mode,
                    reason_code=reason_code,
                ),
            )
            if _run_budget_exhausted(reliability_observer):
                # The run-level ceiling (Rebuild-22) was hit by this attempt;
                # neither a transient retry nor a self-correction may exceed it.
                break
            if (
                isinstance(exc, LLMOutputValidationError)
                and retry_policy.self_correct_on_validation_error
                and self_corrections_used < retry_policy.max_self_corrections
            ):
                self_corrections_used += 1
                request = build_repair_request(
                    request,
                    exc,
                    temperature=retry_policy.self_correction_temperature,
                )
                reason_code = _SELF_CORRECTION_REASON
                # A self-correction is an immediate, different-prompt repair —
                # backoff (meant to space out transient infra retries) is skipped.
                continue
            if (
                transient_retries_used < retry_policy.max_attempts - 1
                and _should_retry(exc, retry_policy)
            ):
                transient_retries_used += 1
                reason_code = None
                if retry_policy.backoff_seconds > 0:
                    await asyncio.sleep(retry_policy.backoff_seconds)
                continue
            break
        else:
            reliability_observer.record(
                LLMReliabilityEvent(
                    event_type=LLMReliabilityEventType.SUCCEEDED,
                    schema_name=schema_name,
                    attempt=attempt,
                    max_attempts=effective_ceiling,
                    provider=provider,
                    mode=mode,
                    reason_code=reason_code,
                ),
            )
            return result
    detail = last_error.safe_message if last_error else "Unknown LLM retry failure."
    reliability_observer.record(
        LLMReliabilityEvent(
            event_type=LLMReliabilityEventType.RETRY_EXHAUSTED,
            schema_name=schema_name,
            attempt=attempt,
            max_attempts=effective_ceiling,
            error_code=last_error.error_code if last_error else None,
            provider=provider,
            mode=mode,
        ),
    )
    raise LLMRetryLimitExceeded(f"LLM retry limit exceeded: {detail}") from last_error


def _run_budget_exhausted(observer: LLMReliabilityObserver) -> bool:
    return isinstance(observer, _ExhaustionAwareObserver) and observer.exhausted()


def _should_retry(error: LLMError, policy: LLMRetryPolicy) -> bool:
    if isinstance(error, LLMTimeoutError):
        return policy.retry_on_timeout
    if isinstance(error, LLMProviderError):
        return policy.retry_on_provider_error
    if isinstance(error, LLMOutputParseError):
        return policy.retry_on_parse_error
    return False
