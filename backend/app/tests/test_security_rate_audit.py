from datetime import UTC, datetime

from app.security.audit import build_audit_event
from app.security.rate_limit import InMemoryRateLimiter


def test_in_memory_rate_limiter_allows_then_blocks_after_threshold() -> None:
    now = 10.0

    def clock() -> float:
        return now

    limiter = InMemoryRateLimiter(requests_per_minute=2, clock=clock, window_seconds=60)

    assert limiter.check("client-a").allowed is True
    assert limiter.check("client-a").allowed is True
    blocked = limiter.check("client-a")
    assert blocked.allowed is False
    assert blocked.retry_after_seconds > 0


def test_in_memory_rate_limiter_resets_window() -> None:
    timestamps = iter([0.0, 1.0, 61.0])
    limiter = InMemoryRateLimiter(
        requests_per_minute=1,
        clock=lambda: next(timestamps),
        window_seconds=60,
    )

    assert limiter.check("client-a").allowed is True
    assert limiter.check("client-a").allowed is False
    assert limiter.check("client-a").allowed is True


def test_audit_event_shape_redacts_metadata() -> None:
    event = build_audit_event(
        event_type="http_request",
        request_id="req_test",
        route="/api/v1/dev/models",
        method="GET",
        status_code=200,
        metadata={"api_key": "abc123", "email": "learner@example.test"},
        timestamp=datetime.now(UTC),
    )

    assert event.actor == "anonymous_demo"
    assert event.metadata["api_key"] == "[REDACTED_SECRET]"
    assert event.metadata["email"] == "[REDACTED_EMAIL]"
