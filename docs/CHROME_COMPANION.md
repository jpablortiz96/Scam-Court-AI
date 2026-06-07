# 🧩 Chrome Companion Mode (Mocked)

> This document describes the planned Chrome extension companion for Scam Court AI. **No extension code exists yet.** This is a design specification for future implementation.

---

## Concept

A lightweight browser companion that lets users put **any selected text** on trial without leaving the page.

**Use cases:**
- Highlight a suspicious WhatsApp Web message → instant verdict
- Select a shady Gmail subject line → risk score overlay
- Right-click any selected text on any page → "Analyze with Scam Court AI"

---

## Architecture (Planned)

```
┌─────────────────┐     selected text      ┌──────────────────────┐
│  Chrome Extension │  ──────────────────>  │  Scam Court AI       │
│  (content script) │   POST /analyze       │  (local or HF Space) │
│  (popup UI)       │  <──────────────────  │  CourtroomEngine     │
└─────────────────┘     JSON report         └──────────────────────┘
```

### Components

1. **Content Script**
   - Injects a floating "Put on Trial" button when text is selected.
   - Captures selected text + page origin.
   - Sends message to background worker.

2. **Background Service Worker**
   - Receives text from content script.
   - Calls the Scam Court AI endpoint (local `http://localhost:7860` or public HF Space).
   - Returns the `CourtroomReport` JSON.

3. **Popup / Overlay UI**
   - Renders a miniature version of the courtroom:
     - Risk score circle (top)
     - Verdict badge
     - Collapsible role cards
     - Safe reply + copy button
   - Styled to match the dark gold courtroom theme.

---

## API Endpoint (Planned)

```http
POST /analyze
Content-Type: application/json

{
  "text": "URGENT: Your account has been suspended...",
  "source": "chrome_extension"
}
```

**Response:** Full `CourtroomReport` v1 schema (see `docs/API_CONTRACT.md`).

---

## UI Mock

```
┌─────────────────────────────┐
│  ⚖️ Scam Court AI          │
│  ─────────────────────────  │
│         ┌─────┐             │
│        /  88   \            │
│        \  SCAM /            │
│         └─────┘             │
│  ─────────────────────────  │
│  [Detective] [Judge] [Clerk]│
│  ─────────────────────────  │
│  Safe Reply:                │
│  "Do not reply..."          │
│  [Copy] [Close]             │
└─────────────────────────────┘
```

---

## Privacy Design

- **Default mode:** Local analysis only. Extension talks to `localhost:7860`.
- **Remote mode (opt-in):** User can point to a trusted HF Space endpoint.
- No selected text is logged or transmitted to third parties.

---

## Files to Create (Future)

```
extension/
├── manifest.json          # Chrome V3 manifest
├── content.js             # Text selection + floating button
├── background.js          # API caller
├── popup.html             # Mini courtroom UI
├── popup.css              # Dark gold theme (subset of app.py CSS)
└── icons/                 # 16/32/48/128 px courtroom icons
```

---

## Open Questions

1. Should the extension support **image** analysis (screenshots of scam messages) via MiniCPM-V later?
2. Should we add a **batch mode** for analyzing entire chat histories?
3. Should the safe reply include a **one-click copy** formatted for WhatsApp Web / Gmail?

---

## Status

🚧 **Not yet implemented.** This document serves as the specification for post-hackathon development.
