"""MiniCPM-V vision backend — real screenshot analysis.

Loads openbmb/MiniCPM-V-4 (or user-configured model) lazily.
Falls back safely if dependencies are missing or the model fails.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from .base import BaseVisionBackend
from ..zero_gpu import (
    SPACES_IMPORT_SUCCEEDED,
    ZERO_GPU_DECORATOR_ACTIVE,
    ZERO_GPU_RUNTIME_ACTIVE,
)

_DEFAULT_MODEL = "openbmb/MiniCPM-V-4"
_LOGGER = logging.getLogger(__name__)

_VISION_PROMPT = """You are a forensic screenshot examiner. Inspect this image carefully.

Describe what you see and return ONLY a single JSON object with no markdown, no explanation, and no code fences.

Required JSON format:
{
  "screenshot_type": "whatsapp|sms|email|marketplace|invoice|bank_alert|unknown",
  "extracted_text": "All visible text from the image, transcribed exactly.",
  "visual_risk_clues": ["fake URL bar", "urgency banner", "mismatched logo", "unknown sender", "payment request"],
  "recommended_text_for_analysis": "A clean summary of the message content for further scam analysis.",
  "vision_confidence": 0.85
}

Rules:
- screenshot_type: classify the screenshot type.
- extracted_text: transcribe every readable word.
- visual_risk_clues: list specific visual scam signals you actually see. Use real descriptions. Do NOT output placeholder words like "list", "of", "visual", "red", "flags", "item", or "none".
- recommended_text_for_analysis: a concise paragraph of the suspicious message content.
- vision_confidence: number 0.0–1.0 estimating how sure you are.
- Do NOT give safety advice. Only describe what you observe.
- Return ONLY valid JSON. No markdown, no explanation before or after.
"""


def _extract_json(raw: str) -> dict[str, Any] | None:
    """Try to extract a JSON object from raw text."""
    # Try direct parse first
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try first { ... } pair
    brace_match = re.search(r"(\{.*\})", raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def _get_device() -> str:
    """Return best available torch device."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _get_versions() -> dict[str, str]:
    """Return diagnostic version info for torch and transformers."""
    versions: dict[str, str] = {"vision_model": _DEFAULT_MODEL, "device": _get_device()}
    try:
        import torch
        versions["torch"] = torch.__version__
    except Exception:
        versions["torch"] = "unknown"
    try:
        import transformers
        versions["transformers"] = transformers.__version__
    except Exception:
        versions["transformers"] = "unknown"
    return versions


def _log_vision_failure(exc: BaseException, model_id: str) -> None:
    """Log deployment diagnostics without exposing message or image contents."""
    _LOGGER.error(
        "MiniCPM-V failure: exception_type=%s exception_message=%s "
        "model_id=%s device=%s spaces_import_succeeded=%s "
        "zero_gpu_decorator_active=%s zero_gpu_runtime_active=%s",
        type(exc).__name__,
        str(exc),
        model_id,
        _get_device(),
        SPACES_IMPORT_SUCCEEDED,
        ZERO_GPU_DECORATOR_ACTIVE,
        ZERO_GPU_RUNTIME_ACTIVE,
        exc_info=(type(exc), exc, exc.__traceback__) if exc.__traceback__ else False,
    )


