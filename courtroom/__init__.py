"""Scam Court AI — Modular courtroom engine for suspicious message analysis."""

from .backends import get_backend
from .engine import CourtroomEngine, CourtroomReport
from .personas import PERSONAS
from .utils import sanitize_input, format_evidence
from .vision_backends import get_vision_backend

__all__ = [
    "get_backend",
    "get_vision_backend",
    "CourtroomEngine",
    "CourtroomReport",
    "PERSONAS",
    "sanitize_input",
    "format_evidence",
]
