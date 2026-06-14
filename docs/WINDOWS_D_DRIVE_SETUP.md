# 🖥️ Windows D: Drive Setup Guide

> For users with limited **C:** drive space who want to run Scam Court AI (and MiniCPM-V) entirely from **D:**.

---

## Problem

By default, Python caches, pip packages, Hugging Face models, and PyTorch weights all land on **C:** under your user profile. MiniCPM-V-4 alone needs **8–16 GB** of cache space. If your C: drive is a small SSD, this fills up quickly.

## Solution

Move every cache to **D:\AI_CACHE** and keep the virtual environment inside **D:\scam-court-ai\.venv**.

---

## 1. Create Cache Folders on D:

Open **PowerShell** and run:

```powershell
# Create cache directories
New-Item -ItemType Directory -Force -Path "D:\AI_CACHE\pip"
New-Item -ItemType Directory -Force -Path "D:\AI_CACHE\huggingface"
New-Item -ItemType Directory -Force -Path "D:\AI_CACHE\torch"
New-Item -ItemType Directory -Force -Path "D:\AI_CACHE\transformers"
New-Item -ItemType Directory -Force -Path "D:\AI_CACHE\temp"
New-Item -ItemType Directory -Force -Path "D:\scam-court-ai"
```

---

## 2. Recommended: Use the `.env` File (Persists Across Terminals)

Scam Court AI loads `.env` automatically on startup. This is the cleanest way to persist settings across PowerShell, VS Code, and Hugging Face Spaces.

```powershell
cd D:\scam-court-ai

# 1. Copy the template
Copy-Item .env.example .env

# 2. Edit .env with your cache paths
notepad .env
```

Set these values inside `.env`:

```env
SCAM_COURT_BACKEND=heuristic
SCAM_COURT_VISION_BACKEND=none
SCAM_COURT_VISION_MODEL=openbmb/MiniCPM-V-4

HF_HOME=D:\AI_CACHE\huggingface
HUGGINGFACE_HUB_CACHE=D:\AI_CACHE\huggingface\hub
TRANSFORMERS_CACHE=D:\AI_CACHE\huggingface\transformers
TORCH_HOME=D:\AI_CACHE\torch
PIP_CACHE_DIR=D:\AI_CACHE\pip
```

> **Never commit `.env`.** It is already in `.gitignore`. Only `.env.example` is tracked.

**Important:** Restart your terminal or VS Code after editing `.env` so the new values are picked up.

---

## 3. Alternative: Temporary Setup (Current Terminal Only)

Use this if you want to test before editing `.env`:

```powershell
# Move caches to D: for this session only
$env:PIP_CACHE_DIR       = "D:\AI_CACHE\pip"
$env:HF_HOME             = "D:\AI_CACHE\huggingface"
$env:HUGGINGFACE_HUB_CACHE = "D:\AI_CACHE\huggingface\hub"
$env:TRANSFORMERS_CACHE  = "D:\AI_CACHE\transformers"
$env:TORCH_HOME          = "D:\AI_CACHE\torch"
$env:TEMP                = "D:\AI_CACHE\temp"
$env:TMP                 = "D:\AI_CACHE\temp"

# Verify
echo "HF_HOME: $env:HF_HOME"
echo "PIP_CACHE_DIR: $env:PIP_CACHE_DIR"
```

