"""Scam Court AI — Gradio courtroom interface.

Run locally:
    python app.py

Deploy to Hugging Face Spaces:
    Push this repo; Spaces will run app.py automatically.
"""

from __future__ import annotations

import json
import random

import gradio as gr

from courtroom import CourtroomEngine
from courtroom.personas import PERSONAS, PERSONA_ORDER

# ---------------------------------------------------------------------------
# Custom CSS — dramatic courtroom aesthetic
# ---------------------------------------------------------------------------
COURT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');

:root {
  --wood-dark: #2c1e14;
  --wood-mid: #4a332a;
  --gold: #c5a059;
  --gold-light: #e8d5a3;
  --red-flag: #c0392b;
  --green-safe: #27ae60;
  --amber-warn: #f39c12;
  --parchment: #fdfbf7;
  --ink: #1a1a1a;
  --slate: #4a4a4a;
}

body {
  font-family: 'Inter', sans-serif;
  background: linear-gradient(135deg, #1a120b 0%, #2c1e14 100%);
  color: var(--parchment);
}

.gradio-container {
  background: transparent !important;
}

#court-header {
  text-align: center;
  padding: 1.5rem 1rem 1rem;
  border-bottom: 3px solid var(--gold);
  margin-bottom: 1.5rem;
}

#court-header h1 {
  font-family: 'Playfair Display', serif;
  font-size: 2.4rem;
  color: var(--gold-light);
  margin: 0;
  letter-spacing: 1px;
}

#court-header p {
  color: var(--gold);
  font-size: 1.05rem;
  margin-top: 0.4rem;
  opacity: 0.9;
}

.court-panel {
  background: rgba(253, 251, 247, 0.06);
  border: 1px solid rgba(197, 160, 89, 0.25);
  border-radius: 12px;
  padding: 1.2rem;
  margin-bottom: 1rem;
  backdrop-filter: blur(6px);
}

.court-panel h3 {
  font-family: 'Playfair Display', serif;
  color: var(--gold-light);
  margin-top: 0;
  margin-bottom: 0.6rem;
  font-size: 1.3rem;
}

.court-panel p, .court-panel li {
  color: var(--parchment);
  line-height: 1.6;
  font-size: 0.95rem;
}

.risk-gauge {
  text-align: center;
  padding: 1rem;
  border-radius: 12px;
  font-family: 'Playfair Display', serif;
  font-size: 2.2rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 1rem;
  transition: background 0.4s ease;
}

