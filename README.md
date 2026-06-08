# ⚖️ Scam Court AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/gradio-UI-orange.svg)](https://gradio.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HF Spaces](https://img.shields.io/badge/🤗-Spaces-blue)](https://huggingface.co/spaces)

> **Put suspicious messages on trial before they hurt someone.**

Scam Court AI is a tiny, multi-agent courtroom that analyzes suspicious WhatsApp messages, SMS, emails, and marketplace chats. Instead of a boring green/red banner, you get a dramatic interactive trial:

- 🔍 **Detective** — extracts red flags
- ⚖️ **Prosecutor** — explains manipulation tactics
- 🛡️ **Defender** — checks if it could be legitimate
- 👨‍⚖️ **Judge** — delivers a risk score (0–100) and verdict
- 📋 **Safety Clerk** — writes a safe reply and next steps

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

Then open http://localhost:7860

---

## 🖼️ Screenshot

*(Add screenshot here after first UI run)*

---

## 🏗️ Architecture

```
scam-court-ai/
├── app.py                     # Gradio UI (custom CSS, premium courtroom feel)
├── courtroom/
│   ├── __init__.py
│   ├── engine.py              # Heuristic analysis engine (swappable for models)
│   ├── personas.py            # Persona prompts and metadata
│   └── utils.py               # Sanitization & formatting helpers
├── data/
│   ├── scam_examples_seed.json
│   ├── evaluation_cases.json
│   └── agent_trace_example.json
├── docs/
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
- **Dramatic UX:** Custom CSS makes it feel like a courtroom, not a chatbot.

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

## 🧑‍⚖️ Example Verdict

**Input:**
> "Hi honey, it's Mom. I got a new phone and lost all my contacts. Can you send me $500 via Zelle? I'm stuck at the grocery store and my card isn't working. Please don't tell Dad, it's embarrassing. Send it to this number quickly!"

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
| Backyard AI | Mom-friendly UI, safe replies, zero setup |
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

> *"Scam Court AI puts suspicious messages on trial."*
