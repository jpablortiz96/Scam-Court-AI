# ⚖️ Scam Court AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/gradio-UI-orange.svg)](https://gradio.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HF Spaces](https://img.shields.io/badge/🤗-Spaces-blue)](https://huggingface.co/spaces)

> **3-Second Scam Shield + AI Courtroom Explanation for the people you protect.**

Scam Court AI is a tiny, multi-agent courtroom that analyzes suspicious WhatsApp messages, SMS, emails, and marketplace chats. It is designed first for **older adults and non-technical family members** who need a clear, calm answer in seconds — then explains the reasoning for anyone who wants to dig deeper.

### Four modes, one safe workflow

- 🛡️ **Shield** — High-contrast 3-second verdict: **STOP / VERIFY FIRST / LOW VISIBLE RISK**
- ⚖️ **Court** — Dramatic interactive trial with Detective, Prosecutor, Defender, Judge, and Safety Clerk
- 📞 **Suspicious Call** — Five-question quick check for live phone scams
- 💬 **Companion Preview** — Simulated WhatsApp, SMS, and Marketplace reply cards you can share

Built for the **Hugging Face Build Small Hackathon** with ≤32B parameters, zero cloud APIs, and CPU-first architecture.

---

## 🚀 Live Demo

**[Try it on Hugging Face Spaces →](YOUR_SPACE_LINK_HERE)**

Or run locally in 30 seconds:

```powershell
# Windows / PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open http://localhost:7861

---

## 🖼️ Screenshot

*(Add screenshot here after first UI run)*

---

## 🏗️ Architecture

```
scam-court-ai/
├── app.py                     # Gradio UI (Shield / Court / Call / Companion tabs)
├── courtroom/
│   ├── __init__.py
│   ├── engine.py              # Heuristic analysis engine + Shield Mode logic
│   ├── backends/              # Pluggable model backends
│   │   ├── base.py
│   │   ├── heuristic.py
│   │   └── smollm3.py
│   ├── config.py              # Backend selection from environment
│   ├── json_parser.py         # Model JSON validation + gap filling
│   ├── prompts.py             # Structured prompts for SmolLM3
│   ├── personas.py            # Persona prompts and metadata
│   └── utils.py               # Sanitization & formatting helpers
├── data/
│   ├── scam_examples_seed.json
│   ├── evaluation_cases.json
│   └── agent_trace_example.json
├── docs/
│   ├── INTEGRATION_CONTRACT.md # Stable v2 JSON schema
│   ├── CHROME_COMPANION_PLAN.md
│   ├── PRIZE_STRATEGY.md
│   ├── FIELD_NOTES.md
│   ├── DEMO_SCRIPT.md
│   └── MODEL_CARD.md
├── requirements.txt
├── .env.example
└── LICENSE
```

### Design Philosophy
- **Modular engine:** Swap heuristic → SmolLM3-3B → MiniCPM-V without touching `app.py`.
- **Privacy-first:** No API keys, no data leaves your machine.
- **Elder-safe UX:** Shield Mode uses large type, high contrast, and one-sentence actions.
- **Dramatic Court UX:** Custom CSS makes the Court tab feel like a courtroom, not a chatbot.

### Backend Modes

Scam Court AI supports two analysis backends, selectable via the `SCAM_COURT_BACKEND` environment variable.

| Mode | Env Value | Speed | Model | Requirements |
|------|-----------|-------|-------|--------------|
| **Heuristic** (default) | `heuristic` | < 50 ms | None | None |
| **SmolLM3** | `smollm3` | 10–30 s | HuggingFaceTB/SmolLM3-3B | `transformers`, `torch` |

**Default behavior:** `SCAM_COURT_BACKEND` is unset or invalid → heuristic runs instantly.

**Switching to SmolLM3:**
```powershell
# Windows
$env:SCAM_COURT_BACKEND = "smollm3"
python app.py
```

```bash
# Linux / macOS
export SCAM_COURT_BACKEND=smollm3
python app.py
```

**Fallback:** If SmolLM3 fails to load or generates invalid output, the app automatically falls back to heuristic and marks `model_backend: "heuristic_fallback_after_smollm3_error"` in the report trace.

**Install model dependencies (only when using SmolLM3):**
```bash
pip install transformers torch
```

---

## 🛡️ Shield Mode Example

**Input:**
> "Hi honey, it's Mom. I got a new phone and lost all my contacts. Can you send me $500 via Zelle? I'm stuck at the grocery store and my card isn't working. Please don't tell Dad, it's embarrassing. Send it to this number quickly!"

**Shield Verdict:**
> **VERIFY FIRST** — Risk Score: 47/100  
> Call your family member directly on a number you already know. Do not reply to this message.

**Tell a trusted contact:**
> "I'm checking this message because someone is pretending to be family. Can you help me reach [name] on the number I already have to confirm they're okay?"

---

## 🧑‍⚖️ Court Mode Example

**Judge Verdict:**
> **SCAM** — Risk Score: 88/100  
> The evidence is overwhelming. The court finds 3 distinct red flags: family impersonation, false urgency, and payment demand. Do not respond or send money.

**Safety Clerk:**
> *Do not reply. Do not click links. Do not send codes or money.* Block the sender and report the message.
> 1. Forward the message to your carrier's spam report number (e.g., 7726).
> 2. Report to the FTC at reportfraud.ftc.gov.
> 3. Warn family members who might receive similar messages.

---

## 🏆 Prize Tracks

| Track | Strategy |
|-------|----------|
| Backyard AI | Mom-friendly Shield UI, safe replies, zero setup |
| OpenBMB | MiniCPM-V-4_5 vision integration (roadmap) |
| Tiny Titan | SmolLM3-3B reasoning core (roadmap) |
| Off-Brand | Courtroom metaphor — not a chatbot |
| Best Demo | Cinematic 60-second video (script ready) |
| Best Agent | Multi-agent traces with structured reasoning |
| Modal | Batch evaluation on GPUs (roadmap) |
| Community Choice | Shareable verdict cards + social campaign |

Full strategy: [`docs/PRIZE_STRATEGY.md`](docs/PRIZE_STRATEGY.md)

---

## 🛠️ Development

### Windows + VS Code + PowerShell

```powershell
# 1. Clone
cd d:\scam-court-ai

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install
pip install -r requirements.txt

# 4. Run
python app.py

# 5. Format & lint (optional)
pip install black ruff
black .
ruff check .
```

### Project Commands

```powershell
# Run tests (when added)
python -m pytest tests/

# Run evaluation
python -m scripts.evaluate

# Export report for an example
python -c "from courtroom import CourtroomEngine; print(CourtroomEngine().analyze(open('data/scam_examples_seed.json').read()))"
```

---

## 📚 Documentation

- [`docs/INTEGRATION_CONTRACT.md`](docs/INTEGRATION_CONTRACT.md) — Stable JSON schema v2.1 for integrations
- [`docs/CHROME_COMPANION_PLAN.md`](docs/CHROME_COMPANION_PLAN.md) — Privacy-first browser extension spec
- [`docs/PRIZE_STRATEGY.md`](docs/PRIZE_STRATEGY.md) — How we target every award
- [`docs/FIELD_NOTES.md`](docs/FIELD_NOTES.md) — Architecture decisions & roadmap
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — 60-second video storyboard
- [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) — Model card for hackathon judges

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 🙋‍♂️ Team

Built with urgency, paranoia, and justice for the Hugging Face Build Small Hackathon.

> *"Scam Court AI puts suspicious messages on trial — and gives families a shield."*
