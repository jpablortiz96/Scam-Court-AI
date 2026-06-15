# Scam Court AI Model and System Card

## System Summary

Scam Court AI is a multimodal consumer-safety system for suspicious messages,
screenshots, marketplace conversations, and phone-call warning signs. It
combines a deterministic safety engine, an optional small text model, and an
on-demand vision model.

The system produces:

- a Shield verdict: `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK`;
- a weighted risk score from 0 to 100;
- detected evidence and scenario tags;
- Detective, Prosecutor, Defender, Judge, and Safety Clerk outputs;
- an immediate action and trusted-contact script;
- vision provenance and known limitations;
- exportable JSON.

## Components

| Component | Identifier | Status | Purpose |
|---|---|---|---|
| Heuristic engine | `heuristic_v1` | Default | Detection, scoring, safety policy, and fallback |
| Small text model | `HuggingFaceTB/SmolLM3-3B` | Optional | Structured reasoning with heuristic fallback |
| Vision model | `openbmb/MiniCPM-V-4` | Active when enabled | Screenshot text extraction and visual clues |

The heuristic engine has no learned parameters. SmolLM3 and MiniCPM-V are
lazy-loaded only when their backends are selected.

## Intended Use

- Help users pause before clicking a suspicious link.
- Identify OTP, payment, impersonation, delivery, invoice, and account-action risks.
- Explain visible risk signals in accessible language.
- Provide a safer independent-verification action.
- Support education, family discussion, and prototype integrations.

## Out of Scope

- Proving that a sender or website is legitimate.
- Live domain reputation or malware scanning.
- Legal, financial, law-enforcement, or cybersecurity advice.
- Blocking messages or making payments on the user's behalf.
- Background surveillance of chats, email, or browser activity.

## Safety Behavior

- Screenshot-only failure returns `VERIFY FIRST`, never low visible risk.
- OTP, password, PIN, and recovery-code requests are treated as stop signals.
- Family impersonation combined with money is treated as a stop signal.
- Links and action requests require independent verification.
- The app never recommends verifying through the suspicious link or phone number.
- `LOW VISIBLE RISK` is not a guarantee of legitimacy.

## Evaluation

The committed synthetic dataset contains 60 cases across ten categories. The
current deterministic baseline reports:

| Metric | Result |
|---|---:|
| Cases passed | 60 / 60 |
| Verdict accuracy | 100% |
| Score-range accuracy | 100% |
| False low-visible-risk results | 0 |
| Safety failures | 0 |
| STOP recall | 100% |

These are regression results against expected policy behavior, not a
real-world prevalence-weighted accuracy estimate. Reproduce them with:

```powershell
python tools/evaluate_cases.py --fail-on-safety
```

## Data

- The heuristic patterns were authored for common consumer scam scenarios.
- No model fine-tuning is performed by this repository.
- The evaluation dataset is synthetic and contains no intended real personal data.
- Uploaded user evidence is not added to a training dataset by the application.

## Privacy

Local heuristic mode does not call a third-party inference API. The public
Hugging Face Space processes evidence within the Space session. The
application does not intentionally persist submitted messages or screenshots,
and runtime diagnostics avoid logging their contents.

Users should not submit passwords, OTPs, payment-card data, government
identifiers, or other secrets.

## Limitations and Bias

- English-first patterns can under-detect multilingual scams.
- Regex and weighted rules can miss novel wording or over-flag legitimate messages.
- The score is not a calibrated probability.
- MiniCPM-V can misread low-resolution or visually complex screenshots.
- The evaluation dataset is synthetic and balanced for coverage.
- The Defender role does not eliminate false positives.
- No component independently confirms sender identity or URL ownership.

## Deployment

The live Space uses Gradio and ZeroGPU. MiniCPM-V is called through a function
registered with `@spaces.GPU` and remains lazy-loaded.

Live Space:

https://huggingface.co/spaces/build-small-hackathon/scam-court-ai

Repository:

https://github.com/jpablortiz96/Scam-Court-AI

## License

MIT.
