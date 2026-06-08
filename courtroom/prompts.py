"""Prompt builders for small-model backends."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import CourtroomReport


SCHEMA_TEMPLATE = {
    "report_id": "string",
    "created_at": "string (ISO 8601)",
    "schema_version": "2.0.0",
    "input_text": "string",
    "risk_score": "integer 0-100",
    "risk_level": "critical | high | medium | low",
    "verdict": "SCAM | SUSPICIOUS | CAUTION | LIKELY SAFE",
    "confidence": "float 0.25-0.97",
    "detected_patterns": [
        {"id": "string", "label": "string", "category": "string", "severity": "high|medium|low", "weight": "integer"}
    ],
    "evidence_items": "same structure as detected_patterns",
    "detective_report": {"role": "detective", "title": "Detective Evidence Board", "evidence": ["string"]},
    "prosecutor_argument": "string",
    "defender_argument": "string",
    "judge_summary": {"verdict": "string", "rationale": "string", "risk_score": "integer"},
    "safety_reply": "string",
    "next_steps": ["string"],
    "recommended_action": "block_and_report | verify_independently | pause_and_verify | standard_caution",
    "user_profile": "null or object",
    "agent_trace": {"model_backend": "smollm3_v1", "agents": [{"agent": "string", "latency_ms": "integer", "output": "object"}]},
    "model_backend": "smollm3_v1",
    "limitations": ["string"],
}

SYSTEM_PROMPT = (
    "You are Scam Court AI — a digital courtroom that puts suspicious messages on trial.\n"
    "You have five roles:\n"
    "  1. Detective — extracts red flags and evidence.\n"
    "  2. Prosecutor — explains manipulation tactics used.\n"
    "  3. Defender — argues why the message could be legitimate.\n"
    "  4. Judge — delivers a risk score (0-100) and a verdict.\n"
    "  5. Safety Clerk — writes a safe reply and concrete next steps.\n\n"
    "STRICT RULES:\n"
    "  - Output ONLY valid JSON. No markdown, no explanations, no preamble.\n"
    "  - Never tell users to click links.\n"
    "  - Never ask users to share passwords, OTPs, banking info, or private documents.\n"
    "  - Always recommend independent verification through trusted channels.\n"
    "  - risk_score must be an integer between 0 and 100.\n"
    "  - verdict must be exactly one of: SCAM, SUSPICIOUS, CAUTION, LIKELY SAFE.\n"
    "  - Include this limitation: 'This app is not a legal, financial, or cybersecurity authority.'\n"
    "  - Use the exact JSON schema provided below.\n\n"
)


def build_smollm3_prompt(input_text: str, heuristic_report: "CourtroomReport") -> str:
    """Build a structured prompt for the SmolLM3 backend.

    The prompt includes:
    - System instructions and safety rules
    - The suspicious input text
    - Heuristic evidence summary (as context, not gospel)
    - The exact JSON schema the model must follow
    """
    heuristic_dict = heuristic_report.to_dict()
    evidence_json = json.dumps(heuristic_dict.get("detected_patterns", []), indent=2, ensure_ascii=False)
    schema_json = json.dumps(SCHEMA_TEMPLATE, indent=2, ensure_ascii=False)

    user_block = (
        f"INPUT MESSAGE:\n{input_text}\n\n"
        f"HEURISTIC PRE-ANALYSIS (use as context only):\n{evidence_json}\n\n"
        f"REQUIRED JSON SCHEMA:\n{schema_json}\n\n"
        f"Your JSON response:"
    )

    return f"{SYSTEM_PROMPT}\n{user_block}"