.risk-scam   { background: linear-gradient(90deg, #c0392b, #e74c3c); }
.risk-suspicious { background: linear-gradient(90deg, #d35400, #f39c12); }
.risk-caution { background: linear-gradient(90deg, #f39c12, #f1c40f); color: #2c1e14 !important; }
.risk-safe   { background: linear-gradient(90deg, #27ae60, #2ecc71); }

.verdict-badge {
  display: inline-block;
  padding: 0.35rem 1rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  border: 2px solid;
}

.badge-scam { background: rgba(192, 57, 43, 0.15); border-color: var(--red-flag); color: #ff6b6b; }
.badge-suspicious { background: rgba(243, 156, 18, 0.15); border-color: var(--amber-warn); color: #f1c40f; }
.badge-caution { background: rgba(241, 196, 15, 0.15); border-color: #f1c40f; color: #f1c40f; }
.badge-safe { background: rgba(39, 174, 96, 0.15); border-color: var(--green-safe); color: #2ecc71; }

.example-btn {
  background: var(--wood-mid) !important;
  color: var(--gold-light) !important;
  border: 1px solid var(--gold) !important;
}

.example-btn:hover {
  background: var(--gold) !important;
  color: var(--wood-dark) !important;
}

/* Gradio overrides */
button.primary {
  background: linear-gradient(90deg, var(--gold), var(--gold-light)) !important;
  color: var(--wood-dark) !important;
  font-weight: 700 !important;
  border: none !important;
  border-radius: 8px !important;
}

textarea, input {
  background: rgba(253, 251, 247, 0.08) !important;
  color: var(--parchment) !important;
  border: 1px solid rgba(197, 160, 89, 0.3) !important;
  border-radius: 8px !important;
}

textarea::placeholder {
  color: rgba(253, 251, 247, 0.4) !important;
}

footer { display: none !important; }
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
        "label": "🏠 Family Impersonation",
        "text": (
            "Hi honey, it's Mom. I got a new phone and lost all my contacts. "
            "Can you send me $500 via Zelle? I'm stuck at the grocery store and my card isn't working. "
            "Please don't tell Dad, it's embarrassing. Send it to this number quickly!"
        ),
    },
    {
        "label": "🏦 Fake Bank Alert",
        "text": (
            "ALERT: Your Chase account has been suspended due to suspicious login activity. "
            "Verify your identity immediately at http://chase-verify-now.tk/login to avoid permanent closure. "
            "Failure to act within 24 hours will result in loss of all funds."
        ),
    },
    {
        "label": "🔑 OTP / Code Theft",
        "text": (
            "Hey, this is Mike from IT support. We're doing a security audit and I need you to forward "
            "the 6-digit code I just sent to your phone. It's urgent — the CEO's account is compromised "
            "and we need to lock it down now. Please reply with the code ASAP."
        ),
    },
    {
        "label": "🛒 Marketplace Deposit Scam",
        "text": (
            "Hi! I'm very interested in buying your couch. I can't pick it up in person because I'm a "
            "marine engineer offshore, but I'll send a courier. Please pay a $150 holding deposit via "
            "Cash App so I know you're serious. My assistant will collect it tomorrow."
        ),
    },
    {
        "label": "📄 Fake Invoice",
        "text": (
            "Invoice #8921-REM is now 7 days overdue. Total due: $4,250.00. "
            "Please remit payment immediately to avoid late fees and service interruption. "
            "Click here to view and pay your invoice: https://invoice-portal.zip/pay?id=8921"
        ),
    },
]

EXAMPLE_BUTTONS = [[ex["label"], ex["text"]] for ex in EXAMPLES]


def _risk_class(score: int) -> str:
    if score >= 80:
        return "risk-scam"
    if score >= 50:
        return "risk-suspicious"
    if score >= 20:
        return "risk-caution"
    return "risk-safe"


def _badge_class(score: int) -> str:
    if score >= 80:
        return "badge-scam"
    if score >= 50:
        return "badge-suspicious"
    if score >= 20:
        return "badge-caution"
    return "badge-safe"


def _verdict_label(score: int) -> str:
    if score >= 80:
        return "SCAM"
    if score >= 50:
        return "SUSPICIOUS"
    if score >= 20:
        return "CAUTION"
    return "LIKELY SAFE"


# ---------------------------------------------------------------------------
# Analysis function
# ---------------------------------------------------------------------------
def analyze_message(message: str) -> tuple[str, str, str, str, str, str, str, str]:
    if not message or not message.strip():
        empty = "_Waiting for evidence…_"
        return empty, empty, empty, empty, empty, empty, empty, ""

    report = engine.analyze(message)

    # 1. Risk gauge
    gauge_html = (
        f'<div class="risk-gauge {_risk_class(report.risk_score)}">'
        f"Risk Score: {report.risk_score} / 100</div>"
    )

    # 2. Verdict badge
    verdict_html = (
        f'<div style="text-align:center;margin-bottom:1rem;">'
        f'<span class="verdict-badge {_badge_class(report.risk_score)}">'
        f"{_verdict_label(report.risk_score)}"
        f"</span></div>"
    )

    # 3. Detective
    detective_md = "\n".join(f"- {e}" for e in report.detective_evidence) or "_No red flags detected._"

    # 4. Prosecutor
    prosecutor_md = report.prosecutor_argument

    # 5. Defender
    defender_md = report.defender_argument

    # 6. Judge
    judge_md = f"**{report.judge_verdict}**\n\n{report.judge_rationale}"

    # 7. Clerk
    steps_md = "\n".join(f"{i}. {step}" for i, step in enumerate(report.clerk_next_steps, 1))
    clerk_md = f"**Safe Reply:**\n\n{report.clerk_safe_reply}\n\n**Next Steps:**\n\n{steps_md}"

    # 8. JSON export (hidden collapsible)
    json_export = report.to_json()

    return gauge_html, verdict_html, detective_md, prosecutor_md, defender_md, judge_md, clerk_md, json_export


# ---------------------------------------------------------------------------
# Random example loader
# ---------------------------------------------------------------------------
def load_random_example() -> str:
    return random.choice(EXAMPLES)["text"]


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Scam Court AI") as demo:
        gr.HTML(
            """
            <div id="court-header">
                <h1>⚖️ Scam Court AI</h1>
                <p>Put suspicious messages on trial before they hurt someone.</p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Submit Evidence")
                msg_input = gr.Textbox(
                    label="Paste the suspicious message",
                    placeholder=(
                        "Paste a WhatsApp message, SMS, email, or screenshot text here…"
                    ),
                    lines=8,
                    max_lines=16,
                )
                with gr.Row():
                    submit_btn = gr.Button("🧑‍⚖️ Bring to Court", variant="primary")
                    random_btn = gr.Button("🎲 Random Example")
                    clear_btn = gr.Button("🧹 Clear")

                gr.Markdown("#### 📂 Quick Load")
                example_btns = []
                for label, text in EXAMPLE_BUTTONS:
                    btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                    example_btns.append((btn, text))

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Verdict")
                risk_gauge = gr.HTML()
                verdict_badge = gr.HTML()

                with gr.Tabs():
                    with gr.TabItem("🔍 Detective"):
                        detective_out = gr.Markdown()
                    with gr.TabItem("⚖️ Prosecutor"):
                        prosecutor_out = gr.Markdown()
                    with gr.TabItem("🛡️ Defender"):
                        defender_out = gr.Markdown()
                    with gr.TabItem("👨‍⚖️ Judge"):
                        judge_out = gr.Markdown()
                    with gr.TabItem("📋 Safety Clerk"):
                        clerk_out = gr.Markdown()
                    with gr.TabItem("📦 Export JSON"):
                        json_out = gr.Code(language="json", label="Report JSON")

        # Events
        submit_btn.click(
            fn=analyze_message,
            inputs=msg_input,
            outputs=[
                risk_gauge,
                verdict_badge,
                detective_out,
                prosecutor_out,
                defender_out,
                judge_out,
                clerk_out,
                json_out,
            ],
        )

        random_btn.click(fn=load_random_example, outputs=msg_input)

        for btn, text in example_btns:
            btn.click(fn=lambda t=text: t, outputs=msg_input)

        clear_btn.click(
            fn=lambda: ("", "", "", "", "", "", "", "", ""),
            outputs=[
                msg_input,
                risk_gauge,
                verdict_badge,
                detective_out,
                prosecutor_out,
                defender_out,
                judge_out,
                clerk_out,
                json_out,
            ],
        )

        gr.Markdown(
            """
            <div style="text-align:center;opacity:0.6;font-size:0.8rem;margin-top:1.5rem;">
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
