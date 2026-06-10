"""SmolLM3-3B backend — optional small-model reasoning.

Lazy-loads HuggingFaceTB/SmolLM3-3B only when selected via SCAM_COURT_BACKEND.
Falls back to heuristic on any load or generation error.
"""

from __future__ import annotations

import dataclasses
import datetime
import secrets
from typing import TYPE_CHECKING

from .base import BaseBackend
from ..engine import CourtroomEngine, CourtroomReport
from ..json_parser import parse_model_json
from ..prompts import build_smollm3_prompt

if TYPE_CHECKING:
    from transformers import AutoModelForCausalLM, AutoTokenizer

_MODEL_ID = "HuggingFaceTB/SmolLM3-3B"


class SmolLM3Backend(BaseBackend):
    """Small-model backend using HuggingFaceTB/SmolLM3-3B.

    Requires `transformers` and `torch` (install manually when using this backend).
    Keeps heuristic as fallback for speed and reliability.
    """

    model_backend = "smollm3"

    def __init__(self) -> None:
        self._engine = CourtroomEngine()
        self._model: "AutoModelForCausalLM | None" = None
        self._tokenizer: "AutoTokenizer | None" = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------
    def _lazy_load(self) -> None:
        if self._loaded:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "SmolLM3 backend requires 'transformers' and 'torch'. "
                "Install them: pip install transformers torch"
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(_MODEL_ID)
        self._model = AutoModelForCausalLM.from_pretrained(
            _MODEL_ID,
            device_map="cpu",
            torch_dtype="auto",
        )
        self._loaded = True

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze(self, raw_text: str) -> CourtroomReport:
        """Run heuristic pre-analysis, then prompt SmolLM3 for structured output.

        On any failure (load error, generation error, invalid JSON),
        falls back to the heuristic report with a clear fallback marker.
        """
        # Always get heuristic baseline first (fast, reliable)
        heuristic_report = self._engine.analyze(raw_text)

        try:
            self._lazy_load()
            prompt = build_smollm3_prompt(raw_text, heuristic_report)

            # Tokenize and generate
            inputs = self._tokenizer(prompt, return_tensors="pt")  # type: ignore[misc]
            outputs = self._model.generate(  # type: ignore[misc]
                **inputs,
                max_new_tokens=1200,
                temperature=0.3,
                do_sample=True,
                repetition_penalty=1.1,
                pad_token_id=self._tokenizer.eos_token_id,
            )
            generated = self._tokenizer.decode(outputs[0], skip_special_tokens=True)  # type: ignore[misc]

            # Parse generated JSON
            fallback_dict = heuristic_report.to_dict()
            parsed = parse_model_json(generated, fallback_dict)

            # Enforce schema metadata that the model should not control
            parsed["report_id"] = f"scr-{secrets.token_urlsafe(6)}"
            parsed["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            parsed["schema_version"] = "2.0.0"
            parsed["model_backend"] = "smollm3_v1"
            parsed["limitations"] = list(CourtroomEngine.LIMITATIONS)

            # Build CourtroomReport from parsed dict
            return CourtroomReport(**parsed)

        except Exception as exc:
            return self._fallback(heuristic_report, str(exc))

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------
    def _fallback(self, heuristic_report: CourtroomReport, error_msg: str) -> CourtroomReport:
        """Return heuristic report with a clear fallback marker."""
        return dataclasses.replace(
            heuristic_report,
            model_backend="heuristic_fallback_after_smollm3_error",
            agent_trace={
                **heuristic_report.agent_trace,
                "fallback_reason": error_msg,
                "fallback_source": "smollm3",
            },
        )
