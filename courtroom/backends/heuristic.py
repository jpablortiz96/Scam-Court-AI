"""Heuristic backend — wraps the existing rule-based engine."""

from .base import BaseBackend
from ..engine import CourtroomEngine, CourtroomReport


class HeuristicBackend(BaseBackend):
    """Default fast backend using regex + weighted scoring.

    Requires no model download, no GPU, and starts instantly.
    """

    def __init__(self) -> None:
        self._engine = CourtroomEngine()

    def analyze(self, raw_text: str) -> CourtroomReport:
        return self._engine.analyze(raw_text)
