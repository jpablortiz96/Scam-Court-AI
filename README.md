---
title: Scam Court AI
emoji: 🛡️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.34.0
app_file: app.py
pinned: false
license: mit
python_version: "3.10"
---

# Scam Court AI

## A 3-Second Scam Shield with an AI Courtroom Behind It

[![Live Space](https://img.shields.io/badge/Hugging_Face-Live_Space-FFD21E)](https://huggingface.co/spaces/build-small-hackathon/scam-court-ai)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange)](https://www.gradio.app/)
[![MiniCPM-V-4](https://img.shields.io/badge/Vision-OpenBMB_MiniCPM--V--4-blue)](https://huggingface.co/openbmb/MiniCPM-V-4)
[![Evaluation](https://img.shields.io/badge/Safety_Eval-60%2F60_cases_pass-brightgreen)](docs/EVALUATION.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Scam Court AI helps a person pause before clicking, paying, or sharing a code.**
It gives an immediate `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK` action,
then opens a transparent courtroom explanation for anyone who wants the evidence.

**Live Space:**

https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

## The Problem

Scams arrive when people are rushed, frightened, or trying to help someone they
love. A fake package alert, "new number" family message, bank warning, or OTP
request can create pressure before the recipient has time to reason.

Older adults and non-technical family members often do not need a long security
report first. They need one calm instruction:

- Do not click.
- Do not send the code.
- Call the person using a saved number.
- Open the official app yourself.

Scam Court AI puts that protective action first and makes the reasoning
available second.

## How It Works

1. The user pastes a message, uploads a screenshot, or answers a short call checklist.
2. MiniCPM-V-4 can extract visible text and screenshot clues when vision is enabled.
3. The selected text backend produces a structured `CourtroomReport`.
4. A safety policy prevents incomplete or action-oriented evidence from receiving false reassurance.
5. The UI shows the immediate Shield verdict, then the Detective, Prosecutor, Defender, Judge, and Safety Clerk explanation.
6. The result can be exported as JSON for audit or future integrations.

## Five Product Surfaces

### Shield Mode

The urgent path. It returns a large safety verdict, risk score, immediate action,
and a script for asking a trusted person for help.

### Court Mode

The explanation path. Five courtroom roles turn detected evidence into a
structured, inspectable decision:

- **Detective:** collects visible red flags.
- **Prosecutor:** explains the manipulation pattern.
- **Defender:** tests plausible benign explanations.
- **Judge:** assigns the court verdict and risk score.
- **Safety Clerk:** gives safe next steps.

### Suspicious Call

A five-question active-call rescue flow for money requests, OTP requests,
family impersonation, urgency, and secrecy. It is designed to help someone stop
the interaction before pressure escalates.

### Companion Preview

A product preview for selected-text workflows in WhatsApp Web, SMS, and
marketplaces. It demonstrates how a future companion could bring the Shield
verdict to the message instead of making the user leave the conversation.

### Vision Witness

OpenBMB `openbmb/MiniCPM-V-4` reads uploaded screenshots, extracts visible text,
classifies the screenshot context, and identifies visual risk clues. Its output
is evidence for the existing safety engine, not a replacement for the policy.

If vision is unavailable or cannot extract usable text, screenshot-only input
is forced to `VERIFY FIRST`. The app does not pretend the image was analyzed.

## Models and Decision Layers

| Layer | Implementation | Role |
|---|---|---|
| Safety baseline | Deterministic heuristic engine | Fast pattern detection, scoring, policy enforcement, and offline fallback |
| Optional text backend | `HuggingFaceTB/SmolLM3-3B` | Structured small-model reasoning with heuristic fallback |
| Vision Witness | `openbmb/MiniCPM-V-4` | Screenshot text extraction and visual evidence |
| Experience layer | Gradio courtroom personas | Human-readable explanation and immediate action |

The default text backend is heuristic. SmolLM3 and MiniCPM-V are lazy-loaded
only when selected.

## Why Small Models Fit

This problem is constrained and action-oriented. The product does not need an
unbounded assistant; it needs fast evidence extraction, a narrow safety policy,
clear structured output, and reliable fallback behavior.

- Deterministic rules handle known high-risk patterns quickly.
- A 3B text model can provide optional structured reasoning without becoming a startup dependency.
- MiniCPM-V-4 supplies the missing screenshot evidence on demand.
- Each model path falls back to a safer deterministic action when it fails.

Small components make the system easier to inspect, run locally, evaluate, and
deploy within the hackathon's small-model constraint.

## Safety Philosophy

Scam Court AI optimizes against dangerous reassurance.

- **No false low-risk result when evidence is incomplete.**
- **Links and action requests resolve to verification, not trust.**
- **Never click a suspicious message link to verify the message.**
- **Never share an OTP, password, PIN, or recovery code.**
- **Never use a phone number supplied by the suspicious message.**
- **Use an official app, manually typed website, saved number, or trusted contact.**
- **`LOW VISIBLE RISK` means no strong signal was detected, not a guarantee of safety.**

## Evaluation Proof

The public synthetic suite contains **60 cases across 10 categories**:

- family impersonation
- OTP/code theft
- fake bank alerts
- package delivery scams
- marketplace deposit scams
- fake invoices
- government/refund/stimulus scams
- romance/emergency-money scams
- safe benign messages
- ambiguous action-required messages

Current deterministic baseline:

| Metric | Result |
|---|---:|
| Cases passed | 60 / 60 |
| Verdict accuracy | 100% |
| Score-range accuracy | 100% |
| False `LOW VISIBLE RISK` results | 0 |
| Safety failures | 0 |
| STOP recall | 100% |

These results are regression results on a synthetic, policy-focused dataset,
not a claim of real-world scam-detection accuracy. See
[`docs/EVALUATION.md`](docs/EVALUATION.md).

## Screenshots

| Proof view | Placeholder |
|---|---|
| Shield Mode with FedEx screenshot and `VERIFY FIRST` | Add final Shield capture before submission |
| Court Mode with five role cards and evidence | Add final Court capture before submission |
| Vision Witness extraction panel | Add MiniCPM-V screenshot evidence capture |
| Evaluation report summary | Add generated report capture |

## Privacy

- Local CPU mode sends no message or screenshot to a third-party model API.
- On the public Space, evidence is processed inside the Hugging Face Space session.
- The application does not intentionally persist uploaded screenshots or message text.
- Runtime logs contain backend diagnostics and errors, not message contents.
- JSON export is initiated by the user.

Do not submit passwords, OTPs, full payment-card data, government identifiers,
or other secrets to any demo application.

## Limitations

- The heuristic engine is English-first and can miss novel wording.
- Risk scores are weighted safety indicators, not calibrated probabilities.
- The 60-case dataset is synthetic and balanced for policy coverage.
- The app does not perform live URL reputation, sender identity, bank, or payment verification.
- MiniCPM-V extraction can fail on low-resolution, cropped, or visually complex screenshots.
- A low visible-risk result is not proof that a message is legitimate.
- Scam Court AI is an educational safety aid, not legal, financial, or cybersecurity advice.

## Run Locally

```powershell
git clone https://github.com/jpablortiz96/Scam-Court-AI.git
cd Scam-Court-AI
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

The CPU-safe defaults are:

```text
SCAM_COURT_BACKEND=heuristic
SCAM_COURT_VISION_BACKEND=none
SCAM_COURT_VISION_MODEL=openbmb/MiniCPM-V-4
```

Open http://localhost:7860.

## Deploy on Hugging Face Spaces

Create or duplicate a **Gradio Space**, push this repository, and select
**ZeroGPU** hardware for screenshot inference. Configure these Space variables:

```text
SCAM_COURT_BACKEND=heuristic
SCAM_COURT_VISION_BACKEND=minicpm_v
SCAM_COURT_VISION_MODEL=openbmb/MiniCPM-V-4
```

`analyze_message` is registered through the real `@spaces.GPU` decorator on
Hugging Face. MiniCPM-V still loads lazily after a screenshot request. For a
CPU-only Space, set `SCAM_COURT_VISION_BACKEND=none`.

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for startup and fallback details.

## Run the Safety Suite

```powershell
python -m compileall app.py courtroom tools modal tests
python -m unittest discover -s tests -v
python tools/evaluate_cases.py --fail-on-safety
```

Reports are written to:

```text
outputs/evaluation_report.json
outputs/evaluation_report.md
```

Optional Modal execution:

```powershell
python -m pip install modal
modal setup
modal run modal/eval_modal_job.py
```

Modal is not imported by the normal Gradio application.

## Architecture and Public Proof

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - runtime, data flow, ZeroGPU, and fallbacks
- [`docs/EVALUATION.md`](docs/EVALUATION.md) - metrics, dataset, and reproduction
- [`docs/FIELD_NOTES.md`](docs/FIELD_NOTES.md) - build story and lessons learned
- [`docs/DEMO_PLAN.md`](docs/DEMO_PLAN.md) - 60-90 second demo sequence
- [`docs/SUBMISSION_COPY.md`](docs/SUBMISSION_COPY.md) - submission and social copy
- [`docs/INTEGRATION_CONTRACT.md`](docs/INTEGRATION_CONTRACT.md) - JSON report contract
- [`data/agent_trace_example.json`](data/agent_trace_example.json) - representative public agent trace

## Hackathon Alignment

| Badge or award | Public evidence |
|---|---|
| Backyard AI | A concrete safety workflow for older adults and families |
| OpenBMB | MiniCPM-V-4 is the working Vision Witness |
| Off-Brand | A custom premium courtroom interface rather than a generic chatbot |
| Best Agent | Structured Detective-to-Safety-Clerk trace and JSON export |
| Best Demo | Immediate screenshot-to-verdict narrative with visible evidence |
| Field Notes | A publishable technical and human build story |
| Modal | Reproducible optional batch evaluation job |

## License

MIT. See [`LICENSE`](LICENSE).
