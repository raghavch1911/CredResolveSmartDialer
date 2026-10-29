
from app.database import get_db
from app.models.states import AgentStatus


def create_agent(name):
    with get_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO agents (name, status)
            VALUES (?, ?)
            """,
            (name, AgentStatus.AVAILABLE.value),
        )
        return {
            "id": cursor.lastrowid,
            "name": name,
            "status": AgentStatus.AVAILABLE.value,
        }


def create_borrower(name, phone):
    with get_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO borrowers (name, phone, status)
            VALUES (?, ?, 'QUEUED')
            """,
            (name, phone),
        )
        return {
            "id": cursor.lastrowid,
            "name": name,
            "phone": phone,
            "status": "QUEUED",
        }
