# Scam Court AI Submission Copy

## Project Title

Scam Court AI

## Tagline

3-Second Scam Shield + AI Courtroom Explanation

## Short Description

Scam Court AI helps older adults and families pause before clicking, paying, or
sharing a code. It reads suspicious text or screenshots, gives an immediate
`STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK` action, and then explains the
evidence through a five-role AI courtroom.

## Long Description

Scams succeed under pressure. A fake package alert, suspended-bank warning,
"new number" family message, or OTP request can push someone toward an
irreversible action before they have time to investigate.

Scam Court AI is designed for that moment. Shield Mode gives one immediate
safety instruction. Court Mode then exposes the evidence through a Detective,
Prosecutor, Defender, Judge, and Safety Clerk. Suspicious Call provides a
five-question rescue flow during active calls, while Companion Preview
demonstrates future selected-text integrations.

OpenBMB MiniCPM-V-4 acts as the Vision Witness for uploaded screenshots. It
extracts visible text and visual clues, which feed the existing safety engine.
If screenshot analysis fails or evidence is incomplete, the app returns
`VERIFY FIRST` rather than false reassurance.

The default text path is a deterministic heuristic engine. An optional
SmolLM3-3B backend can provide structured small-model reasoning with heuristic
fallback. The app runs as a Gradio Hugging Face Space with ZeroGPU for
screenshot inference and remains CPU-safe when vision is disabled.

The public evaluation suite contains 60 synthetic cases across ten categories.
The current deterministic baseline passes 60/60 with zero false
`LOW VISIBLE RISK` results and zero safety failures. These are regression
results, not a claim of general real-world accuracy.

## Live Project

https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

## Tech Stack

- Python 3.10+
- Gradio
- Hugging Face Spaces and ZeroGPU
- `spaces` GPU decorator
- PyTorch and Transformers
- OpenBMB MiniCPM-V-4
- Optional HuggingFaceTB SmolLM3-3B
- Deterministic heuristic safety engine
- Modal optional batch evaluation
- JSON/Markdown evaluation reports

## Models Used

| Model or engine | Use |
|---|---|
| Heuristic safety engine | Default text analysis, scoring, policy, and fallback |
| `HuggingFaceTB/SmolLM3-3B` | Optional structured text reasoning |
| `openbmb/MiniCPM-V-4` | Screenshot Vision Witness |

## Public Prize Positioning

- **Backyard AI:** built around a concrete family safety problem.
- **OpenBMB:** MiniCPM-V-4 performs working screenshot analysis.
- **Off-Brand:** the custom courtroom interface is deliberately not a chatbot.
- **Best Agent:** five explicit roles produce a structured, shareable trace.
- **Best Demo:** one visual story moves from screenshot to action to evidence.
- **Field Notes:** the build story documents product and safety decisions.
- **Modal:** the same evaluation runner can execute as an optional Modal job.

## Social Post Draft

Scams do not arrive when someone is ready to investigate. They arrive when a
person is rushed and one click away from harm.

I built **Scam Court AI**: a 3-Second Scam Shield with an AI courtroom behind it.

- Upload a suspicious screenshot
- OpenBMB MiniCPM-V-4 reads the visible evidence
- Get `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK`
- Inspect the Detective, Prosecutor, Defender, Judge, and Safety Clerk
- Review a 60-case safety evaluation focused on false reassurance

Current deterministic baseline: 60/60 cases passed, 0 false low-risk results.

Try the live Hugging Face Space:  
https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

#BuildSmall #Gradio #HuggingFace #OpenBMB #ZeroGPU #AIForGood

## Video Description Draft

Scam Court AI is a Gradio safety application for suspicious messages,
screenshots, and active phone calls. In this demo, OpenBMB MiniCPM-V-4 reads a
synthetic FedEx delivery screenshot, the Shield returns `VERIFY FIRST`, and the
AI courtroom explains the evidence. The demo also covers the active-call rescue
flow, Companion Preview, JSON agent trace, and the 60-case safety evaluation.

Live Space:  
https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

Repository:  
https://github.com/jpablortiz96/Scam-Court-AI
