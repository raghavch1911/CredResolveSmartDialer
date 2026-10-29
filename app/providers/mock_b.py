
import random

from app.providers.base import TelecomProvider


class MockProviderB(TelecomProvider):
    """Less reliable provider with simulated timeouts and duplicate events."""

    def __init__(self, failure_rate=0.15, duplicate_rate=0.30):
        self.failure_rate = failure_rate
        self.duplicate_rate = duplicate_rate

    def initiate_call(self, call_id: int, idempotency_key: str) -> dict:
        if random.random() < self.failure_rate:
            raise TimeoutError("Mock provider B timed out")

        result = {
            "provider": "mock_b",
            "provider_call_id": f"B-{idempotency_key}",
            "status": "INITIATED",
            "latency_ms": 500,
        }

        result["duplicate_event_simulated"] = (
            random.random() < self.duplicate_rate
        )
        return result
