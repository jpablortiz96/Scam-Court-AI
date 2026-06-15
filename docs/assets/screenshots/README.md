# Screenshot Proof Pack

These captures use synthetic messages and contain no personal data, credentials,
tokens, private browser tabs, or private repository paths.

Files:

- `01-shield-vision-witness.png` - Shield verdict and Vision Witness summary.
- `02-vision-witness-extracted-text.png` - MiniCPM-V status, type, confidence,
  extracted text, and visual clues.
- `03-court-mode.png` - five court roles and evidence panel.
- `04-suspicious-call.png` - high-risk call factors and `STOP` action.
- `05-chrome-companion.png` - selected-text browser overlay.
- `06-companion-preview.png` - in-app WhatsApp-style integration preview.

## Provenance

The first four app captures and the Companion Preview use the project's real
Gradio renderers. The Vision Witness data came from an actual local
`openbmb/MiniCPM-V-4` analysis of a synthetic delivery-message image.

The Chrome Companion capture executes the committed `content.js` and
`styles.css` against a synthetic page and supplies the same stable API result
shape used by the service worker.

The screenshot input and capture harness were temporary ignored artifacts and
are not part of the application runtime.
