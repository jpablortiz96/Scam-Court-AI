"""Scam Court AI runtime configuration.

Reads environment variables with sensible defaults.
Loads .env file if present; OS environment variables always win.
"""

import os

from dotenv import load_dotenv

# Load .env before any os.getenv calls.
# override=False ensures OS env vars take precedence over .env values.
load_dotenv(override=False)

DEFAULT_BACKEND = "heuristic"
VALID_BACKENDS = {"heuristic", "smollm3"}

DEFAULT_VISION_BACKEND = "none"
VALID_VISION_BACKENDS = {"none", "minicpm_v"}

DEFAULT_VISION_MODEL = "openbmb/MiniCPM-V-4"


def get_backend_name() -> str:
    """Return the backend name from SCAM_COURT_BACKEND env var.

    Falls back to 'heuristic' if missing or invalid.
    """
    backend = os.getenv("SCAM_COURT_BACKEND", DEFAULT_BACKEND).lower().strip()
    if backend not in VALID_BACKENDS:
        return DEFAULT_BACKEND
    return backend


def get_vision_backend_name() -> str:
    """Return the vision backend name from SCAM_COURT_VISION_BACKEND env var.

    Falls back to 'none' if missing or invalid.
    """
    backend = os.getenv("SCAM_COURT_VISION_BACKEND", DEFAULT_VISION_BACKEND).lower().strip()
    if backend not in VALID_VISION_BACKENDS:
        return DEFAULT_VISION_BACKEND
    return backend


def get_vision_model_id() -> str:
    """Return the vision model ID from SCAM_COURT_VISION_MODEL env var.

    Falls back to 'openbmb/MiniCPM-V-4' if missing.
    """
    return os.getenv("SCAM_COURT_VISION_MODEL", DEFAULT_VISION_MODEL).strip()
