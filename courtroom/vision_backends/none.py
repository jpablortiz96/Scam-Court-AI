"""Default no-op vision backend."""

from __future__ import annotations

from typing import Any

from .base import BaseVisionBackend


class NoneVisionBackend(BaseVisionBackend):
    """Placeholder vision backend when no vision model is configured.

    Returns a friendly fallback message without pretending to analyze images.
    """

    backend_name = "none"

    def analyze_image(
        self,
        image_path: str,
        context_text: str | None = None,
    ) -> dict[str, Any]:
        return {
            "vision_status": "inactive",
            "vision_model": None,
            "vision_summary": None,
            "extracted_text": None,
            "screenshot_type": None,
            "screenshot_risk_clues": [],
            "recommended_text_for_analysis": None,
            "vision_confidence": 0.0,
            "vision_error": None,
        }

    def is_available(self) -> bool:
        return True
