"""Scam Court AI - premium Gradio safety interface.

Run locally:
    python app.py
"""

from __future__ import annotations

import dataclasses
import datetime
import html
import os
import pathlib
import random
import re
import subprocess
import sys
from typing import Any

import gradio as gr

from courtroom import get_backend, get_vision_backend
from courtroom.config import get_vision_model_id
from courtroom.engine import CourtroomEngine
from courtroom.ui import DEFAULT_LANG, PAGE_JS, build_css, normalize_lang, t, theme_choices
from courtroom.zero_gpu import (
    SPACES_IMPORT_SUCCEEDED,
    ZERO_GPU_DECORATOR_ACTIVE,
    ZERO_GPU_RUNTIME_ACTIVE,
    gpu_function,
)


ASSET_DIR = pathlib.Path(__file__).parent / "assets"
ROLE_ORDER = ("detective", "prosecutor", "defender", "judge", "clerk")
UI_VERSION = "ui_premium_2026_v2"


def _resolve_build_marker() -> str:
    for key in ("SPACE_COMMIT_SHA", "GIT_COMMIT", "COMMIT_SHA", "SOURCE_COMMIT"):
        value = os.getenv(key, "").strip()
        if value:
            return value[:8]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=8", "HEAD"],
            cwd=pathlib.Path(__file__).parent,
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        )
        if result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return datetime.datetime.now(datetime.timezone.utc).strftime("build-%Y%m%d%H%M")


BUILD_MARKER = _resolve_build_marker()


def _load_svg(name: str) -> str:
    return (ASSET_DIR / f"{name}.svg").read_text(encoding="utf-8")


ROLE_SVGS = {role: _load_svg(role) for role in ROLE_ORDER}

SHIELD_ICON = """
<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 3 19 6v5c0 4.8-2.7 8.1-7 10-4.3-1.9-7-5.2-7-10V6l7-3Z" stroke="currentColor" stroke-width="1.8"/>
  <path d="m9.2 12 1.8 1.8 3.9-4.1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
STOP_ICON = """
<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M9 3h6l4 4v6l-4 4H9l-4-4V7l4-4Z" stroke="currentColor" stroke-width="1.8"/>
  <path d="M12 7.5v5.2M12 16.2v.1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>
"""
VERIFY_ICON = """
<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 4 21 20H3L12 4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
  <path d="M12 9v4.6M12 17v.1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>
"""
SAFE_ICON = """
<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/>
  <path d="m8 12.2 2.5 2.5L16.5 9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
CAMERA_ICON = """
<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M4 8.5h3l1.4-2h7.2l1.4 2h3v10H4v-10Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
  <circle cx="12" cy="13.5" r="3.2" stroke="currentColor" stroke-width="1.7"/>
</svg>
"""

backend = get_backend()

EXAMPLES = [
    {
        "key": "ex_family",
        "text": (
            "Hi honey, it's Mom. I got a new phone and lost all my contacts. "
            "Can you send me $500 via Zelle? Please don't tell Dad. Send it quickly."
        ),
    },
    {
        "key": "ex_bank",
        "text": (
            "ALERT: Your Chase account has been suspended. Verify immediately at "
            "http://chase-verify-now.tk/login or your funds will be locked."
        ),
    },
    {
        "key": "ex_otp",
        "text": (
            "This is IT support. Forward the 6-digit code I just sent to your phone. "
            "It is urgent and we need it now."
        ),
    },
    {
        "key": "ex_marketplace",
        "text": (
            "I want to buy your couch but cannot meet. Pay a $150 holding deposit via "
            "Cash App and my courier will collect it tomorrow."
        ),
    },
    {
        "key": "ex_invoice",
        "text": (
            "Invoice #8921 is overdue. Pay $4,250 immediately to avoid service interruption: "
            "https://invoice-portal.zip/pay?id=8921"
        ),
    },
]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def _mode_intro(lang: str, mode: str) -> str:
    return f"""
    <section class="mode-intro">
      <div class="mode-eyebrow">{_esc(t(lang, f"mode_{mode}_eyebrow"))}</div>
      <h2>{_esc(t(lang, f"mode_{mode}_title"))}</h2>
      <p>{_esc(t(lang, f"mode_{mode}_subtitle"))}</p>
    </section>
    """


def _label(text: str, css_class: str = "section-label") -> str:
    return f'<div class="{css_class}">{_esc(text)}</div>'


def render_ui_state(lang: str, theme: str) -> str:
    language = normalize_lang(lang)
    safe_theme = theme if theme in ("dark", "light") else "dark"
    return (
        f'<div id="sc-ui-state" class="ui-state-marker" '
        f'data-lang="{language}" data-theme="{safe_theme}" aria-hidden="true"></div>'
    )


def _verdict_kind(verdict: str) -> str:
    upper = verdict.upper()
    if "STOP" in upper or "HANG UP" in upper:
        return "stop"
    if "VERIFY" in upper or "PAUSE" in upper:
        return "verify"
    return "safe"


def _localized_verdict(verdict: str, lang: str) -> str:
    kind = _verdict_kind(verdict)
    return t(lang, {"stop": "verdict_stop", "verify": "verdict_verify", "safe": "verdict_safe"}[kind])


def _status_icon(kind: str) -> str:
    return {"stop": STOP_ICON, "verify": VERIFY_ICON, "safe": SAFE_ICON}.get(kind, SHIELD_ICON)


def _score_color(score: int) -> str:
    if score >= 70:
        return "var(--sc-danger)"
    if score >= 35:
        return "var(--sc-warning)"
    return "var(--sc-safe)"


def _report_tags(report: dict[str, Any]) -> set[str]:
    tags = set(report.get("scenario_tags") or [])
    tags.update(report.get("safety_policy_tags") or [])
    tags.update(
        item.get("id", "")
        for item in report.get("detected_patterns", [])
        if isinstance(item, dict)
    )
    return {tag for tag in tags if tag}


def _localized_action(report: dict[str, Any], lang: str) -> str:
    tags = _report_tags(report)
    status = report.get("vision_status")
    if report.get("image_evidence_present") and status != "analyzed":
        return t(lang, "action_vision_failed")
    if "otp_theft" in tags:
        return t(lang, "action_otp")
    if tags.intersection({"payment_request", "marketplace_deposit"}):
        return t(lang, "action_money")
    if "impersonation_family" in tags:
        return t(lang, "action_family")
    if "package_delivery" in tags:
        return t(lang, "action_package")
    if "impersonation_bank" in tags:
        return t(lang, "action_bank")
    if tags.intersection({"suspicious_link", "unknown_link_action"}):
        return t(lang, "action_link")
    score = int(report.get("risk_score", 0))
    if score >= 70:
        return t(lang, "action_high")
    if score >= 35:
        return t(lang, "action_verify")
    return t(lang, "action_safe")


