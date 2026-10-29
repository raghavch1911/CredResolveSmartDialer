
from app.providers.base import TelecomProvider


class MockProviderA(TelecomProvider):
    """Fast, reliable provider for local simulation."""

    def initiate_call(self, call_id: int, idempotency_key: str) -> dict:
        return {
            "provider": "mock_a",
            "provider_call_id": f"A-{idempotency_key}",
            "status": "INITIATED",
            "latency_ms": 100,
        }