Then continue with [Step 5: Install Dependencies](#5-install-dependencies).

---

## 4. Alternative: Permanent Windows Registry Setup

If you need cache variables set at the **Windows user level** (affecting all apps), run PowerShell **as Administrator**:

```powershell
[Environment]::SetEnvironmentVariable("PIP_CACHE_DIR",       "D:\AI_CACHE\pip",           "User")
[Environment]::SetEnvironmentVariable("HF_HOME",             "D:\AI_CACHE\huggingface",   "User")
[Environment]::SetEnvironmentVariable("HUGGINGFACE_HUB_CACHE", "D:\AI_CACHE\huggingface\hub", "User")
[Environment]::SetEnvironmentVariable("TRANSFORMERS_CACHE",  "D:\AI_CACHE\transformers",  "User")
[Environment]::SetEnvironmentVariable("TORCH_HOME",          "D:\AI_CACHE\torch",         "User")
```

> ⚠️ **Note:** Windows registry changes require a logout/login to fully propagate. The `.env` file approach (Step 2) is usually sufficient and safer.

---

## 5. Recreate .venv on D:

If you already have a `.venv` on C:, delete it and recreate it inside the project folder on D:

```powershell
cd D:\scam-court-ai

# Remove old venv (if it exists on C: or elsewhere)
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# Create new venv inside D:\scam-court-ai
python -m venv .venv

# Activate
.venv\Scripts\Activate.ps1
```

---

## 6. Install Dependencies

With caches redirected to D:, install everything:

```powershell
cd D:\scam-court-ai
.venv\Scripts\Activate.ps1

# Upgrade pip (uses D:\AI_CACHE\pip)
python -m pip install --upgrade pip

# Install Scam Court AI dependencies (uses D:\AI_CACHE\pip)
pip install -r requirements.txt
```

> **First run only:** MiniCPM-V-4 will download ~8–16 GB of model weights to `D:\AI_CACHE\huggingface\hub`. Ensure D: has enough free space.

---

## 7. Run the App

```powershell
cd D:\scam-court-ai
.venv\Scripts\Activate.ps1

# Text-only mode (fast, no model download)
$env:SCAM_COURT_VISION_BACKEND = "none"
python app.py

# With vision (downloads model to D:\AI_CACHE\huggingface on first use)
$env:SCAM_COURT_VISION_BACKEND = "minicpm_v"
python app.py
```

---

## 8. Verify Cache Locations

```powershell
# Check where pip is caching
python -m pip cache dir

# Check where Hugging Face stores models
python -c "import os; print('HF_HOME:', os.getenv('HF_HOME'))"

# Check where transformers caches
python -c "import os; print('TRANSFORMERS_CACHE:', os.getenv('TRANSFORMERS_CACHE'))"

# Check torch home
python -c "import os; print('TORCH_HOME:', os.getenv('TORCH_HOME'))"
```

All paths should point to `D:\AI_CACHE\...`.

---

## 9. Do Not Commit Caches or Models

Your `.gitignore` already protects the repo from committing:

- `.venv/`
- `__pycache__/`
- `*.bin`, `*.safetensors`
- `models/`, `checkpoints/`
- `.env`

**Never** commit:
- Downloaded model weights (`D:\AI_CACHE\huggingface\hub`)
- Pip cache (`D:\AI_CACHE\pip`)
- Your virtual environment (`.venv/`)

---

## Troubleshooting

### "Not enough free disk space to download the file"

- Free up space on D: or use a different drive letter.
- MiniCPM-V-4 needs at least **20 GB free** for model + extraction overhead.

### "pip install fails with permission denied"

- Run PowerShell as Administrator, or
- Use `--user` flag: `pip install --user -r requirements.txt`

### "Environment variable not recognized after reboot"

- Run Step 3 again and ensure you used `"User"` scope.
- Open a **new** PowerShell window after setting variables.

### "Model still downloads to C:\Users\..."

- Double-check that `HF_HOME` is set in the **current** terminal:
  ```powershell
  echo $env:HF_HOME
  ```
- If empty, re-run Step 2 (temporary) or Step 3 (permanent).

### "Gradio says port 7860 is in use"

- Kill the old process or use a different port:
  ```powershell
  $env:PORT = "7862"
  python app.py
  ```

---

## Quick Reference Table

| Variable | D: Path | Purpose |
|----------|---------|---------|
| `PIP_CACHE_DIR` | `D:\AI_CACHE\pip` | pip download cache |
| `HF_HOME` | `D:\AI_CACHE\huggingface` | Hugging Face config + tokens |
| `HUGGINGFACE_HUB_CACHE` | `D:\AI_CACHE\huggingface\hub` | Model weights cache |
| `TRANSFORMERS_CACHE` | `D:\AI_CACHE\transformers` | Transformers model cache |
| `TORCH_HOME` | `D:\AI_CACHE\torch` | PyTorch hub + datasets |
| `TEMP` / `TMP` | `D:\AI_CACHE\temp` | Windows temp files |

---

## Status

✅ **Ready for D:-drive deployment.**
