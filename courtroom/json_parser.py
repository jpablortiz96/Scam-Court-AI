"""Safe JSON extraction and validation for model-generated reports.

Handles markdown code blocks, partial JSON, missing fields,
and automatic fallback population.
"""

import json
import re
from typing import Any


def extract_json(text: str) -> dict[str, Any] | None:
    """Extract the first valid JSON object from raw text.

    Handles markdown fences (```json ... ```) and plain text.
    Returns None if no parseable JSON is found.
    """
    # Try markdown code block first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        candidate = match.group(1).strip()
    else:
        # Try to find the outermost JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        candidate = match.group(0).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def parse_model_json(text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    """Parse model output, validate required fields, and fill gaps from fallback.

    Raises ValueError if extraction or validation fails.
    """
    parsed = extract_json(text)
    if not parsed:
        raise ValueError("No valid JSON found in model output")

    # Required fields that the model must provide
    required = ["risk_score", "verdict", "detective_report", "judge_summary"]
    for field in required:
        if field not in parsed or parsed[field] is None:
            raise ValueError(f"Missing required field: {field}")

    # Clamp risk_score
    if "risk_score" in parsed:
        try:
            parsed["risk_score"] = max(0, min(100, int(parsed["risk_score"])))
        except (ValueError, TypeError):
            raise ValueError("risk_score must be an integer between 0 and 100")

    # Ensure verdict is valid
    valid_verdicts = {"SCAM", "SUSPICIOUS", "CAUTION", "LIKELY SAFE"}
    if parsed.get("verdict") not in valid_verdicts:
        raise ValueError(f"Invalid verdict: {parsed.get('verdict')}")

    # Fill missing optional fields from fallback
    for key, value in fallback.items():
        if key not in parsed or parsed[key] is None:
            parsed[key] = value

    return parsed
