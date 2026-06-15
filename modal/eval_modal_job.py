"""Run the Scam Court AI evaluation suite on Modal.

Setup:
    python -m pip install modal
    modal setup

Run from the repository root:
    modal run modal/eval_modal_job.py

This job is optional. The normal Gradio app never imports Modal and does not
require the Modal package. No secrets or private tokens are embedded here.
"""

from __future__ import annotations

import json
from pathlib import Path

import modal

APP_ROOT = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/scam-court-ai"

app = modal.App("scam-court-ai-evaluation")
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("python-dotenv>=1.0")
    .add_local_dir(APP_ROOT / "courtroom", f"{REMOTE_ROOT}/courtroom")
    .add_local_dir(APP_ROOT / "tools", f"{REMOTE_ROOT}/tools")
    .add_local_file(
        APP_ROOT / "data" / "evaluation_cases.json",
        f"{REMOTE_ROOT}/data/evaluation_cases.json",
    )
)


@app.function(image=image, timeout=600)
def run_evaluation() -> dict:
    import sys

    sys.path.insert(0, REMOTE_ROOT)
    from tools.evaluate_cases import evaluate_cases, load_cases, print_summary

    cases = load_cases(Path(REMOTE_ROOT) / "data" / "evaluation_cases.json")
    evaluation = evaluate_cases(cases)
    print_summary(evaluation)
    print(json.dumps(evaluation["summary"], indent=2))
    return evaluation["summary"]


@app.local_entrypoint()
def main() -> None:
    summary = run_evaluation.remote()
    print("Modal evaluation complete:")
    print(json.dumps(summary, indent=2))
