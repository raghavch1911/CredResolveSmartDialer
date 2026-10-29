
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(
    os.getenv(
        "SMARTDIALER_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "smartdialer.db"),
    )
)


def get_connection():
    """Create a SQLite connection with foreign-key enforcement."""
    connection = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def get_db():
    """Provide a connection and safely commit or roll back changes."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Initialize the core SmartDialer database tables."""
    with get_db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'AVAILABLE'
                    CHECK (status IN (
                        'OFFLINE', 'AVAILABLE', 'RESERVED',
                        'DIALING', 'CONNECTED', 'WRAP_UP', 'PAUSED'
                    )),
                reserved_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS borrowers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'QUEUED'
                    CHECK (status IN (
                        'QUEUED', 'RESERVED', 'CONTACTED',
                        'COMPLETED', 'FAILED'
                    )),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL REFERENCES agents(id),
                borrower_id INTEGER NOT NULL REFERENCES borrowers(id),
                provider TEXT NOT NULL DEFAULT 'mock_a',
                status TEXT NOT NULL DEFAULT 'RESERVED'
                    CHECK (status IN (
                        'QUEUED', 'RESERVED', 'INITIATED',
                        'RINGING', 'ANSWERED', 'CONNECTED',
                        'COMPLETED', 'FAILED', 'CANCELLED'
                    )),
                provider_call_id TEXT UNIQUE,
                idempotency_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_agents_status
                ON agents(status);

            CREATE INDEX IF NOT EXISTS idx_borrowers_status
                ON borrowers(status);

            CREATE INDEX IF NOT EXISTS idx_calls_status
                ON calls(status);

            CREATE TABLE IF NOT EXISTS provider_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                call_id INTEGER NOT NULL REFERENCES calls(id),
                event_type TEXT NOT NULL,
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
