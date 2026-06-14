# Hugging Face Spaces Deployment

Scam Court AI supports Hugging Face ZeroGPU for MiniCPM-V screenshot analysis.
The Gradio handler `analyze_message` is registered with `@spaces.GPU` through a
safe compatibility helper.

## ZeroGPU Configuration

Select **ZeroGPU** in the Space hardware settings and configure:

```text
SCAM_COURT_BACKEND=heuristic
SCAM_COURT_VISION_BACKEND=minicpm_v
SCAM_COURT_VISION_MODEL=openbmb/MiniCPM-V-4
```

ZeroGPU requires at least one function decorated with `@spaces.GPU` during
startup. The `spaces` package is listed in `requirements.txt`, and the shared
Shield/Court analysis handler receives the real decorator when that package is
available.

MiniCPM-V remains lazy-loaded. Importing the app registers the decorated
function but does not download or initialize the model. The model-loading path
runs only after an uploaded screenshot reaches `analyze_message`.

The decorator reserves up to 180 seconds for the first request because model
download and initialization can be slower than subsequent analyses.

## CPU-Only Fallback

For a CPU-only demo, set:

```text
SCAM_COURT_BACKEND=heuristic
SCAM_COURT_VISION_BACKEND=none
SCAM_COURT_VISION_MODEL=openbmb/MiniCPM-V-4
```

If the `spaces` package is unavailable during local development, the decorator
helper becomes a no-op and `python app.py` continues to work normally.

If vision loading or inference fails, screenshot-only analysis remains
safety-biased: it returns `VERIFY FIRST` and never `LOW VISIBLE RISK`.

## Startup Diagnostics

Startup logs report:

- Text backend
- Vision backend
- Vision model
- Whether the `spaces` import succeeded
- Whether the GPU decorator is active
- Whether the process is running inside ZeroGPU
- Port

Vision failures log the exception type, exception message, model ID, selected
device, and ZeroGPU decorator state. Message and screenshot contents are not
logged.

## Verification

```powershell
python -m pip install -r requirements.txt
python -m compileall app.py courtroom
python app.py
```

CPU fallback:

```powershell
$env:SCAM_COURT_BACKEND="heuristic"
$env:SCAM_COURT_VISION_BACKEND="none"
python app.py
```

ZeroGPU configuration check:

```powershell
$env:SCAM_COURT_BACKEND="heuristic"
$env:SCAM_COURT_VISION_BACKEND="minicpm_v"
$env:SCAM_COURT_VISION_MODEL="openbmb/MiniCPM-V-4"
python -c "import app; from courtroom.zero_gpu import ZERO_GPU_DECORATOR_ACTIVE; print(ZERO_GPU_DECORATOR_ACTIVE)"
```
