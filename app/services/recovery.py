
from app.database import get_db


def find_stale_calls(age_seconds=60):
    """Find uncertain calls for reconciliation, without redialing."""
    with get_db() as connection:
        rows = connection.execute(
            """
            SELECT
                c.id AS call_id,
                c.agent_id,
                c.borrower_id,
                c.provider,
                c.status,
                c.idempotency_key,
                c.created_at
            FROM calls c
            WHERE c.status IN ('RESERVED', 'INITIATED', 'RINGING')
              AND c.created_at <= datetime(
                  'now', ?
              )
            ORDER BY c.id
            """,
            (f"-{max(1, age_seconds)} seconds",),
        ).fetchall()

        return [dict(row) for row in rows]


def reconcile_failed_reservation(call_id: int):
    """Release resources only after confirming no call was initiated."""
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")

        call = connection.execute(
            "SELECT * FROM calls WHERE id = ?",
            (call_id,),
        ).fetchone()

        if call is None:
            return {"updated": False, "reason": "Call not found"}

        if call["status"] != "RESERVED":
            return {
                "updated": False,
                "reason": "Call is not an unresolved reservation",
            }

        connection.execute(
            """
            UPDATE calls
            SET status = 'FAILED', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'RESERVED'
            """,
            (call_id,),
        )

        connection.execute(
            """
            UPDATE agents
            SET status = 'AVAILABLE', reserved_at = NULL
            WHERE id = ? AND status = 'RESERVED'
            """,
            (call["agent_id"],),
        )

        connection.execute(
            """
            UPDATE borrowers SET status = 'QUEUED'
            WHERE id = ? AND status = 'RESERVED'
            """,
            (call["borrower_id"],),
        )

        return {
            "updated": True,
            "call_id": call_id,
            "status": "FAILED",
        }
