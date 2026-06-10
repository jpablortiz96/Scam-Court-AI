"""Vision backend router for Scam Court AI.

Selects the vision backend via SCAM_COURT_VISION_BACKEND env var.
"""

from __future__ import annotations

from .base import BaseVisionBackend
from .none import NoneVisionBackend


def get_vision_backend() -> BaseVisionBackend:
    """Return the configured vision backend instance."""
    from ..config import get_vision_backend_name

    name = get_vision_backend_name()
    if name == "minicpm_v":
        from .minicpm_v import MiniCPMVBackend
        return MiniCPMVBackend()
    return NoneVisionBackend()
