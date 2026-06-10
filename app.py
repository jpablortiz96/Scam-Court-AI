"""Scam Court AI — Premium Gradio courtroom interface with Shield Mode.

Run locally:
    python app.py

Deploy to Hugging Face Spaces:
    Push this repo; Spaces will run app.py automatically.
"""

from __future__ import annotations

import dataclasses
import html
import pathlib
import random
import re
import urllib.parse

import gradio as gr

from courtroom import get_backend, get_vision_backend
from courtroom.config import get_vision_model_id
from courtroom.engine import CourtroomEngine

# ---------------------------------------------------------------------------
# Load local SVG assets
# ---------------------------------------------------------------------------
_ASSET_DIR = pathlib.Path(__file__).parent / "assets"


def _load_svg(name: str) -> str:
    return (_ASSET_DIR / f"{name}.svg").read_text(encoding="utf-8")


ROLE_SVGS = {
    "detective": _load_svg("detective"),
    "prosecutor": _load_svg("prosecutor"),
    "defender": _load_svg("defender"),
    "judge": _load_svg("judge"),
    "clerk": _load_svg("clerk"),
}

ROLE_SUBTITLES = {
    "detective": "Red Flags",
    "prosecutor": "The Case",
    "defender": "Devil's Advocate",
    "judge": "The Ruling",
    "clerk": "Next Steps",
}


# ---------------------------------------------------------------------------
# Dynamic CSS — role button backgrounds + subtitles
# ---------------------------------------------------------------------------
def _build_role_css(svgs: dict[str, str], subtitles: dict[str, str]) -> str:
    bg_rules = []
    for role, svg in svgs.items():
        uri = f"url('data:image/svg+xml;charset=utf-8,{urllib.parse.quote(svg)}')"
        bg_rules.append(
            f".role-btn-{role} {{ background-image: {uri} !important; "
            f"background-repeat: no-repeat !important; "
            f"background-position: center 14px !important; "
            f"background-size: 44px 44px !important; }}"
        )
    sub_rules = []
    for role, sub in subtitles.items():
        sub_rules.append(
            f".role-btn-{role}::after {{ content: '{sub}'; display: block; "
            f"font-family: 'Inter', sans-serif; font-size: 0.6rem; "
            f"color: rgba(197, 160, 89, 0.55); text-transform: uppercase; "
            f"letter-spacing: 1.2px; margin-top: 3px; font-weight: 500; }}"
        )
    return "\n".join(bg_rules + sub_rules)


# ---------------------------------------------------------------------------
# Custom CSS — premium dark courtroom aesthetic + accessible Shield Mode
# ---------------------------------------------------------------------------
COURT_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
  --wood-dark: #120d08;
  --wood-mid: #1a120b;
  --gold: #c5a059;
  --gold-light: #e8d5a3;
  --gold-dim: rgba(197, 160, 89, 0.12);
  --red-flag: #c0392b;
  --green-safe: #27ae60;
  --amber-warn: #f39c12;
  --parchment: #fdfbf7;
}}

body {{
  font-family: 'Inter', sans-serif;
  background: linear-gradient(135deg, #0c0805 0%, #120d08 40%, #1a120b 100%);
  color: var(--parchment);
  min-height: 100vh;
}}

.gradio-container {{
  background: transparent !important;
  max-width: 1280px !important;
}}

/* Header */
#court-header {{
  text-align: center;
  padding: 2.2rem 1rem 1.4rem;
  border-bottom: 1px solid rgba(197, 160, 89, 0.18);
  margin-bottom: 1.8rem;
  position: relative;
}}
#court-header::after {{
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 140px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
}}
#court-header h1 {{
  font-family: 'Playfair Display', serif;
  font-size: 2.6rem;
  color: var(--gold-light);
  margin: 0;
  letter-spacing: 2px;
  font-weight: 700;
}}
#court-header p {{
  color: var(--gold);
  font-size: 1rem;
  margin-top: 0.5rem;
  opacity: 0.8;
  font-weight: 300;
  letter-spacing: 0.5px;
}}

/* Mode tabs */
.mode-tabs > .tab-nav {{
  border-bottom: 1px solid rgba(197, 160, 89, 0.18) !important;
}}
.mode-tabs .tab-nav button {{
  background: transparent !important;
  color: var(--gold) !important;
  font-weight: 600 !important;
  letter-spacing: 0.6px !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  padding: 0.8rem 1.2rem !important;
}}
.mode-tabs .tab-nav button.selected {{
  color: var(--gold-light) !important;
  border-bottom-color: var(--gold) !important;
}}

/* Input panel card */
.input-panel {{
  background: rgba(253, 251, 247, 0.02);
  border: 1px solid rgba(197, 160, 89, 0.1);
  border-radius: 16px;
  padding: 1.4rem;
}}

/* Role selector */
.role-selector {{
  display: flex;
  gap: 0.6rem;
  margin: 1.2rem 0 0.3rem;
}}

.role-btn {{
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: flex-end !important;
  background: rgba(253, 251, 247, 0.02) !important;
  border: 1px solid rgba(197, 160, 89, 0.14) !important;
  border-radius: 14px !important;
  color: var(--gold-light) !important;
  font-family: 'Playfair Display', serif !important;
  font-size: 0.85rem !important;
  padding: 72px 0.3rem 0.7rem !important;
  transition: all 0.3s ease !important;
  cursor: pointer !important;
  min-height: 124px !important;
  line-height: 1.2 !important;
  position: relative !important;
}}

.role-btn:hover {{
  background: rgba(197, 160, 89, 0.06) !important;
  border-color: rgba(197, 160, 89, 0.45) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35) !important;
}}

.role-btn:active {{
  background: rgba(197, 160, 89, 0.14) !important;
  border-color: var(--gold) !important;
  box-shadow: 0 0 28px rgba(197, 160, 89, 0.22), inset 0 0 14px rgba(197, 160, 89, 0.06) !important;
  transform: translateY(0) !important;
}}

/* Active indicator bar */
.active-indicator {{
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.8rem;
}}
.active-bar {{
  flex: 1;
  height: 3px;
  border-radius: 2px;
  background: transparent;
  transition: background 0.3s ease;
}}
.active-bar.on {{
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
}}

/* Verdict gauge */
.gauge-container {{
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.2rem 1rem 0.8rem;
  background: rgba(253, 251, 247, 0.02);
  border: 1px solid rgba(197, 160, 89, 0.1);
  border-radius: 16px;
  margin-bottom: 1.2rem;
}}
.gauge-verdict {{
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem;
  color: var(--gold-light);
  margin-top: 0.5rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}}
