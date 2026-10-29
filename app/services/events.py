
from app.database import get_db


EVENT_STATUSES = {
    "INITIATED": "INITIATED",
    "RINGING": "RINGING",
    "ANSWERED": "ANSWERED",
    "CONNECTED": "CONNECTED",
    "COMPLETED": "COMPLETED",
    "FAILED": "FAILED",
    "CANCELLED": "CANCELLED",
}

TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}

ALLOWED = {
    "RESERVED": {"INITIATED", "FAILED", "CANCELLED"},
    "INITIATED": {
        "RINGING", "ANSWERED", "CONNECTED",
        "COMPLETED", "FAILED", "CANCELLED",
    },
    "RINGING": {
        "ANSWERED", "CONNECTED", "COMPLETED",
        "FAILED", "CANCELLED",
    },
    "ANSWERED": {"CONNECTED", "COMPLETED", "FAILED"},
    "CONNECTED": {"COMPLETED", "FAILED"},
}


def process_provider_event(
    call_id: int,
    event_id: str,
    event_type: str,
):
    target = EVENT_STATUSES.get(event_type.upper())

    if target is None:
        raise ValueError("Unsupported provider event")

    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")

        # The event ID must be stable across provider redeliveries.
        try:
            connection.execute(
                """
                INSERT INTO provider_events (
                    event_id, call_id, event_type
                )
                VALUES (?, ?, ?)
                """,
                (event_id, call_id, event_type.upper()),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                return {
                    "call_id": call_id,
                    "event_id": event_id,
                    "applied": False,
                    "reason": "Duplicate event",
                }
            raise

        call = connection.execute(
            "SELECT * FROM calls WHERE id = ?",
            (call_id,),
        ).fetchone()

        if call is None:
            raise ValueError("Call not found")

        current = call["status"]

        # Terminal states are never overwritten by late events.
        if current in TERMINAL:
            return {
                "call_id": call_id,
                "status": current,
                "applied": False,
                "reason": "Call is already terminal",
            }

        if target not in ALLOWED.get(current, set()):
            return {
                "call_id": call_id,
                "status": current,
                "applied": False,
                "reason": "Invalid or out-of-order transition",
            }

        connection.execute(
            """
            UPDATE calls
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (target, call_id),
        )

        if target in TERMINAL:
            connection.execute(
                """
                UPDATE agents
                SET status = 'WRAP_UP', reserved_at = NULL
                WHERE id = ?
                """,
                (call["agent_id"],),
            )

            borrower_status = (
                "CONTACTED" if target == "COMPLETED" else "QUEUED"
            )

            connection.execute(
                """
                UPDATE borrowers SET status = ?
                WHERE id = ?
                """,
                (borrower_status, call["borrower_id"]),
            )

        elif target in {"ANSWERED", "CONNECTED"}:
            connection.execute(
                """
                UPDATE agents SET status = 'CONNECTED'
                WHERE id = ?
                """,
                (call["agent_id"],),
            )

        return {
            "call_id": call_id,
            "status": target,
            "applied": True,
            "reason": "Event processed",
        }
