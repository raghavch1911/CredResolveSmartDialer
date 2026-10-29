
import time
from collections import deque


class CircuitBreaker:
    """Open the circuit after repeated failures; allow a later probe."""

    def __init__(self, failure_threshold=3, recovery_seconds=10):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.opened_at = None
        self.recent_failures = deque(maxlen=20)

    @property
    def state(self):
        if self.opened_at is None:
            return "CLOSED"

        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            return "HALF_OPEN"

        return "OPEN"

    def allow_request(self):
        return self.state != "OPEN"

    def record_success(self):
        self.failures = 0
        self.opened_at = None
        self.recent_failures.clear()

    def record_failure(self):
        self.failures += 1
        self.recent_failures.append(time.monotonic())

        if self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic()
