# 🔮 OpenBMB Vision Plan — Screenshot Witness

> Phase 6B: Real MiniCPM-V screenshot analysis is now live.

---

## Why MiniCPM-V?

OpenBMB's **MiniCPM-V** family is designed for efficient vision-language understanding on consumer hardware:

- **Small footprint** — runs on 8 GB VRAM or CPU-offload
- **Strong OCR** — reads text inside screenshots, memes, and photos
- **Multilingual** — handles scam messages in Spanish, Chinese, and more
- **Open weights** — fully local, no API keys, no cloud calls

These traits align perfectly with Scam Court AI's privacy-first, elder-safety mission.

---

## How Screenshot Analysis Works

```
User uploads screenshot of suspicious WhatsApp message
        ↓
MiniCPM-V runs OCR + vision-language reasoning on the image
        ↓
Returns strict JSON:
  - screenshot_type:       "whatsapp"
  - extracted_text:        "Hi Mom, send $500 via Zelle..."
  - visual_risk_clues:     ["urgency_banner", "unknown_sender", "payment_request"]
  - recommended_text_for_analysis: "Concise summary for scam engine"
  - vision_confidence:     0.92
        ↓
Text backend (heuristic or SmolLM3) analyzes extracted_text
        ↓
CourtroomReport v2.2.0 merges both streams
        ↓
UI shows:
  - Shield verdict from text analysis
  - Vision Witness card with type, extracted text, visual clues, confidence
```

---

## Current Status (Phase 6B)

| Component | Status |
|-----------|--------|
| Screenshot upload in Shield / Court tabs | ✅ Live |
| Vision backend abstraction | ✅ Live |
| Default no-op backend (`NoneVisionBackend`) | ✅ Live |
| Real MiniCPM-V backend (`MiniCPMVBackend`) | ✅ Live |
| Lazy model loading | ✅ Live |
| Robust JSON parsing from model output | ✅ Live |
| Raw-text fallback if JSON parse fails | ✅ Live |
| Device selection (cuda → cpu) | ✅ Live |
| Schema fields (v2.2.0) | ✅ Live |
| UI "Vision Witness" card | ✅ Live |
| Backend status indicator | ✅ Live |
| Safety rule: no LOW RISK when vision fails | ✅ Live |
| Text + screenshot combination | ✅ Live |
| Evaluation dataset with screenshot pairs | 🚧 Planned |

---

## Usage

### Default (no vision)

```powershell
python app.py
```

Screenshots are accepted but the app shows a safe fallback and forces **VERIFY FIRST**.

### With MiniCPM-V (local GPU or CPU)

```powershell
# Install dependencies
pip install transformers torch accelerate

# Activate
$env:SCAM_COURT_VISION_BACKEND = "minicpm_v"
$env:SCAM_COURT_VISION_MODEL = "openbmb/MiniCPM-V-4"
python app.py
```

The model downloads on first use (~8–16 GB depending on variant) and caches in `~/.cache/huggingface/`.

### With MiniCPM-V on Hugging Face ZeroGPU / GPU Space

For Spaces with GPU or ZeroGPU, add a GPU decorator and let the Space handle device allocation:

```python
# In app.py or a separate module
import os

def load_vision_model():
    """GPU-aware model loader for Spaces."""
    from transformers import AutoModel, AutoTokenizer
    model_id = os.getenv("SCAM_COURT_VISION_MODEL", "openbmb/MiniCPM-V-4")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True)
    return model, tokenizer

# If running on Spaces with @spaces.GPU:
# from spaces import GPU
# @GPU
# def analyze_with_gpu(image_path):
#     model, tokenizer = load_vision_model()
#     ...
```

Recommended Space settings:
- **Hardware:** GPU (NVIDIA T4 or better)
- **Sleep:** Allow sleeping (MiniCPM-V loads on demand)
- **Environment:** `SCAM_COURT_VISION_BACKEND=minicpm_v`

---

## Model Loading Strategy

1. **Lazy load** — model is not imported or downloaded until the first screenshot is uploaded
2. **Device auto-selection** — `cuda` if available, otherwise `cpu` with `float32`
3. **Error isolation** — any load failure is caught and returns `vision_status: "failed"` or `"not_available"`
4. **No startup delay** — text-only users experience zero model-load penalty
5. **Dependency pre-check** — missing `torch`/`transformers`/`pillow` are detected before model load with clear install instructions

---

## Prompt Design

MiniCPM-V receives a strict JSON prompt:

```
You are a forensic screenshot examiner. Inspect this image carefully.
Describe what you see and return ONLY a single JSON object...
{
  "screenshot_type": "...",
  "extracted_text": "...",
  "visual_risk_clues": ["..."],
  "recommended_text_for_analysis": "...",
  "vision_confidence": 0.0
}
```

**Safety rule:** The prompt explicitly forbids the model from giving safety advice. It only acts as a witness — reads, extracts, lists clues.

---

## Privacy Design

| Concern | Mitigation |
|---------|------------|
| Images stored on disk | Temporary path only; Gradio cleans up after session |
| Images sent to cloud | None — MiniCPM-V runs entirely locally |
| Images retained in report | Only metadata (`vision_status`, `extracted_text`); no image bytes |
| Background camera access | Not requested — upload button only |

**User-facing note:** *"Screenshot processed only for this session."*

---

## OpenBMB Award Alignment

| Criterion | How MiniCPM-V helps |
|-----------|---------------------|
| **Efficiency** | ≤8 GB VRAM, CPU-offload possible, no cloud costs |
| **Multilingual** | OCR handles Spanish, Chinese, and other scam-target languages |
| **Real-world impact** | Screenshots are how non-technical users actually share suspicious content |
| **Open weights** | Fully reproducible, no API gatekeeping |
| **Innovation** | First courtroom-themed scam analyzer with vision-language evidence |

---

## Status

✅ **Phase 6B complete — real MiniCPM-V screenshot analysis is live.**
