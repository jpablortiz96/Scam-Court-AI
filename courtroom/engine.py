"""CourtroomEngine — deterministic heuristic analysis with a pluggable backend.

Today: rule-based red-flag detection, scoring, and templated persona responses.
Tomorrow: swap `analyze()` for a small-model pipeline (SmolLM3-3B, MiniCPM-V, etc.)
without touching the UI layer.

Design rules:
1. All outputs are structured dataclasses.
2. No external API calls.
3. Deterministic scoring.
4. Persona copy is generated from data, not hard-coded in Gradio.
"""

from __future__ import annotations

import dataclasses
import json
import re
from typing import Any

from .personas import PERSONAS, PERSONA_ORDER
from .utils import clamp_score, sanitize_input


@dataclasses.dataclass
class CourtroomReport:
    """Structured output from the courtroom."""

    raw_input: str
    detective_evidence: list[str]
    prosecutor_argument: str
    defender_argument: str
    judge_verdict: str
    judge_rationale: str
    risk_score: int
    clerk_safe_reply: str
    clerk_next_steps: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class CourtroomEngine:
    """Heuristic courtroom engine.

    Usage:
        engine = CourtroomEngine()
        report = engine.analyze("Your car warranty is expiring...")
    """

    # Heuristic weights (must sum to a basis we normalize later)
    RED_FLAGS: dict[str, dict[str, Any]] = {
        "urgency": {
            "patterns": [
                r"\b(urgent|immediately|right now|act now|limited time|expires?|deadline|today only|within \d+ hours?)\b",
                r"\b(account suspended|will be locked|final notice|last warning)\b",
            ],
            "weight": 15,
            "label": "Creates false urgency",
        },
        "impersonation_bank": {
            "patterns": [
                r"\b(bank of america|chase|wells fargo|citi|capital one|paypal|venmo|zelle|your bank)\b",
                r"\b(verify your account|confirm your identity|security alert)\b",
            ],
            "weight": 20,
            "label": "Impersonates a financial institution",
        },
        "impersonation_family": {
            "patterns": [
                r"\b(it'?s me[,\s]+(mom|dad|grandma|grandpa|uncle|aunt))\b",
                r"\b(this is your (mom|dad|son|daughter))\b",
                r"\b(new phone|lost my phone|broken phone)\b",
            ],
            "weight": 18,
            "label": "Impersonates a family member",
        },
        "otp_theft": {
            "patterns": [
                r"\b(send me the code|give me the code|verification code|otp|passcode|pin)\b",
                r"\b(i sent you a code|code i just sent|enter this code)\b",
            ],
            "weight": 25,
            "label": "Requests a one-time password or code",
        },
        "payment_request": {
            "patterns": [
                r"\b(send money|wire transfer|gift card|bitcoin|crypto|deposit)\b",
                r"\b(pay .* fee|processing fee|shipping fee|customs fee)\b",
                r"\b(zelle me|cash app me|venmo me|paypal me)\b",
            ],
            "weight": 22,
            "label": "Requests payment or money transfer",
        },
        "suspicious_link": {
            "patterns": [
                r"http[s]?://[^\s]+\.(tk|ml|ga|cf|top|xyz|click|link|zip)\b",
                r"bit\.ly|tinyurl|t\.ly|short\.link",
                r"click here|tap here|open this link",
            ],
            "weight": 20,
            "label": "Contains suspicious or shortened link",
        },
        "personal_info": {
            "patterns": [
                r"\b(ssn|social security|credit card|cvv|pin|password|login|username)\b",
                r"\b(date of birth|mother'?s maiden name)\b",
            ],
            "weight": 20,
            "label": "Requests sensitive personal information",
        },
        "too_good_to_be_true": {
            "patterns": [
                r"\b(won|winner|congratulations|you'?ve been selected|prize|lottery|refund of)\b",
                r"\b(\$[\d,]+\s*(reward|prize|refund|credit))\b",
                r"\b(free money|guaranteed return|double your)\b",
            ],
            "weight": 16,
            "label": "Too good to be true offer",
        },
        "grammar_poor": {
            "patterns": [
                r"\b(dear customer|dear user|valued customer)\b",
                r"[!]{2,}",
                r"\b(kindly|do the needful)\b",
            ],
            "weight": 8,
            "label": "Poor grammar or generic greeting",
        },
        "marketplace_deposit": {
            "patterns": [
                r"\b(holding fee|security deposit|earnest money| reservation fee)\b",
                r"\b(i can'?t meet in person|ship(ping)? first|courier|agent)\b",
                r"\b(interested in (buying|renting).*(deposit|fee))\b",
            ],
            "weight": 19,
            "label": "Marketplace advance-fee pattern",
        },
        "invoice_scam": {
            "patterns": [
                r"\b(invoice.*overdue|unpaid invoice|payment reminder.*invoice)\b",
                r"\b(click to (view|pay) invoice|attached invoice)\b",
                r"\b(remit payment|outstanding balance)\b",
            ],
            "weight": 18,
            "label": "Fake invoice or payment demand",
        },
    }

    # Responses for defender when risk is low vs high
    DEFENDER_LOW_RISK = (
        "The message appears to use normal language. It contains no urgent demands, "
        "no suspicious links, and no requests for sensitive data. It could be a legitimate "
        "communication, but the user should still verify the sender independently."
    )

    def __init__(self) -> None:
        self.personas = PERSONAS
        self.persona_order = PERSONA_ORDER

    def analyze(self, raw_text: str) -> CourtroomReport:
        """Run the full courtroom analysis."""
        text = sanitize_input(raw_text)
        flags = self._detect_flags(text)
        score = self._calculate_score(flags)
        evidence = [f["label"] for f in flags]

        prosecutor = self._build_prosecutor(flags, text)
        defender = self._build_defender(score, flags, text)
        judge_verdict, judge_rationale = self._build_judge(score, flags)
        clerk_reply, clerk_steps = self._build_clerk(score, flags, text)

        return CourtroomReport(
            raw_input=text,
            detective_evidence=evidence,
            prosecutor_argument=prosecutor,
            defender_argument=defender,
            judge_verdict=judge_verdict,
            judge_rationale=judge_rationale,
            risk_score=score,
            clerk_safe_reply=clerk_reply,
            clerk_next_steps=clerk_steps,
            metadata={
                "engine_version": "heuristic_v1",
                "flags_triggered": [k for k, v in self.RED_FLAGS.items() if self._matches_any(text, v["patterns"])],
                "personas_used": self.persona_order,
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _matches_any(cls, text: str, patterns: list[str]) -> bool:
        lowered = text.lower()
        for pat in patterns:
            if re.search(pat, lowered, re.IGNORECASE):
                return True
        return False

    def _detect_flags(self, text: str) -> list[dict[str, Any]]:
        triggered = []
        for key, config in self.RED_FLAGS.items():
            if self._matches_any(text, config["patterns"]):
                triggered.append({"key": key, **config})
        return triggered

    def _calculate_score(self, flags: list[dict[str, Any]]) -> int:
        if not flags:
            return 5  # baseline paranoia
        raw = sum(f["weight"] for f in flags)
        # Diminishing returns after 100 so we don't always max out
        score = int(100 * (1 - 0.6 ** (raw / 30)))
        return clamp_score(score)

    def _build_prosecutor(self, flags: list[dict[str, Any]], text: str) -> str:
        if not flags:
            return (
                "Your Honor, the prosecution finds no clear red flags in this message. "
                "While scams can be subtle, this sample lacks the typical markers of fraud."
            )
        lines = [
            "Your Honor, the prosecution presents the following case:",
            "",
        ]
        for i, f in enumerate(flags, 1):
            lines.append(f"{i}. **{f['label']}** — weight {f['weight']}")
        lines.append("")
        lines.append("The defendant's message employs classic social-engineering tactics.")
        return "\n".join(lines)

    def _build_defender(self, score: int, flags: list[dict[str, Any]], text: str) -> str:
        if score < 30:
            return self.DEFENDER_LOW_RISK
        if not flags:
            return self.DEFENDER_LOW_RISK

        # Find the weakest flag to argue against
        weakest = min(flags, key=lambda x: x["weight"])
        lines = [
            "Your Honor, the defense respectfully disagrees with the prosecution's emphasis.",
            "",
            f"The so-called '{weakest['label']}' could easily be explained by context: "
            "a rushed sender, an auto-correct error, or a legitimate business process.",
            "",
        ]
        if score > 70:
            lines.append(
                "That said, the cumulative weight of the remaining indicators is hard to dismiss. "
                "The defense cannot offer a credible innocent explanation for the full pattern."
            )
        else:
            lines.append(
                "Taken individually, none of these markers prove malicious intent beyond reasonable doubt."
            )
        return "\n".join(lines)

    def _build_judge(self, score: int, flags: list[dict[str, Any]]) -> tuple[str, str]:
        if score >= 80:
            verdict = "SCAM"
            rationale = (
                f"The evidence is overwhelming. With a risk score of **{score}/100**, "
                f"the court finds {len(flags)} distinct red flags. "
                "This message exhibits multiple classic scam techniques. **Do not respond or click any links.**"
            )
        elif score >= 50:
            verdict = "SUSPICIOUS"
            rationale = (
                f"The court records a risk score of **{score}/100**. "
                f"{len(flags)} indicators are present. While not conclusive proof of fraud, "
                "the user should independently verify the sender through a trusted channel before acting."
            )
        elif score >= 20:
            verdict = "CAUTION"
            rationale = (
                f"A risk score of **{score}/100** suggests minor concerns. "
                "The message is not clearly fraudulent, but the user should remain alert."
            )
        else:
            verdict = "LIKELY SAFE"
            rationale = (
                f"With a risk score of **{score}/100**, the court finds no meaningful evidence of a scam. "
                "Standard caution still applies."
            )
        return verdict, rationale

    def _build_clerk(self, score: int, flags: list[dict[str, Any]], text: str) -> tuple[str, list[str]]:
        if score >= 80:
            reply = (
                "*Do not reply. Do not click links. Do not send codes or money.* "
                "Block the sender and report the message."
            )
            steps = [
                "Forward the message to your carrier's spam report number (e.g., 7726).",
                "Report to the FTC at reportfraud.ftc.gov or your local cyber-crime unit.",
                "Change passwords if you clicked any link or shared any info.",
                "Warn family members who might receive similar messages.",
            ]
        elif score >= 50:
            reply = (
                "'I need to verify this independently. I will call the official number listed on "
                "the company's website, not any number in this message.'"
            )
            steps = [
                "Look up the organization's official contact info independently.",
                "Ask the sender a question only the real person would know.",
                "Check your actual account directly via the official app or website.",
                "Do not send payment or codes until verification is complete.",
            ]
        elif score >= 20:
            reply = (
                "'Thanks for reaching out. Let me confirm this through the usual channel before I proceed.'"
            )
            steps = [
                "Verify the sender's identity with a known contact method.",
                "Hover over (don't click) links to inspect the true URL.",
                "When in doubt, pause. Scammers rely on rushed decisions.",
            ]
        else:
            reply = (
                "No reply needed. The message appears legitimate, but keep normal security habits."
            )
            steps = [
                "Continue standard security hygiene.",
                "If anything feels off later, re-run it through Scam Court AI.",
            ]
        return reply, steps
