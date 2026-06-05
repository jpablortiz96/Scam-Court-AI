# 📝 Field Notes — Scam Court AI

## Design Decisions

### Why a courtroom metaphor?
Normal scam detectors feel like antivirus software — clinical, alarmist, easy to ignore.
A courtroom makes the user a *juror*. They see both sides. They understand *why* something is risky.
That understanding builds lasting habits, not just one-time clicks.

### Why heuristic first?
- Hackathon MVPs die when the model download takes 10 minutes.
- Heuristics give instant feedback and a working UI on day one.
- The `CourtroomEngine` interface is model-agnostic; swapping in SmolLM3-3B is a single method override.

### Why no API calls?
- Privacy: users paste sensitive messages. Sending them to OpenAI is a liability.
- Cost: zero running cost means zero barrier to adoption.
- Hackathon rules: some prizes explicitly reward local / small-model solutions.

### Why Gradio?
- Hugging Face Spaces natively supports it.
- Custom CSS is powerful enough for a premium feel.
- Python-native, so our engine code lives in the same process.

---

## Architecture Evolution

### Phase 1 — Heuristic MVP (today)
- `courtroom/engine.py` runs regex + scoring.
- UI is pure Gradio + custom CSS.
- Runs on CPU in <50ms.

### Phase 2 — Tiny Model Judge
- Add `courtroom/backends/smol_lm_backend.py`.
- Load `HuggingFaceTB/SmolLM3-3B` with `transformers` + `accelerate` CPU offloading.
- Fallback to heuristic if model load fails.

### Phase 3 — Vision Witness
- Add `courtroom/backends/minicpmv_backend.py`.
- Accept image uploads in Gradio.
- MiniCPM-V extracts text + visual red flags from screenshots.

### Phase 4 — Agent Swarm
- Each persona becomes a model call or tool-using agent.
- Prosecutor and defender debate via structured generation.
- Judge synthesizes with chain-of-thought.

### Phase 5 — Modal Batch Eval
- `modal_eval.py` runs evaluation_cases.json on GPUs.
- Generates leaderboard + PR curve for model comparison.

---

## Known Limitations

1. **Heuristics miss novel scams.**
   - Mitigation: rapid model swap capability.
2. **No image input yet.**
   - Mitigation: Phase 3 roadmap with MiniCPM-V.
3. **English-first patterns.**
   - Mitigation: Unicode-aware regex, future multilingual model.
4. **Score is not calibrated probability.**
   - Mitigation: evaluation_cases.json will drive calibration in Phase 2.

---

## Windows + VS Code + PowerShell Notes

- Use `python -m venv .venv` then `.venv\Scripts\Activate.ps1`.
- If execution policy blocks scripts, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
- Run with `python app.py`.
- Formatting: Black (`pip install black`), run `black .` before commits.
- Linting: Ruff (`pip install ruff`), run `ruff check .`.
