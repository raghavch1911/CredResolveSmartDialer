
from app.database import get_db
from app.providers.mock_a import MockProviderA
from app.providers.mock_b import MockProviderB
from app.services.dialer import ProgressiveDialer, AllocationError
from app.services.safety import SafetyController
from app.services.circuit_breaker import CircuitBreaker


class CallService:
    def __init__(self):
        self.dialer = ProgressiveDialer()
        self.safety = SafetyController()

        self.providers = {
            "mock_a": MockProviderA(),
            "mock_b": MockProviderB(),
        }

        self.breakers = {
            name: CircuitBreaker()
            for name in self.providers
        }

    def initiate(self, provider_name="mock_a"):
        if provider_name not in self.providers:
            raise ValueError("Unknown provider")

        breaker = self.breakers[provider_name]

        if not breaker.allow_request():
            raise AllocationError(
                f"Provider circuit is {breaker.state}"
            )

        decision = self.safety.evaluate(
            requested=1,
            provider_healthy=True,
        )

        if decision.approved < 1:
            raise AllocationError(decision.reason)

        allocation = self.dialer.allocate_call(provider_name)
        provider = self.providers[provider_name]

        try:
            result = provider.initiate_call(
                allocation["call_id"],
                allocation["idempotency_key"],
            )
        except TimeoutError:
            breaker.record_failure()

            # Keep the call and agent reserved until reconciliation.
            raise

        breaker.record_success()

        with get_db() as connection:
            connection.execute(
                """
                UPDATE calls
                SET status = 'INITIATED',
                    provider_call_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'RESERVED'
                """,
                (result["provider_call_id"], allocation["call_id"]),
            )

            connection.execute(
                """
                UPDATE agents SET status = 'DIALING'
                WHERE id = ? AND status = 'RESERVED'
                """,
                (allocation["agent_id"],),
            )

        return {
            **allocation,
            "provider_result": result,
            "circuit_state": breaker.state,
        }

    def provider_health(self):
        return {
            name: {
                "state": breaker.state,
                "failures": breaker.failures,
                "request_allowed": breaker.allow_request(),
            }
            for name, breaker in self.breakers.items()
        }
