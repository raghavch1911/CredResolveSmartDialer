
from dataclasses import dataclass

from app.database import get_db


@dataclass
class SafetyDecision:
    approved: int
    requested: int
    reason: str


class SafetyController:
    def evaluate(self, requested: int, provider_healthy: bool = True):
        if requested <= 0:
            return SafetyDecision(0, requested, "No calls requested")

        if not provider_healthy:
            return SafetyDecision(0, requested, "Provider unhealthy")

        with get_db() as connection:
            available_agents = connection.execute(
                "SELECT COUNT(*) FROM agents WHERE status = 'AVAILABLE'"
            ).fetchone()[0]

            queued_borrowers = connection.execute(
                "SELECT COUNT(*) FROM borrowers WHERE status = 'QUEUED'"
            ).fetchone()[0]

        approved = min(requested, available_agents, queued_borrowers)

        return SafetyDecision(
            approved=approved,
            requested=requested,
            reason=(
                "Approved within capacity"
                if approved == requested
                else "Reduced to available capacity"
            ),
        )
