
import sqlite3
import uuid

from app.database import get_db
from app.models.states import AgentStatus, CallStatus


class AllocationError(Exception):
    """Raised when a safe call allocation cannot be completed."""


class ProgressiveDialer:
    """Allocate at most one outbound call per available agent."""

    def allocate_call(self, provider="mock_a"):
        with get_db() as connection:
            # Acquire SQLite's write lock before checking availability.
            connection.execute("BEGIN IMMEDIATE")

            agent = connection.execute(
                """
                SELECT id FROM agents
                WHERE status = ?
                ORDER BY id
                LIMIT 1
                """,
                (AgentStatus.AVAILABLE.value,),
            ).fetchone()

            borrower = connection.execute(
                """
                SELECT id FROM borrowers
                WHERE status = 'QUEUED'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

            if agent is None:
                raise AllocationError("No available agent")

            if borrower is None:
                raise AllocationError("No queued borrower")

            key = str(uuid.uuid4())

            # Conditional updates protect against stale selections.
            agent_update = connection.execute(
                """
                UPDATE agents
                SET status = ?, reserved_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = ?
                """,
                (
                    AgentStatus.RESERVED.value,
                    agent["id"],
                    AgentStatus.AVAILABLE.value,
                ),
            )

            if agent_update.rowcount != 1:
                raise AllocationError("Agent reservation failed")

            borrower_update = connection.execute(
                """
                UPDATE borrowers
                SET status = 'RESERVED'
                WHERE id = ? AND status = 'QUEUED'
                """,
                (borrower["id"],),
            )

            if borrower_update.rowcount != 1:
                raise AllocationError("Borrower reservation failed")

            cursor = connection.execute(
                """
                INSERT INTO calls (
                    agent_id, borrower_id, provider,
                    status, idempotency_key
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    agent["id"],
                    borrower["id"],
                    provider,
                    CallStatus.RESERVED.value,
                    key,
                ),
            )

            return {
                "call_id": cursor.lastrowid,
                "agent_id": agent["id"],
                "borrower_id": borrower["id"],
                "provider": provider,
                "status": CallStatus.RESERVED.value,
                "idempotency_key": key,
            }
