from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class InMemoryRateLimiter:
    def __init__(
        self,
        requests_per_minute: int,
        clock: Callable[[], float] = monotonic,
        window_seconds: int = 60,
    ) -> None:
        self.requests_per_minute = requests_per_minute
        self.clock = clock
        self.window_seconds = window_seconds
        self._buckets: dict[str, tuple[float, int]] = {}

    def check(self, key: str) -> RateLimitResult:
        now = self.clock()
        window_start, count = self._buckets.get(key, (now, 0))
        if now - window_start >= self.window_seconds:
            window_start = now
            count = 0
        count += 1
        self._buckets[key] = (window_start, count)
        remaining = max(0, self.requests_per_minute - count)
        if count <= self.requests_per_minute:
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                retry_after_seconds=0,
            )
        retry_after = max(1, int(self.window_seconds - (now - window_start)))
        return RateLimitResult(
            allowed=False,
            remaining=0,
            retry_after_seconds=retry_after,
        )

    def clear(self) -> None:
        self._buckets.clear()