def _localized_script(report: dict[str, Any], lang: str) -> str:
    tags = _report_tags(report)
    if "otp_theft" in tags:
        return t(lang, "script_otp")
    if tags.intersection({"payment_request", "marketplace_deposit"}):
        return t(lang, "script_money")
    if "impersonation_family" in tags:
        return t(lang, "script_family")
    if "package_delivery" in tags:
        return t(lang, "script_package")
    score = int(report.get("risk_score", 0))
    if score >= 70:
        return t(lang, "script_high")
    if score >= 35:
        return t(lang, "script_verify")
    return t(lang, "script_safe")


def _pattern_label(item: dict[str, Any], lang: str) -> str:
    pattern_id = item.get("id", "")
    key = f"pattern_{pattern_id}"
    translated = t(lang, key)
    return translated if translated != key else str(item.get("label", pattern_id))


def _empty_panel(lang: str, kind: str) -> str:
    if kind == "shield":
        title = t(lang, "shield_empty_title")
        body = t(lang, "shield_empty_body")
        css_class = "shield-empty"
    elif kind == "call":
        title = t(lang, "call_empty_title")
        body = t(lang, "call_empty_body")
        css_class = "call-empty"
    else:
        title = t(lang, "court_waiting_title")
        body = t(lang, "court_waiting_body")
        css_class = "court-empty"
    return f"""
    <div class="{css_class}">
      <div class="empty-emblem">{SHIELD_ICON}</div>
      <div class="empty-title">{_esc(title)}</div>
      <div class="empty-body">{_esc(body)}</div>
    </div>
    """


def render_shield(report: dict[str, Any] | None, lang: str) -> str:
    if not report:
        return _empty_panel(lang, "shield")
    score = int(report.get("risk_score", 0))
    raw_verdict = str(report.get("shield_verdict") or "VERIFY FIRST")
    kind = _verdict_kind(raw_verdict)
    return f"""
    <article class="shield-card {kind}">
      <div class="verdict-topline">
        <div class="verdict-icon">{_status_icon(kind)}</div>
        <div>
          <div class="verdict-label">{_esc(_localized_verdict(raw_verdict, lang))}</div>
          <div class="verdict-score">{_esc(t(lang, "shield_score"))}: {score}/100</div>
        </div>
      </div>
      <div class="action-block">
        <div class="result-label">{_esc(t(lang, "shield_action"))}</div>
        <div class="action-copy">{_esc(_localized_action(report, lang))}</div>
      </div>
      <div class="trusted-card">
        <div class="result-label">{_esc(t(lang, "shield_trusted"))}</div>
        {_esc(_localized_script(report, lang))}
      </div>
      <div class="court-hint">{_esc(t(lang, "shield_court_hint"))}</div>
    </article>
    """


def render_shield_guide(lang: str) -> str:
    items = (
        ("stop", "verdict_stop", "shield_guide_stop"),
        ("verify", "verdict_verify", "shield_guide_verify"),
        ("safe", "verdict_safe", "shield_guide_safe"),
    )
    cards = "".join(
        f"""
        <div class="guide-card {kind}">
          <div class="guide-state">{_esc(t(lang, verdict_key))}</div>
          <div>{_esc(t(lang, copy_key))}</div>
        </div>
        """
        for kind, verdict_key, copy_key in items
    )
    return f"""
    <section class="shield-guide">
      <div class="section-kicker">{_esc(t(lang, "shield_guide_title"))}</div>
      <div class="guide-grid">{cards}</div>
    </section>
    """


def _judge_copy(report: dict[str, Any], lang: str) -> tuple[str, str]:
    score = int(report.get("risk_score", 0))
    if score >= 80:
        return t(lang, "judge_verdict_scam"), t(lang, "judge_sc")
    if score >= 50:
        return t(lang, "judge_verdict_suspicious"), t(lang, "judge_suspicious")
    if score >= 20:
        return t(lang, "judge_verdict_caution"), t(lang, "judge_caution")
    return t(lang, "judge_verdict_safe"), t(lang, "judge_safe")


def render_case_summary(report: dict[str, Any] | None, lang: str) -> str:
    if not report:
        return _empty_panel(lang, "court")
    score = int(report.get("risk_score", 0))
    verdict, rationale = _judge_copy(report, lang)
    count = len(report.get("detected_patterns") or [])
    return f"""
    <section class="case-summary" style="--score-color:{_score_color(score)}">
      <div class="score-orbit">
        <div>
          <div class="score-number">{score}</div>
          <div class="score-caption">{_esc(t(lang, "court_risk_score"))}</div>
        </div>
      </div>
      <div>
        <div class="section-kicker">{_esc(t(lang, "court_case_summary"))}</div>
        <div class="case-verdict">{_esc(verdict)}</div>
        <div class="case-rationale">{_esc(rationale)}</div>
        <div class="case-meta">{_esc(t(lang, "court_evidence_count", count=count))}</div>
      </div>
    </section>
    """


