"""Scam Court AI — Premium Gradio courtroom interface.

Run locally:
    python app.py

Deploy to Hugging Face Spaces:
    Push this repo; Spaces will run app.py automatically.
"""

from __future__ import annotations

import html
import pathlib
import random
import urllib.parse

import gradio as gr

from courtroom import CourtroomEngine

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
# Custom CSS — premium dark courtroom aesthetic
# ---------------------------------------------------------------------------
COURT_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

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
# Engine instance
# ---------------------------------------------------------------------------
engine = CourtroomEngine()

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

    court = report_dict.get("court", {})
    if role == "detective":
        evidence = court.get("detective", {}).get("evidence", [])
        if not evidence:
            content = "<p><em>No red flags detected.</em></p>"
        else:
            items = "".join(f"<li>{html.escape(e)}</li>" for e in evidence)
            content = f"<ul>{items}</ul>"
    elif role == "prosecutor":
        text = court.get("prosecutor", {}).get("argument", "").replace("\n", "<br>")
        content = f"<p>{text}</p>"
    elif role == "defender":
        text = court.get("defender", {}).get("argument", "").replace("\n", "<br>")
        content = f"<p>{text}</p>"
    elif role == "judge":
        verdict = html.escape(court.get("judge", {}).get("verdict", ""))
        rationale = court.get("judge", {}).get("rationale", "").replace("\n", "<br>")
        content = f"<p><strong>{verdict}</strong></p><p>{rationale}</p>"
    else:  # clerk
        reply = html.escape(court.get("clerk", {}).get("safe_reply", ""))
        steps = court.get("clerk", {}).get("next_steps", [])
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
# Analysis function
# ---------------------------------------------------------------------------
def analyze_message(message: str) -> tuple[str, dict, str]:
    if not message or not message.strip():
        empty_gauge = _render_gauge(0, "WAITING", "Submit evidence to begin the trial.")
        return empty_gauge, {}, ""

    report = engine.analyze(message)
    gauge = _render_gauge(report.risk_score, report.judge_verdict, report.judge_rationale)
    report_dict = report.to_dict()
    json_export = report.to_json()
    return gauge, report_dict, json_export


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


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Scam Court AI") as demo:
        gr.HTML(
            """
            <div id="court-header">
                <h1>Scam Court AI</h1>
                <p>Put suspicious messages on trial before they hurt someone.</p>
            </div>
            """
        )

        report_state = gr.State(None)

        with gr.Row():
            # ── Left Column ──
            with gr.Column(scale=1, elem_classes=["input-panel"]):
                gr.Markdown('<div class="section-label">Submit Evidence</div>')
                msg_input = gr.Textbox(
                    label="Paste the suspicious message",
                    placeholder="Paste a WhatsApp message, SMS, email, or screenshot text here…",
                    lines=10,
                    max_lines=18,
                    show_label=False,
                )
                with gr.Row():
                    submit_btn = gr.Button("Bring to Court", variant="primary")
                    random_btn = gr.Button("Random Example")
                    clear_btn = gr.Button("Clear")

                gr.Markdown('<div class="section-label" style="margin-top:1.2rem;">Quick Load</div>')
                example_btns = []
                for label, text in EXAMPLE_BUTTONS:
                    btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                    example_btns.append((btn, text))

            # ── Right Column ──
            with gr.Column(scale=2):
                risk_gauge = gr.HTML()

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

        # Events: analyze
        submit_event = submit_btn.click(
            fn=analyze_message,
            inputs=msg_input,
            outputs=[risk_gauge, report_state, json_out],
        )
        submit_event.then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        # Events: role switching
        btn_detective.click(fn=_make_switch("detective"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_prosecutor.click(fn=_make_switch("prosecutor"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_defender.click(fn=_make_switch("defender"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_judge.click(fn=_make_switch("judge"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_clerk.click(fn=_make_switch("clerk"), inputs=report_state, outputs=[active_indicator, role_display])

        # Events: examples
        random_btn.click(fn=load_random_example, outputs=msg_input)
        for btn, text in example_btns:
            btn.click(fn=lambda t=text: t, outputs=msg_input)

        # Events: clear
        clear_btn.click(
            fn=lambda: (
                "",
                _render_gauge(0, "WAITING", "Submit evidence to begin the trial."),
                None,
                "",
                _render_indicator(None),
                "",
            ),
            outputs=[msg_input, risk_gauge, report_state, json_out, active_indicator, role_display],
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
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        favicon_path=None,
        css=COURT_CSS,
    )
