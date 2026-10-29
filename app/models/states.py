
from enum import StrEnum


class AgentStatus(StrEnum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    DIALING = "DIALING"
    CONNECTED = "CONNECTED"
    WRAP_UP = "WRAP_UP"
    PAUSED = "PAUSED"


class CallStatus(StrEnum):
    QUEUED = "QUEUED"
    RESERVED = "RESERVED"
    INITIATED = "INITIATED"
    RINGING = "RINGING"
    ANSWERED = "ANSWERED"
    CONNECTED = "CONNECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


AGENT_TRANSITIONS = {
    AgentStatus.OFFLINE: {AgentStatus.AVAILABLE},
    AgentStatus.AVAILABLE: {
        AgentStatus.RESERVED,
        AgentStatus.OFFLINE,
        AgentStatus.PAUSED,
    },
    AgentStatus.RESERVED: {
        AgentStatus.DIALING,
        AgentStatus.AVAILABLE,
        AgentStatus.OFFLINE,
    },
    AgentStatus.DIALING: {
        AgentStatus.CONNECTED,
        AgentStatus.AVAILABLE,
        AgentStatus.OFFLINE,
    },
    AgentStatus.CONNECTED: {
        AgentStatus.WRAP_UP,
        AgentStatus.OFFLINE,
    },
    AgentStatus.WRAP_UP: {
        AgentStatus.AVAILABLE,
        AgentStatus.OFFLINE,
        AgentStatus.PAUSED,
    },
    AgentStatus.PAUSED: {
        AgentStatus.AVAILABLE,
        AgentStatus.OFFLINE,
    },
}

CALL_TRANSITIONS = {
    CallStatus.QUEUED: {CallStatus.RESERVED, CallStatus.CANCELLED},
    CallStatus.RESERVED: {
        CallStatus.INITIATED,
        CallStatus.FAILED,
        CallStatus.CANCELLED,
    },
    CallStatus.INITIATED: {
        CallStatus.RINGING,
        CallStatus.ANSWERED,
        CallStatus.CONNECTED,
        CallStatus.COMPLETED,
        CallStatus.FAILED,
        CallStatus.CANCELLED,
    },
    CallStatus.RINGING: {
        CallStatus.ANSWERED,
        CallStatus.CONNECTED,
        CallStatus.COMPLETED,
        CallStatus.FAILED,
        CallStatus.CANCELLED,
    },
    CallStatus.ANSWERED: {
        CallStatus.CONNECTED,
        CallStatus.COMPLETED,
        CallStatus.FAILED,
    },
    CallStatus.CONNECTED: {
        CallStatus.COMPLETED,
        CallStatus.FAILED,
    },
    CallStatus.COMPLETED: set(),
    CallStatus.FAILED: set(),
    CallStatus.CANCELLED: set(),
}


def can_transition(current, target, transitions):
    """Return whether a state transition is permitted."""
    return target in transitions.get(current, set())