class MiniCPMVBackend(BaseVisionBackend):
    """Real MiniCPM-V vision backend.

    Install dependencies before activating:
        pip install transformers torch accelerate

    Environment:
        SCAM_COURT_VISION_BACKEND=minicpm_v
        SCAM_COURT_VISION_MODEL=openbmb/MiniCPM-V-4   (optional)
    """

    backend_name = "minicpm_v"

    def __init__(self) -> None:
        self._model: Any = None
        self._tokenizer: Any = None
        self._loaded = False
        self._load_error: str | None = None
        self._model_id = os.getenv("SCAM_COURT_VISION_MODEL", _DEFAULT_MODEL)

    def _lazy_load(self) -> bool:
        """Attempt to load the model once. Return True on success."""
        if self._loaded:
            return self._load_error is None

        # Explicit dependency pre-check for clearer error messages
        missing = []
        try:
            import torch
            _ = torch
        except Exception:
            missing.append("torch")
        try:
            from transformers import AutoModel, AutoTokenizer
            _ = AutoModel, AutoTokenizer
        except Exception:
            missing.append("transformers")
        try:
            from PIL import Image
            _ = Image
        except Exception:
            missing.append("pillow")

        if missing:
            self._loaded = True
            self._load_error = (
                f"Missing dependencies: {', '.join(missing)}. "
                f"Install with: pip install {' '.join(missing)}"
            )
            _log_vision_failure(RuntimeError(self._load_error), self._model_id)
            return False

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            device = _get_device()
            self._tokenizer = AutoTokenizer.from_pretrained(
                self._model_id,
                trust_remote_code=True,
            )
            self._model = AutoModel.from_pretrained(
                self._model_id,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
            )
            self._model = self._model.to(device).eval()
            self._loaded = True
            self._load_error = None
            return True
        except AttributeError as exc:
            # Known Transformers compatibility issue with trust_remote_code models
            self._loaded = True
            _log_vision_failure(exc, self._model_id)
            err_msg = str(exc)
            if "all_tied_weights_keys" in err_msg:
                versions = _get_versions()
                self._load_error = (
                    f"Transformers compatibility issue: {err_msg}. "
                    f"MiniCPM-V-4 requires transformers 4.x (detected {versions.get('transformers', 'unknown')}). "
                    f"Install a stable 4.x release: pip install 'transformers>=4.45,<5'"
                )
            else:
                self._load_error = err_msg
            return False
        except Exception as exc:
            self._loaded = True
            _log_vision_failure(exc, self._model_id)
            self._load_error = str(exc)
            return False

    def analyze_image(
        self,
        image_path: str,
        context_text: str | None = None,
    ) -> dict[str, Any]:
        if not self._lazy_load():
            # Determine if this is a dependency issue or a model load issue
            status = "not_available" if "Missing dependencies" in (self._load_error or "") else "failed"
            return {
                "vision_status": status,
                "vision_model": self._model_id,
                "vision_summary": (
                    "MiniCPM-V is not available. "
                    "Paste the message text for full analysis."
                ),
                "extracted_text": None,
                "screenshot_type": None,
                "screenshot_risk_clues": [],
                "recommended_text_for_analysis": None,
                "vision_confidence": 0.0,
                "vision_error": self._load_error,
                "vision_diagnostics": _get_versions(),
            }

        try:
            from PIL import Image
            import torch

            device = _get_device()
            image = Image.open(image_path).convert("RGB")

            # Build messages for MiniCPM-V chat API
            msgs = [
                {
                    "role": "user",
                    "content": [_VISION_PROMPT, image],
                }
            ]

            # MiniCPM-V chat signature varies by version;
            # try common patterns and fall back gracefully.
            generated_text = ""
            try:
                # MiniCPM-V-4 style: model.chat(image=image, msgs=msgs, tokenizer=tokenizer)
                res = self._model.chat(
                    image=image,
                    msgs=msgs,
                    tokenizer=self._tokenizer,
                    sampling=False,
                    temperature=0.0,
                )
                if isinstance(res, str):
                    generated_text = res
                elif isinstance(res, (list, tuple)) and len(res) > 0:
                    generated_text = str(res[0])
                else:
                    generated_text = str(res)
            except TypeError:
                # Fallback: try without image keyword
                try:
                    res = self._model.chat(
                        msgs=msgs,
                        tokenizer=self._tokenizer,
                        sampling=False,
                    )
                    generated_text = str(res[0]) if isinstance(res, (list, tuple)) else str(res)
                except Exception:
                    # Final fallback: use tokenizer + generate
                    inputs = self._tokenizer.apply_chat_template(
                        msgs,
                        tokenize=True,
                        return_tensors="pt",
                        return_dict=True,
                    )
                    if hasattr(inputs, "to"):
                        inputs = inputs.to(device)
                    with torch.no_grad():
                        outputs = self._model.generate(
                            **inputs,
                            max_new_tokens=1024,
                            do_sample=False,
                        )
                    generated_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

            parsed = _extract_json(generated_text)

            if parsed is None:
                # Could not parse JSON — use raw text as extracted_text
                return {
                    "vision_status": "analyzed",
                    "vision_model": self._model_id,
                    "vision_summary": "MiniCPM-V returned unstructured output. Using raw transcription.",
                    "extracted_text": generated_text.strip()[:2000],
                    "screenshot_type": "unknown",
                    "screenshot_risk_clues": ["unstructured_model_output"],
                    "recommended_text_for_analysis": generated_text.strip()[:2000],
                    "vision_confidence": 0.3,
                    "vision_error": "JSON parse failed; used raw text fallback.",
                }

            return {
                "vision_status": "analyzed",
                "vision_model": self._model_id,
                "vision_summary": "MiniCPM-V analyzed the screenshot.",
                "extracted_text": str(parsed.get("extracted_text", "")).strip()[:2000] or None,
                "screenshot_type": str(parsed.get("screenshot_type", "unknown")).strip().lower(),
                "screenshot_risk_clues": [
                    str(c).strip()
                    for c in parsed.get("visual_risk_clues", [])
                    if str(c).strip()
                ],
                "recommended_text_for_analysis": str(parsed.get("recommended_text_for_analysis", "")).strip()[:2000] or None,
                "vision_confidence": float(parsed.get("vision_confidence", 0.0)),
                "vision_error": None,
            }

        except Exception as exc:
            _log_vision_failure(exc, self._model_id)
            versions = _get_versions()
            err_msg = str(exc)
            if "all_tied_weights_keys" in err_msg:
                err_msg = (
                    f"Transformers compatibility issue: {err_msg}. "
                    f"MiniCPM-V-4 requires transformers 4.x (detected {versions.get('transformers', 'unknown')}). "
                    f"Install: pip install 'transformers>=4.45,<5'"
                )
            return {
                "vision_status": "failed",
                "vision_model": self._model_id,
                "vision_summary": "Screenshot analysis failed. Paste the message text for full analysis.",
                "extracted_text": None,
                "screenshot_type": None,
                "screenshot_risk_clues": [],
                "recommended_text_for_analysis": None,
                "vision_confidence": 0.0,
                "vision_error": err_msg,
                "vision_diagnostics": versions,
            }

    def is_available(self) -> bool:
        return self._lazy_load()
