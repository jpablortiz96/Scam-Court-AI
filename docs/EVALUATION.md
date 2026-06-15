# Evaluation and Safety Testing

Scam Court AI includes a deterministic evaluation suite for its current analysis
backend. The suite measures whether the product gives the safest visible action,
not whether it can prove fraud with legal certainty.

## What It Measures

- Shield verdict accuracy: `STOP`, `VERIFY_FIRST`, or `LOW_VISIBLE_RISK`
- Risk score compliance with a case-specific expected range
- False reassurance rate on cases that must not be labeled low risk
- STOP recall for explicit high-risk scenarios
- Safety failures, including backend errors, false low-risk results, and missed
  STOP verdicts
- Pass rate by scam category
- Average risk score by scam category

The JSON and Markdown reports include every case result, detected pattern IDs,
policy tags, backend identity, and aggregate metrics.

## Why False LOW RISK Is Dangerous

A false positive can inconvenience a user. A false `LOW_VISIBLE_RISK` result can
encourage a vulnerable user to click a link, send money, disclose credentials,
or share an OTP. For this reason, link and action cases are marked
`must_not_return_low_risk`, and uncertainty should resolve to `VERIFY_FIRST`
rather than reassurance.

The primary safety metric is:

```text
false reassurance rate =
false LOW_VISIBLE_RISK results / cases protected by the no-low-risk guard
```

## Categories Tested

The dataset currently contains 60 cases across:

- Family impersonation
- OTP and verification-code theft
- Fake bank alerts
- Package and delivery scams
- Marketplace deposit scams
- Fake invoices
- Government, refund, and stimulus scams
- Romance and emergency-money scams
- Safe benign messages
- Ambiguous messages that still require a link or account action

Each case records its category, expected verdict, accepted score range,
rationale, no-low-risk guard, and tags.

## Run Locally

The evaluation uses the configured text backend. With no environment override,
it uses the normal deterministic heuristic backend and does not load MiniCPM-V.

```powershell
python tools\evaluate_cases.py
```

Fail a CI or verification command when a safety failure occurs:

```powershell
python tools\evaluate_cases.py --fail-on-safety
```

Reports are written to:

```text
outputs/evaluation_report.json
outputs/evaluation_report.md
```

## Run With Modal

Modal is optional and is not imported by the Gradio application.

```powershell
python -m pip install modal
modal setup
modal run modal/eval_modal_job.py
```

The Modal function packages only the evaluation dataset, `courtroom` engine,
and evaluation tool. It prints summary metrics and returns the summary object.
It contains no private token, hardcoded credential, or model secret.

## Safety and Trust

The suite makes product policy inspectable. Judges and contributors can see
which scenarios are protected, how the engine scored them, whether the safety
policy intervened, and whether any dangerous reassurance occurred.

Required regression guardrails include:

- FedEx or package action links return `VERIFY_FIRST`, never low risk.
- OTP or code requests return `STOP`.
- Family new-number money requests return `STOP`.
- Suspended bank account credential links return `STOP`.
- Safe casual messages return `LOW_VISIBLE_RISK`.
- Screenshot analysis failure returns `VERIFY_FIRST`.

## Current Limitations

- The dataset is synthetic and English-first.
- It is balanced for policy coverage, not representative of real-world scam
  prevalence.
- Risk scores are heuristic safety scores, not calibrated probabilities.
- Text evaluation does not measure MiniCPM-V OCR or screenshot extraction
  quality.
- The runner does not perform live domain reputation, sender identity, payment,
  or bank verification.
- Future versions should add multilingual cases, human-authored adversarial
  cases, screenshot fixtures, and longitudinal regression tracking.
