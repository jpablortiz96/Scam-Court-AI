"""Abstract vision backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseVisionBackend(ABC):
    """Vision backend that analyzes screenshot evidence."""

    backend_name: str = "none"

    @abstractmethod
    def analyze_image(
        self,
        image_path: str,
        context_text: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a screenshot and return vision metadata.

        Returns a dict with keys:
            - vision_status: str  (inactive / loaded / analyzed / failed / not_available)
            - vision_model: str | None
            - vision_summary: str | None
            - extracted_text: str | None
            - screenshot_type: str | None
            - screenshot_risk_clues: list[str]
            - recommended_text_for_analysis: str | None
            - vision_confidence: float
            - vision_error: str | None
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend is loaded and ready."""
        ...