def _plain_to_html(text: str) -> str:
    escaped = _esc(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return "<p>" + escaped.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"


def _clerk_steps(lang: str, score: int) -> list[str]:
    steps = [t(lang, "next_official"), t(lang, "next_contact")]
    if score >= 35:
        steps.insert(1, t(lang, "next_no_money"))
    if score >= 70:
        steps.extend([t(lang, "next_report"), t(lang, "next_accounts")])
    return steps


def _role_content(role: str, report: dict[str, Any], lang: str) -> str:
    score = int(report.get("risk_score", 0))
    patterns = [
        item for item in report.get("detected_patterns", []) if isinstance(item, dict)
    ]
    if role == "detective":
        if not patterns:
            return f"<p>{_esc(t(lang, 'role_no_flags'))}</p>"
        items = "".join(f"<li>{_esc(_pattern_label(item, lang))}</li>" for item in patterns)
        return f"<ul>{items}</ul>"
    if role == "prosecutor":
        if lang == "en":
            return _plain_to_html(str(report.get("prosecutor_argument", "")))
        items = "".join(f"<li>{_esc(_pattern_label(item, lang))}</li>" for item in patterns)
        return (
            f"<p>{_esc(t(lang, 'prosecutor_intro', count=len(patterns)))}</p>"
            f"<ul>{items}</ul><p>{_esc(t(lang, 'prosecutor_close'))}</p>"
        )
    if role == "defender":
        if lang == "en":
            return _plain_to_html(str(report.get("defender_argument", "")))
        key = "defender_high" if score >= 70 else "defender_medium" if score >= 35 else "defender_low"
        return f"<p>{_esc(t(lang, key))}</p>"
    if role == "judge":
        verdict, rationale = _judge_copy(report, lang)
        return f"<p><strong>{_esc(verdict)}</strong></p><p>{_esc(rationale)}</p>"
    reply_key = "clerk_reply_high" if score >= 70 else "clerk_reply_verify" if score >= 35 else "clerk_reply_safe"
    items = "".join(f"<li>{_esc(step)}</li>" for step in _clerk_steps(lang, score))
    return (
        f"<p><strong>{_esc(t(lang, 'role_safe_reply'))}</strong></p>"
        f"<p>{_esc(t(lang, reply_key))}</p>"
        f"<p><strong>{_esc(t(lang, 'role_next_steps'))}</strong></p><ol>{items}</ol>"
    )


def render_role(role: str, report: dict[str, Any] | None, lang: str) -> str:
    if not report:
        return _empty_panel(lang, "court")
    title_key = f"role_title_{role}"
    subtitle_key = f"role_subtitle_{role}"
    return f"""
    <section class="role-panel">
      <div class="role-header">
        <div class="role-avatar">{ROLE_SVGS.get(role, "")}</div>
        <div>
          <div class="role-title">{_esc(t(lang, title_key))}</div>
          <div class="role-subtitle">{_esc(t(lang, subtitle_key))}</div>
        </div>
      </div>
      <div class="role-body">{_role_content(role, report, lang)}</div>
    </section>
    """


def render_vision_witness(report: dict[str, Any] | None, lang: str) -> str:
    if not report or not report.get("image_evidence_present"):
        return ""
    status = str(report.get("vision_status") or "inactive")
    analyzed = status == "analyzed" and bool(report.get("extracted_text"))
    status_key = {
        "analyzed": "vision_analyzed",
        "failed": "vision_failed",
        "not_available": "vision_not_available",
    }.get(status, "vision_inactive")
    fields: list[str] = []
    screenshot_type = report.get("screenshot_type")
    if screenshot_type:
        fields.append(
            f'<div class="vision-field"><div class="result-label">{_esc(t(lang, "vision_type"))}</div>{_esc(screenshot_type)}</div>'
        )
    confidence = float(report.get("vision_confidence") or 0)
    if confidence:
        fields.append(
            f'<div class="vision-field"><div class="result-label">{_esc(t(lang, "vision_confidence"))}</div>{confidence:.0%}</div>'
        )
    extracted = report.get("extracted_text")
    if extracted:
        fields.append(
            f'<div class="vision-field wide"><div class="result-label">{_esc(t(lang, "vision_extracted"))}</div>{_esc(extracted)}</div>'
        )
    clues = report.get("screenshot_risk_clues") or []
    if clues:
        clue_items = "".join(f"<li>{_esc(clue)}</li>" for clue in clues)
        fields.append(
            f'<div class="vision-field wide"><div class="result-label">{_esc(t(lang, "vision_clues"))}</div><ul>{clue_items}</ul></div>'
        )
    error = report.get("vision_error")
    if error and not analyzed:
        fields.append(
            f'<div class="vision-field wide"><div class="result-label">{_esc(t(lang, "vision_error"))}</div>{_esc(error)}</div>'
        )
    model = report.get("vision_model") or report.get("vision_backend") or "none"
    return f"""
    <section class="vision-card">
      <div class="vision-heading">
        <div class="vision-title">{CAMERA_ICON}{_esc(t(lang, "vision_title"))}</div>
        <div class="status-pill {'ok' if analyzed else 'warn'}">{_esc(t(lang, status_key))}</div>
      </div>
      <div class="vision-grid">{''.join(fields)}</div>
      <div class="vision-privacy">{_esc(t(lang, "vision_privacy", model=model))}</div>
    </section>
    """


def _truncate(text: str, length: int = 320) -> str:
    return text if len(text) <= length else text[: length - 1].rstrip() + "..."


def render_companion(
    report: dict[str, Any] | None,
    lang: str,
    platform: str,
) -> str:
    if not report:
        sender_key = "companion_buyer" if platform == "marketplace" else "companion_unknown"
        return f"""
        <section class="companion-shell companion-shell-empty platform-{platform}">
          <div class="companion-header">
            <span class="platform-name">{_esc(t(lang, f"companion_{platform}"))}</span>
            <span class="prototype-badge">prototype</span>
          </div>
          <div class="conversation companion-conversation-empty">
            <div class="message-card message-placeholder">
              <div class="message-meta">{_esc(t(lang, sender_key))} · {_esc(t(lang, "companion_now"))}</div>
              {_esc(t(lang, "companion_selected_placeholder"))}
            </div>
          </div>
          <div class="companion-result companion-result-empty">
            <div class="empty-review-icon">{SHIELD_ICON}</div>
            <div>
              <div class="companion-empty-title">{_esc(t(lang, "companion_empty_title"))}</div>
              <div class="companion-empty-copy">{_esc(t(lang, "companion_review_body"))}</div>
            </div>
          </div>
          <div class="companion-empty-foot">{_esc(t(lang, "companion_empty"))}</div>
        </section>
        """
    raw_verdict = str(report.get("shield_verdict") or "VERIFY FIRST")
    kind = _verdict_kind(raw_verdict)
    sender_key = "companion_buyer" if platform == "marketplace" else "companion_unknown"
    text = str(report.get("input_text") or report.get("effective_input_text") or "")
    return f"""
    <section class="companion-shell platform-{platform}">
      <div class="companion-header">
        <span class="platform-name">{_esc(t(lang, f"companion_{platform}"))}</span>
        <span class="prototype-badge">prototype</span>
      </div>
      <div class="conversation">
        <div class="message-card">
          <div class="message-meta">{_esc(t(lang, sender_key))} · {_esc(t(lang, "companion_now"))}</div>
          {_esc(_truncate(text))}
        </div>
      </div>
      <div class="companion-result">
        <div class="mini-verdict">
          <span style="color:{'var(--sc-danger)' if kind == 'stop' else 'var(--sc-warning)' if kind == 'verify' else 'var(--sc-safe)'}">
            {_esc(_localized_verdict(raw_verdict, lang))}
          </span>
          <span class="mini-score">{int(report.get("risk_score", 0))}/100</span>
        </div>
        <div class="safe-reply">
          <div class="result-label">{_esc(t(lang, "companion_safe_reply"))}</div>
          {_esc(_localized_script(report, lang))}
        </div>
        <div class="safe-reply">
          <div class="result-label">{_esc(t(lang, "companion_action"))}</div>
          {_esc(_localized_action(report, lang))}
        </div>
        <div class="companion-cta">{_esc(t(lang, "companion_take_to_court"))}</div>
      </div>
    </section>
    """


def _clean_visual_risk_clues(raw_clues: list[str], extracted_text: str) -> list[str]:
    placeholders = {"list", "of", "visual", "red", "flags", "item", "none", "n/a", "unknown"}
    cleaned = [
        clue.strip()
        for clue in raw_clues
        if clue and clue.lower().strip() not in placeholders and len(clue.strip()) >= 3
    ]
    lowered = extracted_text.lower()
    fallback_map = {
        "suspicious link detected": bool(re.search(r"https?://", lowered)),
        "package delivery action request": any(
            word in lowered for word in ("fedex", "dhl", "usps", "ups", "package", "parcel", "delivery")
        ),
        "money or payment request": any(
            word in lowered for word in ("payment", "pay", "wire", "gift card", "crypto", "zelle", "venmo")
        ),
        "credential or code request": any(
            word in lowered for word in ("otp", "code", "password", "pin", "verify your identity")
        ),
        "urgency or deadline": any(
            word in lowered for word in ("urgent", "immediately", "24 hours", "deadline", "act now")
        ),
    }
    existing = {item.lower() for item in cleaned}
    for label, triggered in fallback_map.items():
        if triggered and label not in existing:
            cleaned.append(label)
    return cleaned


@gpu_function(duration=180)
def analyze_message(
    message: str,
    image_path: str | None,
    lang: str,
) -> tuple[str, dict[str, Any] | None, str, str, str, str, str, str]:
    lang = normalize_lang(lang)
    has_text = bool(message and message.strip())
    has_image = bool(image_path)
    if not has_text and not has_image:
        return (
            render_case_summary(None, lang),
            None,
            "",
            render_shield(None, lang),
            "",
            render_companion(None, lang, "whatsapp"),
            render_companion(None, lang, "sms"),
            render_companion(None, lang, "marketplace"),
        )

    vision_backend = get_vision_backend()
    vision_result: dict[str, Any] | None = None
    if has_image:
        vision_result = vision_backend.analyze_image(image_path, context_text=message or None)

    pasted_text = message.strip() if has_text else ""
    extracted_text = ""
    input_sources: list[str] = []
    if pasted_text:
        input_sources.append("pasted_text")
    if vision_result:
        extracted_text = (
            vision_result.get("recommended_text_for_analysis")
            or vision_result.get("extracted_text")
            or ""
        ).strip()
        if extracted_text:
            input_sources.append("vision_extracted_text")

    if pasted_text and extracted_text:
        effective_text = f"[User text]: {pasted_text}\n[From screenshot]: {extracted_text}"
    else:
        effective_text = pasted_text or extracted_text

    report = backend.analyze(effective_text)
    if has_image and vision_result:
        vision_status = str(vision_result.get("vision_status") or "inactive")
        vision_succeeded = vision_status == "analyzed" and bool(extracted_text)
        if not vision_succeeded and report.risk_score < 35:
            report = dataclasses.replace(
                report,
                risk_score=35,
                risk_level="medium",
                verdict="VERIFY FIRST",
                shield_verdict="VERIFY FIRST",
                immediate_action="Screenshot analysis was unavailable. Verify independently before acting.",
                trusted_contact_script="The screenshot could not be read. Please help me verify it before I act.",
                recommended_action="verify_independently",
            )
        report = dataclasses.replace(
            report,
            evidence_source="text_and_screenshot" if has_text else "screenshot",
            image_evidence_present=True,
            vision_backend=vision_backend.backend_name,
            vision_model=vision_result.get("vision_model"),
            vision_status=vision_status,
            vision_summary=vision_result.get("vision_summary"),
            extracted_text=vision_result.get("extracted_text"),
            screenshot_type=vision_result.get("screenshot_type"),
            screenshot_risk_clues=_clean_visual_risk_clues(
                vision_result.get("screenshot_risk_clues", []),
                extracted_text,
            ),
            recommended_text_for_analysis=vision_result.get("recommended_text_for_analysis"),
            vision_confidence=float(vision_result.get("vision_confidence", 0.0)),
            vision_error=vision_result.get("vision_error"),
            effective_input_text=effective_text,
            input_sources=input_sources,
            analysis_used_vision_text=bool(extracted_text),
        )
    else:
        report = dataclasses.replace(
            report,
            effective_input_text=effective_text,
            input_sources=input_sources,
            analysis_used_vision_text=False,
        )

    report_dict = report.to_dict()
    return (
        render_case_summary(report_dict, lang),
        report_dict,
        report.to_json(),
        render_shield(report_dict, lang),
        render_vision_witness(report_dict, lang),
        render_companion(report_dict, lang, "whatsapp"),
        render_companion(report_dict, lang, "sms"),
        render_companion(report_dict, lang, "marketplace"),
    )


def analyze_text_api(text: str) -> dict[str, Any]:
    """Return a stable, text-only result for explicit companion requests."""
    selected_text = (text or "").strip()
    if not selected_text:
        return {
            "verdict": "VERIFY FIRST",
            "risk_score": 35,
            "recommended_action": (
                "No selected text was received. Do not click links or share codes; "
                "open Scam Court and review the message manually."
            ),
            "trusted_contact_script": (
                "I could not analyze the message automatically. Can you help me "
                "verify it through an official channel?"
            ),
            "evidence_summary": ["No selected text was provided."],
            "report_id": None,
        }

    try:
        report = backend.analyze(selected_text).to_dict()
    except Exception:
        return {
            "verdict": "VERIFY FIRST",
            "risk_score": 35,
            "recommended_action": (
                "Automatic analysis was unavailable. Do not click links or share "
                "codes; verify through an official channel."
            ),
            "trusted_contact_script": (
                "Scam Court could not analyze this automatically. Can you help me "
                "verify the message before I act?"
            ),
            "evidence_summary": ["The text analysis backend was unavailable."],
            "report_id": None,
        }

    evidence_summary = [
        str(item.get("label"))
        for item in report.get("detected_patterns", [])
        if isinstance(item, dict) and item.get("label")
    ]
    if not evidence_summary:
        evidence_summary = ["No strong scam pattern was visible in the selected text."]

    return {
        "verdict": str(report.get("shield_verdict") or "VERIFY FIRST"),
        "risk_score": int(report.get("risk_score", 35)),
        "recommended_action": str(
            report.get("immediate_action")
            or "Pause and verify through an official channel before acting."
        ),
        "trusted_contact_script": str(report.get("trusted_contact_script") or ""),
        "evidence_summary": evidence_summary,
        "report_id": report.get("report_id"),
    }


def _call_result(
    asks_money: bool,
    asks_code: bool,
    claims_family: bool,
    urgency: bool,
    secrecy: bool,
) -> dict[str, Any]:
    result = CourtroomEngine.evaluate_call_checklist(
        asks_money=asks_money,
        asks_code=asks_code,
        claims_family_new_number=claims_family,
        creates_urgency_or_fear=urgency,
        asks_secrecy=secrecy,
    )
    result["selected"] = [asks_money, asks_code, claims_family, urgency, secrecy]
    return result


def render_call_result(result: dict[str, Any] | None, lang: str) -> str:
    if not result:
        return _empty_panel(lang, "call")
    score = int(result.get("score", 0))
    kind = "stop" if score >= 70 else "verify" if score >= 35 else "safe"
    verdict = t(lang, {"stop": "verdict_stop", "verify": "verdict_verify", "safe": "verdict_safe"}[kind])
    action_key = "call_action_hangup" if score >= 70 else "call_action_pause" if score >= 35 else "call_action_caution"
    tag_keys = {
        "asks_money": "call_tag_money",
        "asks_code": "call_tag_code",
        "claims_family_new_number": "call_tag_family",
        "creates_urgency_or_fear": "call_tag_urgency",
        "asks_secrecy": "call_tag_secrecy",
    }
    tags = "".join(
        f'<span class="warning-tag">{_esc(t(lang, tag_keys[tag]))}</span>'
        for tag in result.get("tags", [])
        if tag in tag_keys
    )
    script_report = {
        "risk_score": score,
        "scenario_tags": [
            "otp_theft" if tag == "asks_code" else
            "payment_request" if tag == "asks_money" else
            "impersonation_family" if tag == "claims_family_new_number" else tag
            for tag in result.get("tags", [])
        ],
    }
    return f"""
    <article class="shield-card {kind}">
      <div class="verdict-topline">
        <div class="verdict-icon">{_status_icon(kind)}</div>
        <div>
          <div class="verdict-label">{_esc(verdict)}</div>
          <div class="verdict-score">{_esc(t(lang, "shield_score"))}: {score}/100</div>
        </div>
      </div>
      <div class="action-block">
        <div class="result-label">{_esc(t(lang, "shield_action"))}</div>
        <div class="action-copy">{_esc(t(lang, action_key))}</div>
      </div>
      <div class="trusted-card">
        <div class="result-label">{_esc(t(lang, "shield_trusted"))}</div>
        {_esc(_localized_script(script_report, lang))}
      </div>
      <div class="warning-tags">{tags}</div>
    </article>
    """


def analyze_call(
    asks_money: bool,
    asks_code: bool,
    claims_family: bool,
    urgency: bool,
    secrecy: bool,
    lang: str,
) -> tuple[str, dict[str, Any]]:
    result = _call_result(asks_money, asks_code, claims_family, urgency, secrecy)
    return render_call_result(result, normalize_lang(lang)), result


def _role_updates(active_role: str) -> list[dict[str, Any]]:
    return [
        gr.update(variant="primary" if role == active_role else "secondary")
        for role in ROLE_ORDER
    ]


def select_role(
    role: str,
    report: dict[str, Any] | None,
    lang: str,
) -> tuple[Any, ...]:
    return (
        render_role(role, report, normalize_lang(lang)),
        role,
        *_role_updates(role),
    )


def _make_role_handler(role: str):
    def handler(report: dict[str, Any] | None, lang: str) -> tuple[Any, ...]:
        return select_role(role, report, lang)

    return handler


def load_random_example() -> str:
    return random.choice(EXAMPLES)["text"]


def _diagnostic_values() -> dict[str, str]:
    import gradio

    text_backend = getattr(backend, "model_backend", "heuristic_v1")
    vision_name = get_vision_backend().backend_name
    return {
        "text": text_backend,
        "vision": vision_name,
        "model": get_vision_model_id(),
        "cache": os.getenv("HF_HOME", "~/.cache/huggingface"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "gradio": gradio.__version__,
        "contract": "v2.2.0",
        "space": "Ready" if os.getenv("SPACE_ID") else "Local / Space-ready",
        "ui": UI_VERSION,
        "build": BUILD_MARKER,
    }


def render_system_brand(lang: str) -> str:
    return f"""
    <div class="utility-brand">
      <div class="utility-brand-mark">{SHIELD_ICON}</div>
      <div>
        <div class="utility-brand-name">Scam Court AI</div>
        <div class="utility-status"><span class="status-dot"></span>{_esc(t(lang, "system_online"))}</div>
        <div class="utility-privacy">{_esc(t(lang, "system_privacy"))} · {_esc(UI_VERSION)} · {_esc(BUILD_MARKER)}</div>
      </div>
    </div>
    """


def render_diagnostics(lang: str) -> str:
    values = _diagnostic_values()
    labels = {
        "text": "system_text",
        "vision": "system_vision",
        "model": "system_model",
        "cache": "system_cache",
        "python": "system_python",
        "gradio": "system_gradio",
        "contract": "system_contract",
        "space": "system_space",
        "ui": "system_ui",
        "build": "system_build",
    }
    cards = "".join(
        f"""
        <div class="diagnostic-item">
          <div class="diagnostic-label">{_esc(t(lang, labels[key]))}</div>
          <div class="diagnostic-value">{_esc(value)}</div>
        </div>
        """
        for key, value in values.items()
    )
    return f'<div class="diagnostic-grid">{cards}</div>'


def render_api_panel(lang: str) -> str:
    return f"""
    <div class="api-card">
      <div class="api-contract"><span class="api-status-dot"></span>{_esc(t(lang, "api_contract"))}</div>
      <div class="api-copy">{_esc(t(lang, "api_copy"))}</div>
      <div class="api-meta">{_esc(t(lang, "api_privacy"))}</div>
      <div class="api-export-hint">{_esc(t(lang, "api_export_hint"))}</div>
    </div>
    """


def _clear_workspace(lang: str) -> tuple[Any, ...]:
    language = normalize_lang(lang)
    return (
        None,
        None,
        "",
        "",
        "",
        render_case_summary(None, language),
        None,
        "",
        render_shield(None, language),
        "",
        "",
        "",
        render_companion(None, language, "whatsapp"),
        render_companion(None, language, "sms"),
        render_companion(None, language, "marketplace"),
        render_role("detective", None, language),
        "detective",
        *_role_updates("detective"),
    )


def build_ui() -> gr.Blocks:
    lang = DEFAULT_LANG
    with gr.Blocks(
        title="Scam Court AI",
        fill_width=True,
        css=build_css(ROLE_SVGS),
        js=PAGE_JS,
    ) as demo:
        lang_state = gr.State(lang)
        theme_state = gr.State("dark")
        report_state = gr.State(None)
        active_role_state = gr.State("detective")
        call_state = gr.State(None)

        hero = gr.HTML(
            f"""
            <header id="sc-hero">
              <h1>Scam Court AI</h1>
              <p>{_esc(t(lang, "app_subtitle"))}</p>
            </header>
            """
        )
        ui_state_marker = gr.HTML(render_ui_state(lang, "dark"))

        with gr.Tabs(elem_classes=["mode-tabs"]) as mode_tabs:
            with gr.Tab(t(lang, "tab_shield"), id="shield") as shield_tab:
                shield_intro = gr.HTML(_mode_intro(lang, "shield"))
                with gr.Row(equal_height=False, elem_classes=["mode-layout", "shield-layout"]):
                    with gr.Column(
                        scale=5,
                        min_width=320,
                        elem_classes=["sc-panel", "evidence-panel"],
                    ):
                        shield_input_label = gr.HTML(_label(t(lang, "input_heading")))
                        shield_input = gr.Textbox(
                            placeholder=t(lang, "input_placeholder"),
                            lines=9,
                            max_lines=16,
                            show_label=False,
                            elem_id="shield-message",
                        )
                        shield_upload_label = gr.HTML(
                            _label(t(lang, "upload_heading"), "quick-label")
                        )
                        shield_image = gr.Image(
                            type="filepath",
                            sources=["upload"],
                            show_label=False,
                            interactive=True,
                            height=230,
                            elem_classes=["image-input"],
                        )
                        shield_upload_hint = gr.HTML(
                            f'<div class="helper-copy">{_esc(t(lang, "upload_hint"))}</div>'
                        )
                        with gr.Row():
                            shield_submit = gr.Button(
                                t(lang, "btn_analyze"),
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                            shield_random = gr.Button(
                                t(lang, "btn_random"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                            shield_clear = gr.Button(
                                t(lang, "btn_clear"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                        shield_quick_label = gr.HTML(
                            _label(t(lang, "quick_examples"), "quick-label")
                        )
                        shield_examples: list[tuple[gr.Button, str]] = []
                        with gr.Row(elem_classes=["example-grid"]):
                            for example in EXAMPLES:
                                button = gr.Button(
                                    t(lang, example["key"]),
                                    size="sm",
                                    elem_classes=["example-btn"],
                                )
                                shield_examples.append((button, example["text"]))
                    with gr.Column(
                        scale=7,
                        min_width=320,
                        elem_classes=["result-column", "shield-result-column"],
                    ):
                        shield_output = gr.HTML(render_shield(None, lang))
                        shield_vision = gr.HTML("")
                        shield_guide = gr.HTML(render_shield_guide(lang))

            with gr.Tab(t(lang, "tab_court"), id="court") as court_tab:
                court_intro = gr.HTML(_mode_intro(lang, "court"))
                with gr.Row(equal_height=False, elem_classes=["mode-layout", "court-layout"]):
                    with gr.Column(
                        scale=4,
                        min_width=300,
                        elem_classes=["sc-panel", "evidence-panel"],
                    ):
                        court_input_label = gr.HTML(_label(t(lang, "input_heading")))
                        court_input = gr.Textbox(
                            placeholder=t(lang, "input_placeholder"),
                            lines=9,
                            max_lines=16,
                            show_label=False,
                            elem_id="court-message",
                        )
                        court_upload_label = gr.HTML(
                            _label(t(lang, "upload_heading"), "quick-label")
                        )
                        court_image = gr.Image(
                            type="filepath",
                            sources=["upload"],
                            show_label=False,
                            interactive=True,
                            height=220,
                            elem_classes=["image-input"],
                        )
                        court_upload_hint = gr.HTML(
                            f'<div class="helper-copy">{_esc(t(lang, "upload_hint"))}</div>'
                        )
                        with gr.Row():
                            court_submit = gr.Button(
                                t(lang, "btn_court"),
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                            court_random = gr.Button(
                                t(lang, "btn_random"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                            court_clear = gr.Button(
                                t(lang, "btn_clear"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                        court_quick_label = gr.HTML(
                            _label(t(lang, "quick_examples"), "quick-label")
                        )
                        court_examples: list[tuple[gr.Button, str]] = []
                        with gr.Row(elem_classes=["example-grid"]):
                            for example in EXAMPLES:
                                button = gr.Button(
                                    t(lang, example["key"]),
                                    size="sm",
                                    elem_classes=["example-btn"],
                                )
                                court_examples.append((button, example["text"]))
                    with gr.Column(
                        scale=8,
                        min_width=320,
                        elem_classes=["result-column", "court-result-column"],
                    ):
                        case_summary = gr.HTML(render_case_summary(None, lang))
                        court_vision = gr.HTML("")
                        court_members_label = gr.HTML(
                            _label(t(lang, "court_members"), "role-section-label")
                        )
                        with gr.Row(elem_classes=["role-selector"]):
                            role_buttons = []
                            for role in ROLE_ORDER:
                                with gr.Column(
                                    min_width=120,
                                    elem_classes=["role-card", f"role-card-{role}"],
                                ):
                                    gr.HTML(
                                        f'<div class="role-selector-emblem">{ROLE_SVGS[role]}</div>'
                                    )
                                    role_buttons.append(
                                        gr.Button(
                                            t(lang, f"role_{role}"),
                                            variant="primary" if role == "detective" else "secondary",
                                            elem_classes=["role-btn", f"role-btn-{role}"],
                                        )
                                    )
                        role_display = gr.HTML(render_role("detective", None, lang))
                        with gr.Accordion(
                            t(lang, "court_export"),
                            open=False,
                            elem_classes=["utility-accordion"],
                        ) as export_accordion:
                            json_out = gr.Code(
                                value="",
                                language="json",
                                lines=18,
                                max_lines=18,
                                label=t(lang, "court_json_label"),
                                interactive=False,
                                elem_classes=["json-code"],
                            )

            with gr.Tab(t(lang, "tab_call"), id="call") as call_tab:
                call_intro = gr.HTML(_mode_intro(lang, "call"))
                with gr.Row(equal_height=False, elem_classes=["mode-layout", "call-layout"]):
                    with gr.Column(
                        scale=5,
                        min_width=320,
                        elem_classes=["sc-panel", "call-panel"],
                    ):
                        call_heading = gr.HTML(_label(t(lang, "call_heading")))
                        call_hint = gr.HTML(
                            f'<div class="helper-copy">{_esc(t(lang, "call_hint"))}</div>'
                        )
                        call_checks = [
                            gr.Checkbox(
                                label=t(lang, key),
                                container=False,
                                elem_classes=["call-factor"],
                            )
                            for key in ("call_money", "call_code", "call_family", "call_urgency", "call_secrecy")
                        ]
                        with gr.Row():
                            call_submit = gr.Button(
                                t(lang, "call_check"),
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                            call_reset = gr.Button(
                                t(lang, "call_reset"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                    with gr.Column(
                        scale=7,
                        min_width=320,
                        elem_classes=["result-column", "call-result-column"],
                    ):
                        call_output = gr.HTML(render_call_result(None, lang))

            with gr.Tab(t(lang, "tab_companion"), id="companion") as companion_tab:
                companion_intro = gr.HTML(_mode_intro(lang, "companion"))
                companion_note = gr.HTML(
                    f'<div class="prototype-note">{_esc(t(lang, "companion_prototype"))}</div>'
                )
                with gr.Row(
                    equal_height=False,
                    elem_classes=["mode-layout", "companion-layout"],
                ):
                    with gr.Column(
                        scale=4,
                        min_width=300,
                        elem_classes=["sc-panel", "companion-input-panel"],
                    ):
                        companion_input_label = gr.HTML(_label(t(lang, "companion_input")))
                        companion_input = gr.Textbox(
                            placeholder=t(lang, "input_placeholder"),
                            lines=10,
                            max_lines=16,
                            show_label=False,
                            elem_id="companion-message",
                        )
                        with gr.Row():
                            companion_submit = gr.Button(
                                t(lang, "btn_companion"),
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                            companion_random = gr.Button(
                                t(lang, "btn_random"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                            companion_clear = gr.Button(
                                t(lang, "btn_clear"),
                                variant="secondary",
                                elem_classes=["secondary-btn"],
                            )
                        companion_quick_label = gr.HTML(
                            _label(t(lang, "quick_examples"), "quick-label")
                        )
                        companion_examples: list[tuple[gr.Button, str]] = []
                        with gr.Row(elem_classes=["example-grid"]):
                            for example in EXAMPLES:
                                button = gr.Button(
                                    t(lang, example["key"]),
                                    size="sm",
                                    elem_classes=["example-btn"],
                                )
                                companion_examples.append((button, example["text"]))
                    with gr.Column(
                        scale=8,
                        min_width=320,
                        elem_classes=["result-column", "companion-preview-column"],
                    ):
                        companion_vision = gr.HTML("")
                        with gr.Tabs(elem_classes=["companion-tabs"]):
                            with gr.Tab(t(lang, "companion_whatsapp")) as whatsapp_tab:
                                companion_whatsapp = gr.HTML(
                                    render_companion(None, lang, "whatsapp")
                                )
                            with gr.Tab(t(lang, "companion_sms")) as sms_tab:
                                companion_sms = gr.HTML(render_companion(None, lang, "sms"))
                            with gr.Tab(t(lang, "companion_marketplace")) as marketplace_tab:
                                companion_marketplace = gr.HTML(
                                    render_companion(None, lang, "marketplace")
                                )

        with gr.Column(elem_classes=["utility-dock"]):
            with gr.Row(equal_height=True, elem_classes=["utility-topbar"]):
                with gr.Column(scale=3, min_width=320):
                    system_brand = gr.HTML(render_system_brand(lang))
                language_dropdown = gr.Dropdown(
                    choices=[("English", "en"), ("Español", "es")],
                    value=lang,
                    label=t(lang, "language"),
                    interactive=True,
                    filterable=False,
                    elem_classes=["settings-control", "language-control"],
                    scale=1,
                )
                theme_dropdown = gr.Dropdown(
                    choices=theme_choices(lang),
                    value="dark",
                    label=t(lang, "theme"),
                    interactive=True,
                    filterable=False,
                    elem_classes=["settings-control", "theme-control"],
                    scale=1,
                )
            with gr.Accordion(
                t(lang, "runtime_title"),
                open=False,
                elem_classes=["utility-accordion"],
            ) as runtime_accordion:
                diagnostics_html = gr.HTML(render_diagnostics(lang))
                refresh_diagnostics = gr.Button(
                    t(lang, "runtime_refresh"),
                    variant="secondary",
                    size="sm",
                    elem_classes=["secondary-btn"],
                )
            with gr.Accordion(
                t(lang, "api_title"),
                open=False,
                elem_classes=["utility-accordion"],
            ) as api_accordion:
                api_html = gr.HTML(render_api_panel(lang))
            footer_tagline = gr.HTML(
                f'<div class="footer-tagline">{_esc(t(lang, "footer_tagline"))}</div>'
            )

        api_text_input = gr.Textbox(visible=False)
        api_json_output = gr.JSON(visible=False)
        api_submit = gr.Button(visible=False)
        api_submit.click(
            fn=analyze_text_api,
            inputs=api_text_input,
            outputs=api_json_output,
            api_name="analyze_text",
        )

        analysis_outputs = [
            case_summary,
            report_state,
            json_out,
            shield_output,
            shield_vision,
            companion_whatsapp,
            companion_sms,
            companion_marketplace,
        ]
        role_outputs = [role_display, active_role_state, *role_buttons]

        for trigger, text_input, image_input in (
            (shield_submit, shield_input, shield_image),
            (court_submit, court_input, court_image),
        ):
            trigger.click(
                fn=analyze_message,
                inputs=[text_input, image_input, lang_state],
                outputs=analysis_outputs,
            ).then(
                fn=_make_role_handler("detective"),
                inputs=[report_state, lang_state],
                outputs=role_outputs,
            ).then(
                fn=lambda report, language: render_vision_witness(report, language),
                inputs=[report_state, lang_state],
                outputs=court_vision,
            )

        companion_submit.click(
            fn=lambda message, language: analyze_message(message, None, language),
            inputs=[companion_input, lang_state],
            outputs=analysis_outputs,
        ).then(
            fn=_make_role_handler("detective"),
            inputs=[report_state, lang_state],
            outputs=role_outputs,
        )

        for role, button in zip(ROLE_ORDER, role_buttons):
            button.click(
                fn=_make_role_handler(role),
                inputs=[report_state, lang_state],
                outputs=role_outputs,
            )

        call_submit.click(
            fn=analyze_call,
            inputs=[*call_checks, lang_state],
            outputs=[call_output, call_state],
        )
        call_reset.click(
            fn=lambda language: (
                False,
                False,
                False,
                False,
                False,
                render_call_result(None, language),
                None,
            ),
            inputs=lang_state,
            outputs=[*call_checks, call_output, call_state],
        )

        for buttons, text_input in (
            (shield_examples, shield_input),
            (court_examples, court_input),
            (companion_examples, companion_input),
        ):
            for button, example_text in buttons:
                button.click(fn=lambda value=example_text: value, outputs=text_input)
        shield_random.click(fn=load_random_example, outputs=shield_input)
        court_random.click(fn=load_random_example, outputs=court_input)
        companion_random.click(fn=load_random_example, outputs=companion_input)

        clear_outputs = [
            shield_image,
            court_image,
            shield_input,
            court_input,
            companion_input,
            case_summary,
            report_state,
            json_out,
            shield_output,
            shield_vision,
            court_vision,
            companion_vision,
            companion_whatsapp,
            companion_sms,
            companion_marketplace,
            role_display,
            active_role_state,
            *role_buttons,
        ]
        for clear_button in (shield_clear, court_clear, companion_clear):
            clear_button.click(
                fn=_clear_workspace,
                inputs=lang_state,
                outputs=clear_outputs,
            )

        refresh_diagnostics.click(
            fn=render_diagnostics,
            inputs=lang_state,
            outputs=diagnostics_html,
        )

        theme_dropdown.change(
            fn=lambda theme, language: (
                theme if theme in ("dark", "light") else "dark",
                render_ui_state(language, theme),
            ),
            inputs=[theme_dropdown, lang_state],
            outputs=[theme_state, ui_state_marker],
        )

        locale_outputs = [
            lang_state,
            ui_state_marker,
            hero,
            shield_tab,
            court_tab,
            call_tab,
            companion_tab,
            shield_intro,
            shield_input_label,
            shield_input,
            shield_upload_label,
            shield_upload_hint,
            shield_submit,
            shield_random,
            shield_clear,
            shield_quick_label,
            *[button for button, _ in shield_examples],
            court_intro,
            court_input_label,
            court_input,
            court_upload_label,
            court_upload_hint,
            court_submit,
            court_random,
            court_clear,
            court_quick_label,
            *[button for button, _ in court_examples],
            court_members_label,
            *role_buttons,
            export_accordion,
            json_out,
            call_intro,
            call_heading,
            call_hint,
            *call_checks,
            call_submit,
            call_reset,
            companion_intro,
            companion_note,
            companion_input_label,
            companion_input,
            companion_submit,
            companion_random,
            companion_clear,
            companion_quick_label,
            *[button for button, _ in companion_examples],
            whatsapp_tab,
            sms_tab,
            marketplace_tab,
            system_brand,
            language_dropdown,
            theme_dropdown,
            runtime_accordion,
            diagnostics_html,
            refresh_diagnostics,
            api_accordion,
            api_html,
            footer_tagline,
            shield_output,
            shield_guide,
            case_summary,
            shield_vision,
            court_vision,
            companion_vision,
            companion_whatsapp,
            companion_sms,
            companion_marketplace,
            role_display,
            call_output,
        ]

        def localize_ui(
            selected_lang: str,
            current_theme: str,
            report: dict[str, Any] | None,
            active_role: str,
            saved_call: dict[str, Any] | None,
        ) -> list[Any]:
            language = normalize_lang(selected_lang)
            example_updates = [gr.update(value=t(language, example["key"])) for example in EXAMPLES]
            vision_html = render_vision_witness(report, language)
            return [
                language,
                gr.update(value=render_ui_state(language, current_theme)),
                gr.update(
                    value=(
                        f'<header id="sc-hero"><h1>Scam Court AI</h1>'
                        f'<p>{_esc(t(language, "app_subtitle"))}</p></header>'
                    )
                ),
                gr.update(label=t(language, "tab_shield")),
                gr.update(label=t(language, "tab_court")),
                gr.update(label=t(language, "tab_call")),
                gr.update(label=t(language, "tab_companion")),
                gr.update(value=_mode_intro(language, "shield")),
                gr.update(value=_label(t(language, "input_heading"))),
                gr.update(placeholder=t(language, "input_placeholder")),
                gr.update(value=_label(t(language, "upload_heading"), "quick-label")),
                gr.update(value=f'<div class="helper-copy">{_esc(t(language, "upload_hint"))}</div>'),
                gr.update(value=t(language, "btn_analyze")),
                gr.update(value=t(language, "btn_random")),
                gr.update(value=t(language, "btn_clear")),
                gr.update(value=_label(t(language, "quick_examples"), "quick-label")),
                *example_updates,
                gr.update(value=_mode_intro(language, "court")),
                gr.update(value=_label(t(language, "input_heading"))),
                gr.update(placeholder=t(language, "input_placeholder")),
                gr.update(value=_label(t(language, "upload_heading"), "quick-label")),
                gr.update(value=f'<div class="helper-copy">{_esc(t(language, "upload_hint"))}</div>'),
                gr.update(value=t(language, "btn_court")),
                gr.update(value=t(language, "btn_random")),
                gr.update(value=t(language, "btn_clear")),
                gr.update(value=_label(t(language, "quick_examples"), "quick-label")),
                *example_updates,
                gr.update(value=_label(t(language, "court_members"), "role-section-label")),
                *[
                    gr.update(
                        value=t(language, f"role_{role}"),
                        variant="primary" if role == active_role else "secondary",
                    )
                    for role in ROLE_ORDER
                ],
                gr.update(label=t(language, "court_export")),
                gr.update(label=t(language, "court_json_label")),
                gr.update(value=_mode_intro(language, "call")),
                gr.update(value=_label(t(language, "call_heading"))),
                gr.update(value=f'<div class="helper-copy">{_esc(t(language, "call_hint"))}</div>'),
                *[
                    gr.update(label=t(language, key))
                    for key in ("call_money", "call_code", "call_family", "call_urgency", "call_secrecy")
                ],
                gr.update(value=t(language, "call_check")),
                gr.update(value=t(language, "call_reset")),
                gr.update(value=_mode_intro(language, "companion")),
                gr.update(value=f'<div class="prototype-note">{_esc(t(language, "companion_prototype"))}</div>'),
                gr.update(value=_label(t(language, "companion_input"))),
                gr.update(placeholder=t(language, "input_placeholder")),
                gr.update(value=t(language, "btn_companion")),
                gr.update(value=t(language, "btn_random")),
                gr.update(value=t(language, "btn_clear")),
                gr.update(value=_label(t(language, "quick_examples"), "quick-label")),
                *example_updates,
                gr.update(label=t(language, "companion_whatsapp")),
                gr.update(label=t(language, "companion_sms")),
                gr.update(label=t(language, "companion_marketplace")),
                gr.update(value=render_system_brand(language)),
                gr.update(label=t(language, "language")),
                gr.update(
                    label=t(language, "theme"),
                    choices=theme_choices(language),
                    value=current_theme,
                ),
                gr.update(label=t(language, "runtime_title")),
                gr.update(value=render_diagnostics(language)),
                gr.update(value=t(language, "runtime_refresh")),
                gr.update(label=t(language, "api_title")),
                gr.update(value=render_api_panel(language)),
                gr.update(value=f'<div class="footer-tagline">{_esc(t(language, "footer_tagline"))}</div>'),
                gr.update(value=render_shield(report, language)),
                gr.update(value=render_shield_guide(language)),
                gr.update(value=render_case_summary(report, language)),
                gr.update(value=vision_html),
                gr.update(value=vision_html),
                gr.update(value=vision_html),
                gr.update(value=render_companion(report, language, "whatsapp")),
                gr.update(value=render_companion(report, language, "sms")),
                gr.update(value=render_companion(report, language, "marketplace")),
                gr.update(value=render_role(active_role, report, language)),
                gr.update(value=render_call_result(saved_call, language)),
            ]

        language_dropdown.change(
            fn=localize_ui,
            inputs=[
                language_dropdown,
                theme_state,
                report_state,
                active_role_state,
                call_state,
            ],
            outputs=locale_outputs,
        )

    return demo


demo = build_ui()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    print(
        "[startup] "
        f"ui_version={UI_VERSION} "
        f"git_commit={BUILD_MARKER} "
        f"text_backend={getattr(backend, 'model_backend', 'heuristic_v1')} "
        f"vision_backend={get_vision_backend().backend_name} "
        f"vision_model={get_vision_model_id()} "
        f"spaces_import_succeeded={SPACES_IMPORT_SUCCEEDED} "
        f"zero_gpu_decorator_active={ZERO_GPU_DECORATOR_ACTIVE} "
        f"zero_gpu_runtime_active={ZERO_GPU_RUNTIME_ACTIVE} "
        f"port={port}",
        flush=True,
    )
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
    )
