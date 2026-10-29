
from app.services.pacing import PredictivePacingEngine


def test_pacing_recommends_calls():
    engine = PredictivePacingEngine()

    decision = engine.recommend(
        available_agents=5,
        active_calls=2,
        answer_rate=0.5,
        provider_healthy=True,
        max_batch=10,
    )

    assert decision.requested_calls == 10


def test_pacing_stops_when_provider_unhealthy():
    engine = PredictivePacingEngine()

    decision = engine.recommend(
        available_agents=10,
        active_calls=0,
        answer_rate=0.5,
        provider_healthy=False,
    )

    assert decision.requested_calls == 0


def test_pacing_handles_zero_available_agents():
    engine = PredictivePacingEngine()

    decision = engine.recommend(
        available_agents=0,
        active_calls=3,
        answer_rate=0.5,
    )

    assert decision.requested_calls == 0
