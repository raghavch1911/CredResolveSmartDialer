
from concurrent.futures import ThreadPoolExecutor

import pytest

import app.database as database
from app.database import init_db, get_db
from app.models.states import (
    AgentStatus,
    CallStatus,
    AGENT_TRANSITIONS,
    CALL_TRANSITIONS,
    can_transition,
)
from app.services.dialer import ProgressiveDialer, AllocationError
from app.services.events import process_provider_event
from app.services.registry import create_agent, create_borrower


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "test_smartdialer.db",
    )
    init_db()


def test_state_transitions():
    assert can_transition(
        AgentStatus.AVAILABLE,
        AgentStatus.RESERVED,
        AGENT_TRANSITIONS,
    )
    assert not can_transition(
        AgentStatus.CONNECTED,
        AgentStatus.AVAILABLE,
        AGENT_TRANSITIONS,
    )
    assert can_transition(
        CallStatus.INITIATED,
        CallStatus.COMPLETED,
        CALL_TRANSITIONS,
    )


def test_progressive_allocation(isolated_db):
    create_agent("Agent One")
    create_borrower("Borrower One", "9000000001")

    dialer = ProgressiveDialer()
    call = dialer.allocate_call()

    assert call["status"] == "RESERVED"

    with pytest.raises(AllocationError):
        dialer.allocate_call()

    with get_db() as connection:
        agent = connection.execute(
            "SELECT status FROM agents WHERE id = ?",
            (call["agent_id"],),
        ).fetchone()

        assert agent["status"] == "RESERVED"


def test_duplicate_and_out_of_order_events(isolated_db):
    create_agent("Agent Two")
    create_borrower("Borrower Two", "9000000002")

    call = ProgressiveDialer().allocate_call()

    first = process_provider_event(
        call["call_id"], "event-1", "INITIATED"
    )
    duplicate = process_provider_event(
        call["call_id"], "event-1", "INITIATED"
    )

    assert first["applied"] is True
    assert duplicate["applied"] is False
    assert duplicate["reason"] == "Duplicate event"

    completed = process_provider_event(
        call["call_id"], "event-2", "COMPLETED"
    )
    late_answer = process_provider_event(
        call["call_id"], "event-3", "ANSWERED"
    )

    assert completed["status"] == "COMPLETED"
    assert late_answer["status"] == "COMPLETED"
    assert late_answer["applied"] is False


def test_two_workers_cannot_reserve_same_agent(isolated_db):
    create_agent("Shared Agent")
    create_borrower("Borrower A", "9000000003")
    create_borrower("Borrower B", "9000000004")

    def allocate():
        try:
            return ProgressiveDialer().allocate_call()
        except AllocationError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: allocate(), range(2)))

    successful = [result for result in results if result is not None]

    assert len(successful) == 1

    with get_db() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM calls"
        ).fetchone()[0] == 1
