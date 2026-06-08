"""Abstract base class for Scam Court AI backends."""

from abc import ABC, abstractmethod

from ..engine import CourtroomReport


class BaseBackend(ABC):
    """All backends must implement analyze(raw_text) -> CourtroomReport."""

    @abstractmethod
    def analyze(self, raw_text: str) -> CourtroomReport:
        """Analyze suspicious message text and return a structured report."""
        raise NotImplementedError
