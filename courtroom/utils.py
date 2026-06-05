"""Utility helpers for Scam Court AI."""

import re
import html


def sanitize_input(text: str) -> str:
    """Clean and truncate user input to prevent abuse and keep UI sane."""
    if not text:
        return ""
    text = html.escape(text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:4000]


def format_evidence(items: list[str]) -> str:
    """Turn a list of evidence strings into a markdown bullet list."""
    if not items:
        return "_No evidence found._"
    return "\n".join(f"- {item}" for item in items)


def clamp_score(score: int) -> int:
    """Keep risk score inside 0–100."""
    return max(0, min(100, score))
