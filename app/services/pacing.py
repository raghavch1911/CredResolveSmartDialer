
from dataclasses import dataclass
import math


@dataclass
class PacingDecision:
    requested_calls: int
    answer_rate: float
    available_agents: int
    active_calls: int
    provider_healthy: bool
    reason: str


class PredictivePacingEngine:
    """Rule-based pacing recommendation; never initiates calls."""

    def recommend(
        self,
        available_agents: int,
        active_calls: int,
        answer_rate: float,
        provider_healthy: bool = True,
        ringing_calls: int = 0,
        max_batch: int = 20,
    ) -> PacingDecision:

        answer_rate = max(0.01, min(answer_rate, 1.0))
        available_agents = max(0, available_agents)
        active_calls = max(0, active_calls)
        ringing_calls = max(0, ringing_calls)

        if not provider_healthy:
            requested = 0
            reason = "Provider unhealthy; pause new dialing"
        elif available_agents == 0:
            requested = 0
            reason = "No available agents"
        else:
            # Estimate additional attempts using the answer probability.
            # The safety controller will independently cap this estimate.
            estimated_need = math.ceil(
                (available_agents + ringing_calls) / answer_rate
            )
            requested = min(max_batch, estimated_need)
            reason = (
                f"Estimated from answer rate {answer_rate:.0%}; "
                f"{ringing_calls} calls already ringing and "
                f"{active_calls} active calls"
            )

        return PacingDecision(
            requested_calls=requested,
            answer_rate=answer_rate,
            available_agents=available_agents,
            active_calls=active_calls,
            provider_healthy=provider_healthy,
            reason=reason,
        )
