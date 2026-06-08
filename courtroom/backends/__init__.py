"""Backend router for Scam Court AI.

Usage:
    from courtroom.backends import get_backend
    backend = get_backend()
    report = backend.analyze("Your car warranty is expiring...")
"""

from ..config import get_backend_name
from .heuristic import HeuristicBackend
from .smollm3 import SmolLM3Backend

_BACKENDS = {
    "heuristic": HeuristicBackend,
    "smollm3": SmolLM3Backend,
}


def get_backend():
    """Return the active backend instance based on SCAM_COURT_BACKEND env var.

    Defaults to HeuristicBackend if the env var is missing, invalid,
    or points to a backend that is not registered.
    """
    name = get_backend_name()
    cls = _BACKENDS.get(name, HeuristicBackend)
    return cls()