.gauge-rationale {{
  font-size: 0.82rem;
  color: rgba(253, 251, 247, 0.65);
  text-align: center;
  margin-top: 0.3rem;
  max-width: 90%;
  line-height: 1.5;
}}

/* Role content panel */
.role-panel {{
  background: rgba(253, 251, 247, 0.02);
  border: 1px solid rgba(197, 160, 89, 0.1);
  border-radius: 16px;
  padding: 1.6rem;
  min-height: 300px;
}}
.role-header {{
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-bottom: 1.2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(197, 160, 89, 0.1);
}}
.role-avatar svg {{
  width: 56px;
  height: 56px;
  filter: drop-shadow(0 0 8px rgba(197, 160, 89, 0.18));
}}
.role-title {{
  font-family: 'Playfair Display', serif;
  font-size: 1.35rem;
  color: var(--gold-light);
  margin: 0;
  line-height: 1.2;
}}
.role-subtitle {{
  font-size: 0.72rem;
  color: var(--gold);
  opacity: 0.6;
  margin: 0.2rem 0 0;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-weight: 500;
}}
.role-body {{
  color: rgba(253, 251, 247, 0.88);
  line-height: 1.7;
  font-size: 0.95rem;
}}
.role-body ul, .role-body ol {{
  padding-left: 1.3rem;
  margin: 0.8rem 0;
}}
.role-body li {{
  margin-bottom: 0.5rem;
}}
.role-body strong {{
  color: var(--gold-light);
  font-weight: 600;
}}
.role-body em {{
  color: rgba(253, 251, 247, 0.5);
  font-style: italic;
}}

/* Shield Mode — high contrast, large type */
.shield-card {{
  border-radius: 18px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 1.2rem;
  border: 3px solid;
}}
.shield-card.stop {{
  background: rgba(192, 57, 43, 0.10);
  border-color: var(--red-flag);
  color: #f5b7b1;
}}
.shield-card.verify {{
  background: rgba(243, 156, 18, 0.10);
  border-color: var(--amber-warn);
  color: #f9e79f;
}}
.shield-card.safe {{
  background: rgba(39, 174, 96, 0.10);
  border-color: var(--green-safe);
  color: #abebc6;
}}
.shield-verdict {{
  font-family: 'Inter', sans-serif;
  font-size: 3.2rem;
  font-weight: 800;
  letter-spacing: 2px;
  margin-bottom: 0.6rem;
}}
.shield-score {{
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 1rem;
}}
.shield-action {{
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.5;
  max-width: 720px;
  margin: 0 auto 1.2rem;
}}
.shield-script {{
  background: rgba(253, 251, 247, 0.06);
  border-left: 4px solid var(--gold);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  text-align: left;
  font-size: 1.05rem;
  line-height: 1.55;
  max-width: 720px;
  margin: 0 auto;
}}
.shield-script-label {{
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--gold);
  margin-bottom: 0.4rem;
}}
.shield-empty {{
  text-align: center;
  padding: 3rem 1rem;
  opacity: 0.6;
  font-size: 1.1rem;
}}

/* Suspicious Call checklist */
.call-check {{
  background: rgba(253, 251, 247, 0.02);
  border: 1px solid rgba(197, 160, 89, 0.1);
  border-radius: 14px;
  padding: 1.2rem;
}}
.call-check label {{
  font-size: 1rem !important;
  color: rgba(253, 251, 247, 0.92) !important;
}}
.call-check .wrap {{
  padding: 0.7rem 0.6rem !important;
  border-radius: 10px !important;
  transition: background 0.2s ease !important;
}}
.call-check .wrap:has(input:checked) {{
  background: rgba(197, 160, 89, 0.12) !important;
  border: 1px solid rgba(197, 160, 89, 0.35) !important;
}}
.call-check input[type="checkbox"] {{
  width: 22px !important;
  height: 22px !important;
  accent-color: var(--gold) !important;
}}
.call-check input[type="checkbox"]:checked {{
  background: var(--gold) !important;
}}

/* Companion previews */
.companion-phone {{
  max-width: 420px;
  margin: 0 auto;
  border: 2px solid rgba(197, 160, 89, 0.25);
  border-radius: 24px;
  background: #0f0f0f;
  overflow: hidden;
}}
.companion-header {{
  background: rgba(197, 160, 89, 0.12);
  padding: 0.7rem 1rem;
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--gold-light);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}
.companion-body {{
  padding: 1rem;
  min-height: 160px;
}}
.companion-bubble-in {{
  background: #2c2c2c;
  color: #eee;
  border-radius: 14px 14px 14px 4px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.6rem;
  font-size: 0.95rem;
  line-height: 1.45;
}}
.companion-bubble-out {{
  background: #005c4b;
  color: #fff;
  border-radius: 14px 14px 4px 14px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.6rem;
  font-size: 0.95rem;
  line-height: 1.45;
  margin-left: auto;
}}
.companion-sms {{
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 1rem;
  font-size: 0.95rem;
  line-height: 1.45;
  color: #eee;
  margin-bottom: 0.6rem;
}}
.companion-sms-label {{
  font-size: 0.75rem;
  color: #888;
  margin-bottom: 0.3rem;
}}
.companion-meta {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #888;
  margin-top: 0.3rem;
}}
.companion-shield {{
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-top: 0.6rem;
}}
.companion-shield.stop {{
  background: rgba(192, 57, 43, 0.25);
  color: #f5b7b1;
}}
.companion-shield.verify {{
  background: rgba(243, 156, 18, 0.25);
  color: #f9e79f;
}}
.companion-shield.safe {{
  background: rgba(39, 174, 96, 0.25);
  color: #abebc6;
}}

/* Vision Witness card */
.vision-card {{
  background: rgba(253, 251, 247, 0.02);
  border: 1px solid rgba(197, 160, 89, 0.15);
  border-radius: 14px;
  padding: 1.2rem;
  margin-top: 1rem;
}}
.vision-header {{
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 700;
  font-size: 1rem;
  color: var(--gold-light);
  margin-bottom: 0.6rem;
}}
.vision-status {{
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}}
.vision-status.inactive {{
  background: rgba(150, 150, 150, 0.2);
  color: #ccc;
}}
.vision-status.loaded {{
  background: rgba(197, 160, 89, 0.2);
  color: var(--gold-light);
}}
.vision-status.analyzed {{
  background: rgba(39, 174, 96, 0.2);
  color: #abebc6;
}}
.vision-status.failed {{
  background: rgba(192, 57, 43, 0.2);
  color: #f5b7b1;
}}
.vision-status.not_available {{
  background: rgba(243, 156, 18, 0.2);
  color: #f9e79f;
}}

