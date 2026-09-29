"""Thread-safe token-bucket rate limiting."""

import time
from collections.abc import Callable
from threading import Lock


class TokenBucket:
    def __init__(
        self,
        refill_rate: float = 8.0,
        capacity: int = 8,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if refill_rate <= 0:
            raise ValueError("refill_rate must be greater than zero")
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        self._refill_rate = refill_rate
        self._capacity = float(capacity)
        self._tokens = float(capacity)
        self._clock = clock
        self._sleeper = sleeper
        self._updated_at = clock()
        self._lock = Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = self._clock()
                elapsed = max(0.0, now - self._updated_at)
                self._tokens = min(
                    self._capacity,
                    self._tokens + elapsed * self._refill_rate,
                )
                self._updated_at = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait_seconds = (1.0 - self._tokens) / self._refill_rate
            self._sleeper(wait_seconds)