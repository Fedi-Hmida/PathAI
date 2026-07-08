from __future__ import annotations

import asyncio

from app.llm.contracts import LLMClient, LLMRetryPolicy, StructuredModel, StructuredOutputRequest
from app.llm.errors import (
    LLMError,
    LLMOutputParseError,
    LLMProviderError,
    LLMRetryLimitExceeded,
    LLMTimeoutError,
)
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.observability.observer import LLMReliabilityObserver, NullObserver


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
    last_error: LLMError | None = None
    for attempt in range(1, retry_policy.max_attempts + 1):
        reliability_observer.record(
            LLMReliabilityEvent(
                event_type=LLMReliabilityEventType.ATTEMPT_STARTED,
                schema_name=schema_name,
                attempt=attempt,
                max_attempts=retry_policy.max_attempts,
                provider=provider,
                mode=mode,
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
                    max_attempts=retry_policy.max_attempts,
                    error_code=exc.error_code,
                    provider=provider,
                    mode=mode,
                ),
            )
            will_retry = attempt < retry_policy.max_attempts and _should_retry(exc, retry_policy)
            if not will_retry:
                break
            if retry_policy.backoff_seconds > 0:
                await asyncio.sleep(retry_policy.backoff_seconds)
        else:
            reliability_observer.record(
                LLMReliabilityEvent(
                    event_type=LLMReliabilityEventType.SUCCEEDED,
                    schema_name=schema_name,
                    attempt=attempt,
                    max_attempts=retry_policy.max_attempts,
                    provider=provider,
                    mode=mode,
                ),
            )
            return result
    detail = last_error.safe_message if last_error else "Unknown LLM retry failure."
    reliability_observer.record(
        LLMReliabilityEvent(
            event_type=LLMReliabilityEventType.RETRY_EXHAUSTED,
            schema_name=schema_name,
            attempt=retry_policy.max_attempts,
            max_attempts=retry_policy.max_attempts,
            error_code=last_error.error_code if last_error else None,
            provider=provider,
            mode=mode,
        ),
    )
    raise LLMRetryLimitExceeded(f"LLM retry limit exceeded: {detail}") from last_error


def _should_retry(error: LLMError, policy: LLMRetryPolicy) -> bool:
    if isinstance(error, LLMTimeoutError):
        return policy.retry_on_timeout
    if isinstance(error, LLMProviderError):
        return policy.retry_on_provider_error
    if isinstance(error, LLMOutputParseError):
        return policy.retry_on_parse_error
    return False
