
from abc import ABC, abstractmethod


class TelecomProvider(ABC):
    @abstractmethod
    def initiate_call(self, call_id: int, idempotency_key: str) -> dict:
        """Initiate a call and return a simulated provider response."""
        raise NotImplementedError