/* Backend status indicator */
.backend-status {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  background: rgba(253, 251, 247, 0.04);
  border: 1px solid rgba(197, 160, 89, 0.15);
  color: var(--gold);
}}
.backend-status .dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green-safe);
}}
.backend-status .dot.off {{
  background: var(--amber-warn);
}}
.vision-body {{
  font-size: 0.95rem;
  color: rgba(253, 251, 247, 0.85);
  line-height: 1.5;
}}
.vision-privacy {{
  font-size: 0.75rem;
  color: #888;
  margin-top: 0.6rem;
}}

/* Forms */
textarea, input {{
  background: rgba(253, 251, 247, 0.04) !important;
  color: var(--parchment) !important;
  border: 1px solid rgba(197, 160, 89, 0.18) !important;
  border-radius: 10px !important;
  font-size: 0.95rem !important;
}}
textarea::placeholder {{
  color: rgba(253, 251, 247, 0.3) !important;
}}

button.primary {{
  background: linear-gradient(135deg, var(--gold), #b08d4b) !important;
  color: var(--wood-dark) !important;
  font-weight: 700 !important;
  border: none !important;
  border-radius: 10px !important;
  letter-spacing: 0.5px !important;
  transition: all 0.2s ease !important;
}}
button.primary:hover {{
  filter: brightness(1.1) !important;
  box-shadow: 0 4px 18px rgba(197, 160, 89, 0.28) !important;
}}

.example-btn {{
  background: rgba(253, 251, 247, 0.03) !important;
  color: var(--gold-light) !important;
  border: 1px solid rgba(197, 160, 89, 0.2) !important;
  border-radius: 8px !important;
  font-size: 0.8rem !important;
}}
.example-btn:hover {{
  background: rgba(197, 160, 89, 0.1) !important;
  border-color: var(--gold) !important;
}}

.section-label {{
  font-family: 'Playfair Display', serif;
  color: var(--gold-light);
  font-size: 1.05rem;
  margin-bottom: 0.6rem;
  letter-spacing: 0.5px;
}}

.gr-accordion {{
  background: rgba(253, 251, 247, 0.015) !important;
  border: 1px solid rgba(197, 160, 89, 0.08) !important;
  border-radius: 12px !important;
}}

footer {{ display: none !important; }}

{_build_role_css(ROLE_SVGS, ROLE_SUBTITLES)}
"""

# ---------------------------------------------------------------------------
# Backend instance (heuristic by default; smollm3 when SCAM_COURT_BACKEND=smollm3)
# ---------------------------------------------------------------------------
backend = get_backend()

# ---------------------------------------------------------------------------
# Example messages
# ---------------------------------------------------------------------------
EXAMPLES = [
    {
        "label": "Family Impersonation",
        "text": (
            "Hi honey, it's Mom. I got a new phone and lost all my contacts. "
            "Can you send me $500 via Zelle? I'm stuck at the grocery store and my card isn't working. "
            "Please don't tell Dad, it's embarrassing. Send it to this number quickly!"
        ),
    },
    {
        "label": "Fake Bank Alert",
        "text": (
            "ALERT: Your Chase account has been suspended due to suspicious login activity. "
            "Verify your identity immediately at http://chase-verify-now.tk/login to avoid permanent closure. "
            "Failure to act within 24 hours will result in loss of all funds."
        ),
    },
    {
        "label": "OTP / Code Theft",
        "text": (
            "Hey, this is Mike from IT support. We're doing a security audit and I need you to forward "
            "the 6-digit code I just sent to your phone. It's urgent — the CEO's account is compromised "
            "and we need to lock it down now. Please reply with the code ASAP."
        ),
    },
    {
        "label": "Marketplace Deposit Scam",
        "text": (
            "Hi! I'm very interested in buying your couch. I can't pick it up in person because I'm a "
            "marine engineer offshore, but I'll send a courier. Please pay a $150 holding deposit via "
            "Cash App so I know you're serious. My assistant will collect it tomorrow."
        ),
    },
    {
        "label": "Fake Invoice",
        "text": (
            "Invoice #8921-REM is now 7 days overdue. Total due: $4,250.00. "
            "Please remit payment immediately to avoid late fees and service interruption. "
            "Click here to view and pay your invoice: https://invoice-portal.zip/pay?id=8921"
        ),
    },
]

EXAMPLE_BUTTONS = [[ex["label"], ex["text"]] for ex in EXAMPLES]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _risk_color(score: int) -> str:
    if score >= 80:
        return "#c0392b"
    if score >= 50:
        return "#d35400"
    if score >= 20:
        return "#f39c12"
    return "#27ae60"


def _verdict_label(score: int) -> str:
    if score >= 80:
        return "SCAM"
    if score >= 50:
        return "SUSPICIOUS"
    if score >= 20:
        return "CAUTION"
    return "LIKELY SAFE"


def _render_gauge(score: int, verdict: str, rationale: str) -> str:
    r = 58
    c = 2 * 3.14159 * r
    offset = c * (1 - score / 100)
    color = _risk_color(score)
    return f"""
    <div class="gauge-container">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="{r}" fill="none" stroke="rgba(197,160,89,0.10)" stroke-width="7"/>
        <circle cx="70" cy="70" r="{r}" fill="none" stroke="{color}" stroke-width="7"
          stroke-dasharray="{c:.2f}" stroke-dashoffset="{offset:.2f}"
          stroke-linecap="round" transform="rotate(-90 70 70)"/>
        <text x="70" y="68" text-anchor="middle" fill="#e8d5a3" font-size="34" font-weight="700"
          font-family="'Playfair Display', serif">{score}</text>
        <text x="70" y="88" text-anchor="middle" fill="#c5a059" font-size="9"
          font-family="'Inter', sans-serif" letter-spacing="2">RISK SCORE</text>
      </svg>
      <div class="gauge-verdict">{html.escape(verdict)}</div>
      <div class="gauge-rationale">{html.escape(rationale)}</div>
    </div>
    """


def _render_indicator(active_role: str | None) -> str:
    roles = ["detective", "prosecutor", "defender", "judge", "clerk"]
    bars = []
    for role in roles:
        cls = "on" if role == active_role else ""
        bars.append(f'<div class="active-bar {cls}"></div>')
    return f'<div class="active-indicator">{ "".join(bars) }</div>'


def _render_role(role: str, report_dict: dict | None) -> str:
    if not report_dict:
        return '<div class="role-panel"><div class="role-body"><em>Waiting for evidence…</em></div></div>'

    titles = {
        "detective": "Detective Evidence Board",
        "prosecutor": "Prosecutor Argument",
        "defender": "Defender Argument",
        "judge": "Judge Verdict",
        "clerk": "Safety Clerk",
    }
    subtitles = {
        "detective": "Sharp, observant, factual",
        "prosecutor": "Persuasive, dramatic, logical",
        "defender": "Skeptical, fair, cautious",
        "judge": "Authoritative, measured, decisive",
        "clerk": "Helpful, calm, actionable",
    }

    if role == "detective":
        evidence = report_dict.get("detective_report", {}).get("evidence", [])
        if not evidence:
            content = "<p><em>No red flags detected.</em></p>"
        else:
            items = "".join(f"<li>{html.escape(e)}</li>" for e in evidence)
            content = f"<ul>{items}</ul>"
    elif role == "prosecutor":
        text = report_dict.get("prosecutor_argument", "").replace("\n", "<br>")
        content = f"<p>{text}</p>"
    elif role == "defender":
        text = report_dict.get("defender_argument", "").replace("\n", "<br>")
        content = f"<p>{text}</p>"
    elif role == "judge":
        verdict = html.escape(report_dict.get("judge_summary", {}).get("verdict", ""))
        rationale = report_dict.get("judge_summary", {}).get("rationale", "").replace("\n", "<br>")
        content = f"<p><strong>{verdict}</strong></p><p>{rationale}</p>"
    else:  # clerk
        reply = html.escape(report_dict.get("safety_reply", ""))
        steps = report_dict.get("next_steps", [])
        content = f"<p><strong>Safe Reply</strong></p><p>{reply}</p>"
        if steps:
            items = "".join(f"<li>{html.escape(s)}</li>" for s in steps)
            content += f"<p><strong>Next Steps</strong></p><ol>{items}</ol>"

    svg = ROLE_SVGS.get(role, "")
    return f"""
    <div class="role-panel">
      <div class="role-header">
        <div class="role-avatar">{svg}</div>
        <div class="role-meta">
          <div class="role-title">{titles.get(role, role)}</div>
          <div class="role-subtitle">{subtitles.get(role, "")}</div>
        </div>
      </div>
      <div class="role-body">{content}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Shield Mode renderers
# ---------------------------------------------------------------------------
def _shield_card_class(verdict: str) -> str:
    v = verdict.upper()
    if "STOP" in v:
        return "stop"
    if "VERIFY" in v:
        return "verify"
    return "safe"


def _shield_icon(verdict: str) -> str:
    v = verdict.upper()
    if "STOP" in v:
        return "&#128721;"  # stop sign
    if "VERIFY" in v:
        return "&#9888;"  # warning
    return "&#10003;"  # check


def render_shield(report_dict: dict | None) -> str:
    if not report_dict:
        return '<div class="shield-empty">Paste a message and tap <strong>Analyze</strong> to see your Shield verdict.</div>'
    verdict = report_dict.get("shield_verdict", "VERIFY FIRST")
    action = report_dict.get("immediate_action", "Pause and verify before acting.")
    script = report_dict.get("trusted_contact_script", "")
    score = report_dict.get("risk_score", 0)
    cls = _shield_card_class(verdict)
    icon = _shield_icon(verdict)
    court_hint = ""
    if score >= 35:
        court_hint = (
            '<div style="margin-top:1rem;font-size:0.9rem;opacity:0.75;">'
            'Switch to the <strong>Court</strong> tab for a full explanation of why this message is risky.</div>'
        )
    return f"""
    <div class="shield-card {cls}">
      <div class="shield-verdict">{icon} {html.escape(verdict, quote=False)}</div>
      <div class="shield-score">Risk score: {score}/100</div>
      <div class="shield-action">{html.escape(action, quote=False)}</div>
      <div class="shield-script">
        <div class="shield-script-label">What to tell a trusted contact</div>
        {html.escape(script, quote=False)}
      </div>
      {court_hint}
    </div>
    """


# ---------------------------------------------------------------------------
# Suspicious Call Quick Check
# ---------------------------------------------------------------------------
def _call_trusted_script(score: int, tags: list[str]) -> str:
    if "asks_code" in tags:
        return "I am on a call where someone is asking for my password or a code. I hung up. Can you help me change my account passwords just in case?"
    if "asks_money" in tags and "claims_family_new_number" in tags:
        return "Someone is pretending to be family and asking for money on the phone. I hung up. Can you help me reach [name] on the number we already have?"
    if "asks_money" in tags:
        return "I just hung up on a call asking me to send money or buy gift cards. Please remind me not to send anything until I verify through an official channel."
    if "claims_family_new_number" in tags:
        return "Someone called claiming to be family from a new number. I hung up. Can you help me reach them on the number we already know?"
    if score >= 70:
        return "I just hung up on a suspicious phone call. The person was pressuring me. Can you sit with me while I report it?"
    if score >= 35:
        return "I received a suspicious call and I am not sure it is real. I told them I would call back. Can you help me verify the number?"
    return "I received a phone call that seemed okay, but I wanted to be cautious. No action needed right now."


def _clean_visual_risk_clues(raw_clues: list[str], extracted_text: str) -> list[str]:
    """Remove placeholder tokens and derive fallback clues from text."""
    placeholder_tokens = {"list", "of", "visual", "red", "flags", "item", "none", "n/a", "unknown"}
    cleaned: list[str] = []
    for clue in raw_clues:
        clue_lower = clue.lower().strip()
        if clue_lower in placeholder_tokens or len(clue_lower) < 3:
            continue
        cleaned.append(clue.strip())

    # Derive fallback clues from extracted text heuristics
    if extracted_text:
        lowered = extracted_text.lower()
        fallback_map = {
            "suspicious link detected": bool(re.search(r"https?://", lowered)),
            "package delivery action request": any(k in lowered for k in ("fedex", "dhl", "usps", "ups", "package", "parcel", "delivery")),
            "money or payment request": any(k in lowered for k in ("payment", "pay", "wire", "gift card", "crypto", "zelle", "venmo")),
            "credential or code request": any(k in lowered for k in ("otp", "code", "password", "pin", "verify your identity")),
            "urgency or deadline": any(k in lowered for k in ("urgent", "immediately", "24 hours", "deadline", "act now")),
            "bank or government impersonation": any(k in lowered for k in ("bank", "irs", "social security", "government", "stimulus")),
            "marketplace off-platform payment": any(k in lowered for k in ("holding deposit", "security deposit", "off platform", "outside the app")),
        }
        for label, triggered in fallback_map.items():
            if triggered and label not in [c.lower() for c in cleaned]:
                cleaned.append(label)

    return cleaned


def analyze_call_checklist(
    asks_money: bool,
    asks_code: bool,
    claims_family_new_number: bool,
    urgency: bool,
    secrecy: bool,
) -> str:
    result = CourtroomEngine.evaluate_call_checklist(
        asks_money=asks_money,
        asks_code=asks_code,
        claims_family_new_number=claims_family_new_number,
        creates_urgency_or_fear=urgency,
        asks_secrecy=secrecy,
    )
    score = result["score"]
    verdict = result["verdict"]
    action = result["action"]
    tags = result["tags"]

    # Override high-risk action with stronger wording
    if score >= 70:
        action = "Hang up now and verify independently using a trusted number."

    cls = _shield_card_class(verdict)
    icon = _shield_icon(verdict)
    script = _call_trusted_script(score, tags)

    tags_html = ""
    if tags:
        tags_html = (
            "<div style='margin-top:0.8rem;font-size:0.85rem;opacity:0.8;'>"
            "Warning signs: " + ", ".join(html.escape(t.replace("_", " "), quote=False) for t in tags)
            + "</div>"
        )
    return f"""
    <div class="shield-card {cls}">
      <div class="shield-verdict">{icon} {html.escape(verdict, quote=False)}</div>
      <div class="shield-score">Quick risk score: {score}/100</div>
      <div class="shield-action">{html.escape(action, quote=False)}</div>
      <div class="shield-script">
        <div class="shield-script-label">What to tell a trusted contact</div>
        {html.escape(script, quote=False)}
      </div>
      {tags_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Companion Preview renderers
# ---------------------------------------------------------------------------
def _truncate(text: str, length: int = 280) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"


def _companion_badge(report_dict: dict | None) -> str:
    if not report_dict:
        return ""
    verdict = report_dict.get("shield_verdict", "VERIFY FIRST")
    cls = _shield_card_class(verdict)
    return f'<span class="companion-shield {cls}">{html.escape(verdict)}</span>'


def render_companion_whatsapp(report_dict: dict | None) -> str:
    if not report_dict:
        return '<div class="shield-empty">Analyze a message first to preview the WhatsApp companion card.</div>'
    text = report_dict.get("input_text", "")
    script = report_dict.get("trusted_contact_script", "")
    action = report_dict.get("immediate_action", "")
    score = report_dict.get("risk_score", 0)
    badge = _companion_badge(report_dict)
    disclaimer = '<div style="font-size:0.7rem;color:#888;margin-top:0.6rem;text-align:center;">Prototype simulation — not a real extension</div>'
    return f"""
    <div class="companion-phone">
      <div class="companion-header">&#128172; WhatsApp preview</div>
      <div class="companion-body">
        <div class="companion-bubble-in">{html.escape(_truncate(text), quote=False)}</div>
        <div class="companion-bubble-out">{html.escape(_truncate(script), quote=False)}</div>
        {badge}
        <div style="margin-top:0.8rem;font-size:0.85rem;color:#aaa;">
          <strong>Action:</strong> {html.escape(action, quote=False)}
        </div>
        <div style="margin-top:0.4rem;font-size:0.8rem;color:#888;">
          Switch to the <strong>Court</strong> tab for the full explanation (score: {score})
        </div>
        {disclaimer}
      </div>
    </div>
    """


def render_companion_sms(report_dict: dict | None) -> str:
    if not report_dict:
        return '<div class="shield-empty">Analyze a message first to preview the SMS companion card.</div>'
    text = report_dict.get("input_text", "")
    script = report_dict.get("trusted_contact_script", "")
    action = report_dict.get("immediate_action", "")
    score = report_dict.get("risk_score", 0)
    badge = _companion_badge(report_dict)
    disclaimer = '<div style="font-size:0.7rem;color:#888;margin-top:0.6rem;text-align:center;">Prototype simulation — not a real extension</div>'
    return f"""
    <div class="companion-phone">
      <div class="companion-header">&#9993; SMS preview</div>
      <div class="companion-body">
        <div class="companion-sms">
          <div class="companion-sms-label">Unknown sender</div>
          {html.escape(_truncate(text), quote=False)}
          <div class="companion-meta"><span>Now</span></div>
        </div>
        <div class="companion-sms">
          <div class="companion-sms-label">Your safe reply</div>
          {html.escape(_truncate(script), quote=False)}
          <div class="companion-meta"><span>Draft</span></div>
        </div>
        {badge}
        <div style="margin-top:0.8rem;font-size:0.85rem;color:#aaa;">
          <strong>Action:</strong> {html.escape(action, quote=False)}
        </div>
        <div style="margin-top:0.4rem;font-size:0.8rem;color:#888;">
          Switch to the <strong>Court</strong> tab for the full explanation (score: {score})
        </div>
        {disclaimer}
      </div>
    </div>
    """


def render_companion_marketplace(report_dict: dict | None) -> str:
    if not report_dict:
        return '<div class="shield-empty">Analyze a message first to preview the Marketplace companion card.</div>'
    text = report_dict.get("input_text", "")
    script = report_dict.get("trusted_contact_script", "")
    action = report_dict.get("immediate_action", "")
    score = report_dict.get("risk_score", 0)
    badge = _companion_badge(report_dict)
    disclaimer = '<div style="font-size:0.7rem;color:#888;margin-top:0.6rem;text-align:center;">Prototype simulation — not a real extension</div>'
    return f"""
    <div class="companion-phone">
      <div class="companion-header">&#128235; Marketplace preview</div>
      <div class="companion-body">
        <div class="companion-sms">
          <div class="companion-sms-label">Buyer message</div>
          {html.escape(_truncate(text), quote=False)}
          <div class="companion-meta"><span>Platform: Marketplace</span></div>
        </div>
        <div class="companion-sms">
          <div class="companion-sms-label">Recommended response</div>
          {html.escape(_truncate(script), quote=False)}
          <div class="companion-meta"><span>Draft reply</span></div>
        </div>
        {badge}
        <div style="margin-top:0.8rem;font-size:0.85rem;color:#aaa;">
          <strong>Action:</strong> {html.escape(action, quote=False)}
        </div>
        <div style="margin-top:0.4rem;font-size:0.8rem;color:#888;">
          Switch to the <strong>Court</strong> tab for the full explanation (score: {score})
        </div>
        {disclaimer}
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Vision Witness renderer
# ---------------------------------------------------------------------------
def render_vision_witness(report_dict: dict | None) -> str:
    if not report_dict:
        return ""
    if not report_dict.get("image_evidence_present"):
        return ""
    status = report_dict.get("vision_status", "inactive")
    backend = report_dict.get("vision_backend", "none")
    model = report_dict.get("vision_model") or backend
    summary = report_dict.get("vision_summary") or ""
    extracted = report_dict.get("extracted_text") or ""
    screenshot_type = report_dict.get("screenshot_type") or ""
    clues = report_dict.get("screenshot_risk_clues", [])
    confidence = report_dict.get("vision_confidence", 0.0)
    error = report_dict.get("vision_error") or ""

    status_label = {
        "inactive": "Inactive — paste text for analysis",
        "loaded": "Loaded — vision backend ready",
        "analyzed": "Analyzed",
        "failed": "Failed — verify independently",
        "not_available": "Not Available — install transformers + torch",
    }.get(status, status)

    body_parts = []
    if screenshot_type:
        body_parts.append(f'<p><strong>Type:</strong> {html.escape(screenshot_type.capitalize(), quote=False)}</p>')
    if summary:
        body_parts.append(f"<p>{html.escape(summary, quote=False)}</p>")
    if extracted:
        body_parts.append(f"<p><strong>Extracted text:</strong> {html.escape(extracted, quote=False)}</p>")
    if clues:
        items = "".join(f"<li>{html.escape(c, quote=False)}</li>" for c in clues)
        body_parts.append(f'<p><strong>Visual clues:</strong></p><ul>{items}</ul>')
    if error and status in ("failed", "not_available"):
        body_parts.append(f'<p style="opacity:0.7;font-size:0.85rem;">Error: {html.escape(error, quote=False)}</p>')

    body_html = "".join(body_parts) if body_parts else "<p>Screenshot received. Vision analysis is not active yet. Paste the message text for full analysis.</p>"

    confidence_badge = ""
    if confidence > 0:
        confidence_badge = f'<span style="margin-left:0.5rem;font-size:0.7rem;opacity:0.7;">Confidence: {confidence:.0%}</span>'

    return f"""
    <div class="vision-card">
      <div class="vision-header">&#128248; Vision Witness</div>
      <span class="vision-status {status}">{html.escape(status_label, quote=False)}</span>{confidence_badge}
      <div class="vision-body">{body_html}</div>
      <div class="vision-privacy">Model: {html.escape(model, quote=False)} · Screenshot processed only for this session.</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Analysis function
# ---------------------------------------------------------------------------
def analyze_message(message: str, image_path: str | None = None) -> tuple[str, dict, str, str, str, str, str, str]:
    has_image = image_path is not None and image_path != ""
    has_text = message and message.strip()

    if not has_text and not has_image:
        empty_gauge = _render_gauge(0, "WAITING", "Submit evidence to begin the trial.")
        empty_shield = render_shield(None)
        empty_vision = render_vision_witness(None)
        empty_companion = (
            render_companion_whatsapp(None),
            render_companion_sms(None),
            render_companion_marketplace(None),
        )
        return empty_gauge, {}, "", empty_shield, empty_vision, *empty_companion

    # Vision backend handling
    vision_backend = get_vision_backend()
    vision_result: dict[str, Any] | None = None
    if has_image:
        vision_result = vision_backend.analyze_image(image_path, context_text=message or None)

    # Determine what text to analyze
    text_for_analysis = message or ""
    extracted_text = ""
    input_sources: list[str] = []
    if has_text:
        input_sources.append("pasted_text")
    if vision_result:
        extracted_text = vision_result.get("extracted_text") or ""
        recommended = vision_result.get("recommended_text_for_analysis") or ""
        if recommended:
            extracted_text = recommended
        if extracted_text:
            input_sources.append("vision_extracted_text")

    # Combine user text + extracted text if both present
    if has_text and extracted_text:
        text_for_analysis = f"[User text]: {message.strip()}\n[From screenshot]: {extracted_text}"
    elif extracted_text:
        text_for_analysis = extracted_text

    # Run text analysis on the effective input
    report = backend.analyze(text_for_analysis)

    # Override vision fields and fusion tracking on the report
    if has_image and vision_result:
        v_status = vision_result.get("vision_status", "inactive")
        v_confidence = float(vision_result.get("vision_confidence", 0.0))

        # SAFETY RULE: if vision failed or is inactive, force at least VERIFY FIRST
        if v_status not in ("analyzed", "loaded"):
            if report.risk_score < 35:
                report = dataclasses.replace(
                    report,
                    risk_score=35,
                    risk_level="medium",
                    verdict="VERIFY FIRST",
                    shield_verdict="VERIFY FIRST",
                    immediate_action="Screenshot uploaded but vision analysis is unavailable. Do not act on this message. Verify through a trusted, independent channel.",
                    trusted_contact_script="I received a suspicious screenshot but the vision tool could not read it. I need help verifying this message before I do anything.",
                    recommended_action="verify_independently",
                )

        # Clean visual risk clues: remove placeholder tokens
        raw_clues = vision_result.get("screenshot_risk_clues", [])
        cleaned_clues = _clean_visual_risk_clues(raw_clues, extracted_text)

        report = dataclasses.replace(
            report,
            evidence_source="text_and_screenshot" if has_text else "screenshot",
            image_evidence_present=True,
            vision_backend=vision_backend.backend_name,
            vision_model=vision_result.get("vision_model"),
            vision_status=v_status,
            vision_summary=vision_result.get("vision_summary"),
            extracted_text=vision_result.get("extracted_text"),
            screenshot_type=vision_result.get("screenshot_type"),
            screenshot_risk_clues=cleaned_clues,
            recommended_text_for_analysis=vision_result.get("recommended_text_for_analysis"),
            vision_confidence=v_confidence,
            vision_error=vision_result.get("vision_error"),
            effective_input_text=text_for_analysis,
            input_sources=input_sources,
            analysis_used_vision_text=bool(extracted_text),
        )
    else:
        # Text-only analysis
        report = dataclasses.replace(
            report,
            effective_input_text=text_for_analysis,
            input_sources=input_sources,
            analysis_used_vision_text=False,
        )

    gauge = _render_gauge(report.risk_score, report.judge_verdict, report.judge_rationale)
    report_dict = report.to_dict()
    json_export = report.to_json()
    shield = render_shield(report_dict)
    vision_html = render_vision_witness(report_dict)
    whatsapp = render_companion_whatsapp(report_dict)
    sms = render_companion_sms(report_dict)
    marketplace = render_companion_marketplace(report_dict)
    return gauge, report_dict, json_export, shield, vision_html, whatsapp, sms, marketplace


# ---------------------------------------------------------------------------
# Random example loader
# ---------------------------------------------------------------------------
def load_random_example() -> str:
    return random.choice(EXAMPLES)["text"]


# ---------------------------------------------------------------------------
# Role switching factory
# ---------------------------------------------------------------------------
def _make_switch(role: str):
    def _switch(report: dict | None) -> tuple[str, str]:
        return _render_indicator(role), _render_role(role, report)
    return _switch


def _show_detective(report: dict | None) -> tuple[str, str]:
    return _render_indicator("detective"), _render_role("detective", report)


def _render_backend_status() -> str:
    """Render a small backend status indicator for the header."""
    import os
    text_backend = getattr(backend, "model_backend", "heuristic_v1")
    vision = get_vision_backend()
    vision_name = vision.backend_name
    vision_dot = "off" if vision_name == "none" else ""
    hf_home = os.getenv("HF_HOME", "~/.cache/huggingface")
    return f"""
    <div style="text-align:center;margin-bottom:1rem;">
      <span class="backend-status">Text: {text_backend}</span>
      <span class="backend-status">Vision: {vision_name} <span class="dot {vision_dot}"></span></span>
      <span class="backend-status">Model: {get_vision_model_id()}</span>
      <span class="backend-status">Cache: {hf_home}</span>
    </div>
    """


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Scam Court AI") as demo:
        gr.HTML(
            """
            <div id="court-header">
                <h1>Scam Court AI</h1>
                <p>3-Second Scam Shield + AI Courtroom Explanation for the people you protect.</p>
            </div>
            """
        )
        gr.HTML(_render_backend_status())

        report_state = gr.State(None)

        with gr.Tabs(elem_classes=["mode-tabs"]):
            # ── Shield Mode ──
            with gr.Tab("Shield"):
                gr.Markdown('<em style="opacity:0.65;font-size:0.85rem;">For suspicious messages or call summaries. Get a 3-second safety verdict.</em>')
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel"]):
                        gr.Markdown('<div class="section-label">Paste a suspicious message</div>')
                        shield_input = gr.Textbox(
                            label="",
                            placeholder="WhatsApp, SMS, email, or screenshot text…",
                            lines=10,
                            max_lines=18,
                            show_label=False,
                        )
                        gr.Markdown(
                            '<div class="section-label" style="margin-top:1rem;">Or upload a screenshot</div>'
                        )
                        shield_image = gr.Image(
                            label="",
                            type="filepath",
                            sources=["upload"],
                            interactive=True,
                            show_label=False,
                        )
                        gr.Markdown(
                            '<em style="opacity:0.55;font-size:0.75rem;">PNG, JPG, JPEG · WhatsApp, SMS, email, marketplace, or fake invoice screenshot</em>'
                        )
                        with gr.Row():
                            shield_submit = gr.Button("Analyze", variant="primary")
                            shield_random = gr.Button("Random Example")
                            shield_clear = gr.Button("Clear")
                        gr.Markdown('<div class="section-label" style="margin-top:1.2rem;">Quick Load</div>')
                        shield_example_btns = []
                        for label, text in EXAMPLE_BUTTONS:
                            btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                            shield_example_btns.append((btn, text))

                    with gr.Column(scale=2):
                        shield_output = gr.HTML()
                        shield_vision = gr.HTML()

            # ── Court Mode ──
            with gr.Tab("Court"):
                gr.Markdown('<em style="opacity:0.65;font-size:0.85rem;">Full AI courtroom explanation. See Detective, Prosecutor, Defender, Judge, and Clerk.</em>')
                with gr.Row():
                    # Left Column
                    with gr.Column(scale=1, elem_classes=["input-panel"]):
                        gr.Markdown('<div class="section-label">Submit Evidence</div>')
                        court_input = gr.Textbox(
                            label="Paste the suspicious message",
                            placeholder="Paste a WhatsApp message, SMS, email, or screenshot text here…",
                            lines=10,
                            max_lines=18,
                            show_label=False,
                        )
                        gr.Markdown(
                            '<div class="section-label" style="margin-top:1rem;">Or upload a screenshot</div>'
                        )
                        court_image = gr.Image(
                            label="",
                            type="filepath",
                            sources=["upload"],
                            interactive=True,
                            show_label=False,
                        )
                        gr.Markdown(
                            '<em style="opacity:0.55;font-size:0.75rem;">PNG, JPG, JPEG · WhatsApp, SMS, email, marketplace, or fake invoice screenshot</em>'
                        )
                        with gr.Row():
                            court_submit = gr.Button("Bring to Court", variant="primary")
                            court_random = gr.Button("Random Example")
                            court_clear = gr.Button("Clear")

                        gr.Markdown('<div class="section-label" style="margin-top:1.2rem;">Quick Load</div>')
                        court_example_btns = []
                        for label, text in EXAMPLE_BUTTONS:
                            btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                            court_example_btns.append((btn, text))

                    # Right Column
                    with gr.Column(scale=2):
                        risk_gauge = gr.HTML()
                        court_vision = gr.HTML()

                        gr.Markdown('<div class="section-label">Court Members</div>')
                        with gr.Row(elem_classes=["role-selector"]):
                            btn_detective = gr.Button("Detective", elem_classes=["role-btn", "role-btn-detective"])
                            btn_prosecutor = gr.Button("Prosecutor", elem_classes=["role-btn", "role-btn-prosecutor"])
                            btn_defender = gr.Button("Defender", elem_classes=["role-btn", "role-btn-defender"])
                            btn_judge = gr.Button("Judge", elem_classes=["role-btn", "role-btn-judge"])
                            btn_clerk = gr.Button("Clerk", elem_classes=["role-btn", "role-btn-clerk"])

                        active_indicator = gr.HTML(_render_indicator(None))
                        role_display = gr.HTML()

                        with gr.Accordion("Export Report JSON", open=False):
                            json_out = gr.Code(language="json", label="Report JSON")

            # ── Suspicious Call Quick Check ──
            with gr.Tab("Suspicious Call"):
                gr.Markdown('<em style="opacity:0.65;font-size:0.85rem;">For active phone calls. Check what is happening right now.</em>')
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel", "call-check"]):
                        gr.Markdown('<div class="section-label">Quick phone-call check</div>')
                        gr.Markdown("Check every box that applies to the call you or a loved one is on.")
                        chk_money = gr.Checkbox(label="They are asking for money, gift cards, or crypto")
                        chk_code = gr.Checkbox(label="They are asking for a code, password, or PIN")
                        chk_family = gr.Checkbox(label="They claim to be family using a new number")
                        chk_urgency = gr.Checkbox(label="They create urgency, fear, or a deadline")
                        chk_secrecy = gr.Checkbox(label="They ask you to keep the call secret")
                        call_submit = gr.Button("Check the Call", variant="primary")
                        call_clear = gr.Button("Reset")
                    with gr.Column(scale=2):
                        call_output = gr.HTML()

            # ── Companion Preview ──
            with gr.Tab("Companion Preview"):
                gr.Markdown('<em style="opacity:0.65;font-size:0.85rem;">Simulation of future WhatsApp/SMS/Marketplace integration.</em>')
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel"]):
                        gr.Markdown('<div class="section-label">Paste a message to preview</div>')
                        companion_input = gr.Textbox(
                            label="",
                            placeholder="WhatsApp, SMS, email, or marketplace message…",
                            lines=10,
                            max_lines=18,
                            show_label=False,
                        )
                        with gr.Row():
                            companion_submit = gr.Button("Analyze Selected Message", variant="primary")
                            companion_random = gr.Button("Random Example")
                            companion_clear = gr.Button("Clear")
                        gr.Markdown('<div class="section-label" style="margin-top:1.2rem;">Quick Load</div>')
                        companion_example_btns = []
                        for label, text in EXAMPLE_BUTTONS:
                            btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                            companion_example_btns.append((btn, text))

                    with gr.Column(scale=2):
                        companion_vision = gr.HTML()
                        with gr.Tabs():
                            with gr.Tab("WhatsApp"):
                                companion_whatsapp = gr.HTML()
                            with gr.Tab("SMS"):
                                companion_sms = gr.HTML()
                            with gr.Tab("Marketplace"):
                                companion_marketplace = gr.HTML()

        # ── Shared events ──
        # Analyze from Shield tab
        shield_submit.click(
            fn=analyze_message,
            inputs=[shield_input, shield_image],
            outputs=[risk_gauge, report_state, json_out, shield_output, shield_vision, companion_whatsapp, companion_sms, companion_marketplace],
        ).then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        # Analyze from Court tab
        court_submit.click(
            fn=analyze_message,
            inputs=[court_input, court_image],
            outputs=[risk_gauge, report_state, json_out, shield_output, court_vision, companion_whatsapp, companion_sms, companion_marketplace],
        ).then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        # Analyze from Companion tab
        companion_submit.click(
            fn=analyze_message,
            inputs=[companion_input, gr.State(None)],
            outputs=[risk_gauge, report_state, json_out, shield_output, companion_vision, companion_whatsapp, companion_sms, companion_marketplace],
        ).then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        # Role switching
        btn_detective.click(fn=_make_switch("detective"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_prosecutor.click(fn=_make_switch("prosecutor"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_defender.click(fn=_make_switch("defender"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_judge.click(fn=_make_switch("judge"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_clerk.click(fn=_make_switch("clerk"), inputs=report_state, outputs=[active_indicator, role_display])

        # Suspicious Call events
        call_submit.click(
            fn=analyze_call_checklist,
            inputs=[chk_money, chk_code, chk_family, chk_urgency, chk_secrecy],
            outputs=call_output,
        )
        call_clear.click(
            fn=lambda: (False, False, False, False, False, ""),
            outputs=[chk_money, chk_code, chk_family, chk_urgency, chk_secrecy, call_output],
        )

        # Examples
        shield_random.click(fn=load_random_example, outputs=shield_input)
        court_random.click(fn=load_random_example, outputs=court_input)
        companion_random.click(fn=load_random_example, outputs=companion_input)
        for btn, text in shield_example_btns:
            btn.click(fn=lambda t=text: t, outputs=shield_input)
        for btn, text in court_example_btns:
            btn.click(fn=lambda t=text: t, outputs=court_input)
        for btn, text in companion_example_btns:
            btn.click(fn=lambda t=text: t, outputs=companion_input)

        # Clear buttons — reset all shared state
        def _clear_all():
            return (
                None, None, None,  # images
                "", "", "",  # texts
                _render_gauge(0, "WAITING", "Submit evidence to begin the trial."),
                None,
                "",
                _render_indicator(None),
                "",
                render_shield(None),
                "", "", "",  # vision outputs
                render_companion_whatsapp(None),
                render_companion_sms(None),
                render_companion_marketplace(None),
            )

        shield_clear.click(
            fn=_clear_all,
            outputs=[
                shield_image, court_image, gr.State(None),
                shield_input, court_input, companion_input,
                risk_gauge, report_state, json_out,
                active_indicator, role_display,
                shield_output, shield_vision, court_vision, companion_vision,
                companion_whatsapp, companion_sms, companion_marketplace,
            ],
        )
        court_clear.click(
            fn=_clear_all,
            outputs=[
                shield_image, court_image, gr.State(None),
                shield_input, court_input, companion_input,
                risk_gauge, report_state, json_out,
                active_indicator, role_display,
                shield_output, shield_vision, court_vision, companion_vision,
                companion_whatsapp, companion_sms, companion_marketplace,
            ],
        )
        companion_clear.click(
            fn=_clear_all,
            outputs=[
                shield_image, court_image, gr.State(None),
                shield_input, court_input, companion_input,
                risk_gauge, report_state, json_out,
                active_indicator, role_display,
                shield_output, shield_vision, court_vision, companion_vision,
                companion_whatsapp, companion_sms, companion_marketplace,
            ],
        )

        gr.Markdown(
            """
            <div style="text-align:center;opacity:0.4;font-size:0.72rem;margin-top:2.2rem;letter-spacing:0.6px;">
            Scam Court AI · Hugging Face Build Small Hackathon · CPU-first · Model-ready
            </div>
            """
        )

    return demo


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    port = int(os.getenv("GRADIO_SERVER_PORT", os.getenv("PORT", "7861")))
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
        favicon_path=None,
        css=COURT_CSS,
    )
