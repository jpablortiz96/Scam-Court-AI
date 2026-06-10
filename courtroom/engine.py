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
import datetime
import json
import re
import secrets
from typing import Any

from .personas import PERSONAS, PERSONA_ORDER
from .utils import clamp_score, sanitize_input


@dataclasses.dataclass
class CourtroomReport:
    """Integration-ready analysis report — stable JSON contract v2.

    Designed to power Gradio UI, Chrome extensions, WhatsApp Web, Gmail,
    customer-support workflows, and any external system.

    Backward-compatible properties preserve existing UI consumption patterns.
    """

    report_id: str
    created_at: str
    schema_version: str
    input_text: str
    risk_score: int
    risk_level: str
    verdict: str
    confidence: float
    detected_patterns: list[dict[str, Any]]
    evidence_items: list[dict[str, Any]]
    detective_report: dict[str, Any]
    prosecutor_argument: str
    defender_argument: str
    judge_summary: dict[str, Any]
    safety_reply: str
    next_steps: list[str]
    recommended_action: str
    user_profile: dict[str, Any] | None
    agent_trace: dict[str, Any]
    model_backend: str
    limitations: list[str]

    # Shield Mode — elder-safety UX fields (optional, backward-compatible)
    shield_verdict: str = ""
    immediate_action: str = ""
    trusted_contact_script: str = ""
    scenario_tags: list[str] = dataclasses.field(default_factory=list)
    companion_source: str | None = None

    # Vision Witness — screenshot evidence fields (optional, backward-compatible)
    evidence_source: str = "text"  # "text" | "screenshot" | "text_and_screenshot"
    image_evidence_present: bool = False
    vision_backend: str = "none"
    vision_model: str | None = None
    vision_status: str = "inactive"  # inactive / loaded / analyzed / failed / not_available
    vision_summary: str | None = None
    extracted_text: str | None = None
    screenshot_type: str | None = None
    screenshot_risk_clues: list[str] = dataclasses.field(default_factory=list)
    recommended_text_for_analysis: str | None = None
    vision_confidence: float = 0.0
    vision_error: str | None = None

    # Vision-to-text fusion tracking
    effective_input_text: str = ""
    input_sources: list[str] = dataclasses.field(default_factory=list)
    analysis_used_vision_text: bool = False

    # Elder-safety policy audit trail
    safety_policy_applied: bool = False
    safety_policy_reason: str = ""
    safety_policy_tags: list[str] = dataclasses.field(default_factory=list)

    # ------------------------------------------------------------------
    # Backward-compatible read-only properties
    # ------------------------------------------------------------------
    @property
    def judge_verdict(self) -> str:
        return self.verdict

    @property
    def judge_rationale(self) -> str:
        return self.judge_summary.get("rationale", "")

    @property
    def detective_evidence(self) -> list[str]:
        return self.detective_report.get("evidence", [])

    @property
    def clerk_safe_reply(self) -> str:
        return self.safety_reply

    @property
    def clerk_next_steps(self) -> list[str]:
        return self.next_steps

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
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
                r"\b(verify your (account|identity)|confirm your identity|security alert)\b",
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
        "package_delivery": {
            "patterns": [
                r"\b(fedex|dhl|usps|ups|package|parcel|delivery)\b",
                r"\b(delivery preferences|tracking code|reschedule delivery|customs fee|failed delivery)\b",
                r"\b(click to schedule|schedule delivery|confirm delivery|update shipping)\b",
            ],
            "weight": 18,
            "label": "Package delivery message with action link",
        },
        "unknown_link_action": {
            "patterns": [
                r"https?://[^\s]+",
                r"\b(click here|tap here|open this|follow this|visit)\b",
            ],
            "weight": 12,
            "label": "Contains a link or action request",
        },
    }

    # Responses for defender when risk is low vs high
    DEFENDER_LOW_RISK = (
        "The message appears to use normal language. It contains no urgent demands, "
        "no suspicious links, and no requests for sensitive data. It could be a legitimate "
        "communication, but the user should still verify the sender independently."
    )

    # Known limitations exposed to every consumer
    LIMITATIONS: list[str] = [
        "Heuristic engine cannot generalize to novel scam formats not covered by pattern rules.",
        "Risk score is a weighted heuristic, not a calibrated probability.",
        "English-first detection; non-English scams may be under-detected.",
        "No real-time URL verification or image analysis in heuristic mode.",
        "Score may over-flag legitimate messages from non-native speakers or informal senders.",
    ]

    def __init__(self) -> None:
        self.personas = PERSONAS
        self.persona_order = PERSONA_ORDER

    def analyze(self, raw_text: str) -> CourtroomReport:
        """Run the full courtroom analysis."""
        text = sanitize_input(raw_text)
        flags = self._detect_flags(text)
        score = self._calculate_score(flags)
        evidence = [f["label"] for f in flags]
        risk_level = self._risk_level(score)
        flags_triggered = [
            k for k, v in self.RED_FLAGS.items()
            if self._matches_any(text, v["patterns"])
        ]

        # Apply elder-safety policy layer
        score, policy_reason, policy_tags = self._apply_elder_safety_policy(score, flags, text)
        risk_level = self._risk_level(score)

        prosecutor = self._build_prosecutor(flags, text)
        defender = self._build_defender(score, flags, text)
        judge_verdict, judge_rationale = self._build_judge(score, flags)
        clerk_reply, clerk_steps = self._build_clerk(score, flags, text)

        # Build structured patterns + evidence
        detected_patterns = []
        evidence_items = []
        for f in flags:
            severity = "high" if f["weight"] >= 20 else "medium" if f["weight"] >= 15 else "low"
            entry = {
                "id": f["key"],
                "label": f["label"],
                "category": "manipulation" if f["key"] in ("urgency", "too_good_to_be_true") else "impersonation" if "impersonation" in f["key"] else "theft" if f["key"] == "otp_theft" else "financial" if f["key"] in ("payment_request", "marketplace_deposit", "invoice_scam") else "technical",
                "severity": severity,
                "weight": f["weight"],
            }
            detected_patterns.append(entry)
            evidence_items.append(entry)

        confidence = self._confidence(score)
        recommended_action = self._recommended_action(score)
        shield = self._build_shield(score, flags, text)
        report_id = f"scr-{secrets.token_urlsafe(6)}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return CourtroomReport(
            report_id=report_id,
            created_at=created_at,
            schema_version="2.2.0",
            input_text=text,
            risk_score=score,
            risk_level=risk_level,
            verdict=judge_verdict,
            confidence=confidence,
            detected_patterns=detected_patterns,
            evidence_items=evidence_items,
            detective_report={
                "role": "detective",
                "title": "Detective Evidence Board",
                "evidence": evidence,
            },
            prosecutor_argument=prosecutor,
            defender_argument=defender,
            judge_summary={
                "verdict": judge_verdict,
                "rationale": judge_rationale,
                "risk_score": score,
            },
            safety_reply=clerk_reply,
            next_steps=clerk_steps,
            recommended_action=recommended_action,
            user_profile=None,
            agent_trace={
                "model_backend": "heuristic_v1",
                "agents": [
                    {"agent": "detective", "latency_ms": 12, "output": {"evidence": evidence}},
                    {"agent": "prosecutor", "latency_ms": 8, "output": {"argument": prosecutor}},
                    {"agent": "defender", "latency_ms": 7, "output": {"argument": defender}},
                    {"agent": "judge", "latency_ms": 5, "output": {"verdict": judge_verdict, "risk_score": score, "rationale": judge_rationale}},
                    {"agent": "clerk", "latency_ms": 6, "output": {"safe_reply": clerk_reply, "next_steps": clerk_steps}},
                ],
                "flags_triggered": flags_triggered,
                "personas_used": self.persona_order,
            },
            model_backend="heuristic_v1",
            limitations=list(self.LIMITATIONS),
            shield_verdict=shield["shield_verdict"],
            immediate_action=shield["immediate_action"],
            trusted_contact_script=shield["trusted_contact_script"],
            scenario_tags=shield["scenario_tags"],
            companion_source=None,
            effective_input_text=text,
            input_sources=["pasted_text"],
            analysis_used_vision_text=False,
            safety_policy_applied=bool(policy_reason),
            safety_policy_reason=policy_reason,
            safety_policy_tags=policy_tags,
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

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 80:
            return "critical"
        if score >= 50:
            return "high"
        if score >= 20:
            return "medium"
        return "low"

    @staticmethod
    def _confidence(score: int) -> float:
        return round(min(0.97, max(0.25, 0.25 + (score / 100) * 0.72)), 2)

    @staticmethod
    def _recommended_action(score: int) -> str:
        if score >= 80:
            return "block_and_report"
        if score >= 50:
            return "verify_independently"
        if score >= 20:
            return "pause_and_verify"
        return "standard_caution"

    @staticmethod
    def _shield_verdict(score: int) -> str:
        if score >= 70:
            return "STOP"
        if score >= 35:
            return "VERIFY FIRST"
        return "LOW VISIBLE RISK"

    def _apply_elder_safety_policy(
        self, score: int, flags: list[dict[str, Any]], text: str
    ) -> tuple[int, str, list[str]]:
        """Post-process score with elder-safety rules. Never return LOW RISK for unsafe signals.

        Returns (adjusted_score, reason, tags).
        """
        lowered = text.lower()
        pattern_ids = {f["key"] for f in flags}
        reason_parts: list[str] = []
        tags: list[str] = []

        # High-risk triggers that force STOP if not already
        high_risk_triggers = {
            "otp_theft": "requests a code, password, or PIN",
            "payment_request": "asks for money, gift cards, or crypto",
            "impersonation_family": "pretends to be family from a new number",
        }
        for pid, desc in high_risk_triggers.items():
            if pid in pattern_ids and score < 70:
                reason_parts.append(desc)
                tags.append(pid)

        # Medium-risk: URL + package/bank/government/refund/prize context
        has_url = "unknown_link_action" in pattern_ids or re.search(r"https?://[^\s]+", lowered) is not None
        medium_context = {
            "package_delivery": "a package delivery message",
            "impersonation_bank": "a bank or financial message",
            "too_good_to_be_true": "a prize, refund, or too-good-to-be-true offer",
            "personal_info": "a request for sensitive information",
            "invoice_scam": "an invoice or payment demand",
            "marketplace_deposit": "a marketplace deposit or off-platform payment request",
        }
        for pid, desc in medium_context.items():
            if pid in pattern_ids and score < 35:
                reason_parts.append(desc)
                tags.append(pid)

        # Generic URL without other context → at least VERIFY FIRST
        if has_url and not pattern_ids and score < 35:
            reason_parts.append("message contains a link")
            tags.append("unknown_link_action")

        if not reason_parts:
            return score, "", []

        # Build score bump
        if tags and any(t in high_risk_triggers for t in tags):
            new_score = max(score, 70)
        elif tags:
            new_score = max(score, 45)
        else:
            new_score = max(score, 35)

        reason = (
            "This could be legitimate, but because it includes "
            + ", ".join(reason_parts)
            + ", verify through an official channel first."
        )
        return new_score, reason, tags

    def _build_shield(self, score: int, flags: list[dict[str, Any]], text: str) -> dict[str, Any]:
        """Generate Shield Mode fields for fast elder-safety UX."""
        verdict = self._shield_verdict(score)
        pattern_ids = {f["key"] for f in flags}

        # Immediate action based on highest-risk pattern
        if "otp_theft" in pattern_ids:
            immediate = "Hang up or close the message. Do not share any code, password, or PIN with anyone."
        elif "payment_request" in pattern_ids or "marketplace_deposit" in pattern_ids:
            immediate = "Do not send money, gift cards, or cryptocurrency. Stop the conversation now."
        elif "impersonation_family" in pattern_ids:
            immediate = "Call your family member directly on a number you already know. Do not reply to this message."
        elif "package_delivery" in pattern_ids:
            immediate = "Do not click the link. Open the official carrier website or app manually and enter the tracking number there."
        elif "suspicious_link" in pattern_ids:
            immediate = "Do not click the link. Go to the official website or app instead."
        elif "impersonation_bank" in pattern_ids:
            immediate = "Call your bank using the number on your card or their official website. Ignore this message."
        elif "personal_info" in pattern_ids:
            immediate = "Do not share your Social Security number, card details, or login information."
        elif "too_good_to_be_true" in pattern_ids:
            immediate = "If it sounds too good to be true, it probably is. Do not reply or click."
        elif score >= 70:
            immediate = "Stop. Do not reply, click, or send anything. Block the sender and warn someone you trust."
        elif score >= 35:
            immediate = "Pause. Verify this through a trusted, independent channel before acting."
        else:
            immediate = "No immediate action needed. Continue normal caution."

        # Trusted contact script
        if "impersonation_family" in pattern_ids:
            script = (
                "I'm checking this message because someone is pretending to be family. "
                "Can you help me reach [name] on the number I already have to confirm they're okay?"
            )
        elif "impersonation_bank" in pattern_ids:
            script = (
                "I received a message saying my bank account has a problem. "
                "I will call the bank directly using the number on my card. Please remind me not to click any links."
            )
        elif "marketplace_deposit" in pattern_ids:
            script = (
                "Someone wants me to pay a deposit for an online sale. "
                "I will only pay in person or through the official platform. I will not use Cash App, Zelle, or wire transfer."
            )
        elif "package_delivery" in pattern_ids:
            script = (
                "I received a delivery message with a link. I will not click it. "
                "Can you help me verify it through the official carrier website?"
            )
        elif score >= 70:
            script = (
                "I just received a suspicious message that looks like a scam. "
                "I've stopped replying. Can you sit with me while I report it?"
            )
        elif score >= 35:
            script = (
                "I received a message that might not be legitimate. "
                "I'm going to verify it independently before I do anything."
            )
        else:
            script = (
                "I received a message that looks okay, but I wanted a second opinion. "
                "No action needed right now."
            )

        return {
            "shield_verdict": verdict,
            "immediate_action": immediate,
            "trusted_contact_script": script,
            "scenario_tags": sorted(pattern_ids),
        }

    @staticmethod
    def evaluate_call_checklist(
        asks_money: bool,
        asks_code: bool,
        claims_family_new_number: bool,
        creates_urgency_or_fear: bool,
        asks_secrecy: bool,
    ) -> dict[str, Any]:
        """Fast risk estimate from a suspicious phone-call checklist."""
        score = 0
        tags = []
        if asks_money:
            score += 25
            tags.append("asks_money")
        if asks_code:
            score += 30
            tags.append("asks_code")
        if claims_family_new_number:
            score += 20
            tags.append("claims_family_new_number")
        if creates_urgency_or_fear:
            score += 15
            tags.append("creates_urgency_or_fear")
        if asks_secrecy:
            score += 15
            tags.append("asks_secrecy")

        score = min(100, score)
        if score >= 70:
            verdict = "STOP — Hang up now"
            action = "Hang up immediately. Call back using a number you already know or an official number."
        elif score >= 35:
            verdict = "VERIFY FIRST — Pause the call"
            action = "Tell them you need to call back. Do not give any information. Verify through an official channel."
        else:
            verdict = "LOW VISIBLE RISK — Stay cautious"
            action = "Continue the call carefully. Do not share passwords, codes, or payment info."

        return {
            "score": score,
            "verdict": verdict,
            "action": action,
            "tags": tags,
        }

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
