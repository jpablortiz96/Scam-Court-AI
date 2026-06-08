"""Scam Court AI runtime configuration.

Reads environment variables with sensible defaults.
"""

import os

DEFAULT_BACKEND = "heuristic"
VALID_BACKENDS = {"heuristic", "smollm3"}


def get_backend_name() -> str:
    """Return the backend name from SCAM_COURT_BACKEND env var.

    Falls back to 'heuristic' if missing or invalid.
    """
    backend = os.getenv("SCAM_COURT_BACKEND", DEFAULT_BACKEND).lower().strip()
    if backend not in VALID_BACKENDS:
        return DEFAULT_BACKEND
    return backend
