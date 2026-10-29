
from app.services.circuit_breaker import CircuitBreaker


def test_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=3)

    assert breaker.allow_request()

    breaker.record_failure()
    breaker.record_failure()

    assert breaker.state == "CLOSED"

    breaker.record_failure()

    assert breaker.state == "OPEN"
    assert not breaker.allow_request()


def test_success_resets_breaker():
    breaker = CircuitBreaker(failure_threshold=2)

    breaker.record_failure()
    breaker.record_success()

    assert breaker.state == "CLOSED"
    assert breaker.failures == 0
    assert breaker.allow_request()
