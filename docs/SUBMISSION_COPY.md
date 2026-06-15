# Scam Court AI Submission Copy

## Title

Scam Court AI

## Tagline

3-Second Scam Shield + AI Courtroom Explanation

## Short Description

Scam Court AI helps older adults and families pause before clicking, paying, or
sharing a code. It reads suspicious text or screenshots, gives an immediate
`STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK` action, and then explains the
evidence through a five-role AI courtroom.

## Long Description

Scams succeed during a narrow window of pressure. A fake delivery alert,
suspended-bank warning, "new number" family message, marketplace deposit
request, or OTP prompt can push someone toward an irreversible action before
they have time to investigate.

Scam Court AI is designed for that moment. It is not an open-ended chatbot; it
is a safety pause.

Shield Mode gives one immediate instruction. Vision Witness uses OpenBMB
MiniCPM-V-4 to extract visible screenshot evidence. Court Mode then exposes the
reasoning through a Detective, Prosecutor, Defender, Judge, and Safety Clerk.
Suspicious Call provides a five-question rescue flow during an active call.
Companion Preview and the Manifest V3 Chrome prototype show how the same
structured decision can move closer to WhatsApp, SMS, email, and marketplace
workflows.

The default text path is the deterministic `heuristic_v1` safety engine. An
optional SmolLM3-3B backend can produce structured reasoning with heuristic
fallback. The Gradio app runs on Hugging Face Spaces with ZeroGPU around the
screenshot path and remains CPU-safe when vision is disabled.

The product is intentionally conservative. Incomplete screenshot evidence,
vision failure, and Chrome API failure resolve to `VERIFY FIRST`. OTP, password,
high-pressure money, and family-impersonation patterns resolve to `STOP`.

The public evaluation suite contains 60 synthetic cases across ten categories.
The current deterministic baseline passes 60/60 with zero false
`LOW VISIBLE RISK` results and zero safety failures. These are policy regression
results, not a claim of general real-world detection accuracy.

## Links

- **Live Space:** https://huggingface.co/spaces/build-small-hackathon/scam-court-ai
- **GitHub:** https://github.com/jpablortiz96/Scam-Court-AI
- **Demo video:** `ADD_FINAL_60_90_SECOND_VIDEO_URL`
- **Architecture:** https://github.com/jpablortiz96/Scam-Court-AI/blob/main/docs/ARCHITECTURE.md
- **Field Notes:** https://github.com/jpablortiz96/Scam-Court-AI/blob/main/docs/FIELD_NOTES.md

## Tech Stack

- Python 3.10+
- Gradio
- Hugging Face Spaces and ZeroGPU
- `spaces.GPU`
- PyTorch and Transformers
- `openbmb/MiniCPM-V-4`
- optional `HuggingFaceTB/SmolLM3-3B`
- deterministic `heuristic_v1` safety engine
- Manifest V3 Chrome extension
- JSON `CourtroomReport` integration contract
- JSON and Markdown evaluation reports
- optional Modal evaluation scaffold

## Models and Engines

| Component | Use |
|---|---|
| `heuristic_v1` | Default text analysis, weighted safety policy, action selection, and fallback |
| `openbmb/MiniCPM-V-4` | Screenshot Vision Witness |
| `HuggingFaceTB/SmolLM3-3B` | Optional structured text-reasoning scaffold |

## Safety Proof

- 60/60 synthetic evaluation cases passed.
- Zero false `LOW VISIBLE RISK` results.
- Zero safety failures.
- 100% STOP recall in the committed suite.
- Screenshot failure returns `VERIFY FIRST`.
- Chrome API failure returns `VERIFY FIRST`.
- Package-action links require independent verification.
- OTP, password, PIN, and high-pressure money requests return `STOP`.

## 60-90 Second Demo Flow

1. Open Shield Mode with a synthetic delivery screenshot.
2. Show MiniCPM-V-4 extracting text and visual clues.
3. Reveal `VERIFY FIRST` and the instruction not to click.
4. Switch to Court Mode and show the five roles.
5. Run Call Check with money, OTP, family, urgency, and secrecy selected.
6. Select suspicious text and invoke the Chrome Companion.
7. End on the 60-case safety evaluation and live Space URL.

## Prize-Category Positioning

- **Backyard AI:** built for a concrete family safety problem at the moment of risk.
- **OpenBMB:** MiniCPM-V-4 performs working screenshot evidence extraction.
- **Off-Brand:** a custom editorial courtroom rather than a generic chatbot.
- **Best Agent:** five explicit roles write to a stable, exportable trace.
- **Best Demo:** one visual story moves from screenshot to action to explanation.
- **Field Notes:** a publishable account of the product and safety decisions.
- **Modal:** the same deterministic evaluation runner has an optional Modal path.
- **Best Use of Codex:** Codex was used holistically to build and refactor the UI,
  ZeroGPU integration, evaluation suite, tests, browser companion, architecture,
  screenshot proof pack, deployment documentation, and final public presentation.

## Social Post Draft

Scams do not arrive when someone is ready to investigate. They arrive when a
person is rushed and one click away from harm.

I built **Scam Court AI** for the Hugging Face + Gradio Build Small Hackathon:
a 3-Second Scam Shield with an AI courtroom behind it.

- Upload a suspicious screenshot
- OpenBMB MiniCPM-V-4 reads the visible evidence
- Get `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK`
- Inspect the Detective, Prosecutor, Defender, Judge, and Safety Clerk
- Use a selected-text Chrome Companion with no background monitoring
- Review a 60-case safety evaluation focused on false reassurance

Current deterministic baseline: 60/60 cases passed, zero false low-risk results,
and zero safety failures.

Live Space:
https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

GitHub:
https://github.com/jpablortiz96/Scam-Court-AI

#BuildSmall #Gradio #HuggingFace #OpenBMB #ZeroGPU #Codex #AIForGood

## Video Description Draft

Scam Court AI is a Gradio safety application for suspicious messages,
screenshots, and active phone calls. In this demo, OpenBMB MiniCPM-V-4 reads a
synthetic delivery screenshot, the Shield returns `VERIFY FIRST`, and the AI
courtroom explains the visible evidence. The demo also covers the active-call
rescue flow, selected-text Chrome Companion, `CourtroomReport` export, and the
60-case safety evaluation.

Scam Court AI is not a chatbot. It is a safety pause: one clear action first,
then the evidence.

Live Space:
https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

Repository:
https://github.com/jpablortiz96/Scam-Court-AI
