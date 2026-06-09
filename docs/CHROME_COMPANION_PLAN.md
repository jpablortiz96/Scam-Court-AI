# 🧩 Chrome Companion Plan

> Privacy-first browser companion for Scam Court AI. **No extension code exists yet.** This document is the implementation specification.

---

## Core Principles

1. **User-triggered only.** Nothing runs until the user explicitly asks for analysis.
2. **Selected text only.** Only the text the user highlights is transmitted.
3. **No background surveillance.** No DOM mutation observers, no persistent content scripts, no keystroke logging.
4. **Minimal permissions.** Only `activeTab`, `contextMenus`, and optional `host` permissions for a self-hosted endpoint.
5. **Privacy-first.** Local analysis by default. Remote endpoint is opt-in and user-configurable.
6. **Elder-safety first.** The first view is the Shield Mode verdict, not the full courtroom. Everything is large type and high contrast.

---

## User Flow

```
1. User highlights suspicious text on any web page
   (WhatsApp Web, Gmail, Facebook Marketplace, etc.)

2. User right-clicks → "Check with Scam Court AI"

3. Extension sends selected text to local Scam Court AI backend
   (default: http://localhost:7861)
   Body: { text: selected, source: "chrome_extension" }

4. A floating panel appears near the selection showing, in order:
   a. Shield verdict in large type (STOP / VERIFY FIRST / LOW VISIBLE RISK)
   b. Immediate action sentence
   c. "Read this to someone you trust" script with a Copy button
   d. Optional: "See Court Explanation" link to expand the full trial

5. User clicks Close or clicks outside the panel
```

---

## Permissions Justification

| Permission | Why | When |
|------------|-----|------|
| `activeTab` | Read the current tab's selected text | Only during user right-click |
| `contextMenus` | Add "Check with Scam Court AI" to right-click menu | At install time |
| `storage` | Remember user's endpoint preference | At install time |
| `host` (optional) | Connect to a self-hosted HF Space | Only if user opts in |

**Not requested:** `history`, `bookmarks`, `cookies`, `webRequest`, `<all_urls>`, `clipboardWrite` (we use `navigator.clipboard` inside the page context).

---

## Architecture

```
extension/
├── manifest.json          # V3 manifest; minimal permission set
├── background.js          # Context-menu handler + API caller
├── content.js             # Injects floating panel; captures selection
├── panel.html             # Mini Shield + Court UI (dark gold theme)
├── panel.css              # Subset of app.py CSS, ~18 KB
├── panel.js               # Renders report JSON into panel
└── icons/
    ├── 16.png
    ├── 32.png
    ├── 48.png
    └── 128.png
```

### Background Service Worker

```javascript
chrome.contextMenus.create({
  id: "analyze-selection",
  title: "Check with Scam Court AI",
  contexts: ["selection"]
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "analyze-selection") return;
  const endpoint = await getUserEndpoint(); // default: localhost:7861
  const report = await fetch(`${endpoint}/api/analyze`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text: info.selectionText, source: "chrome_extension"})
  }).then(r => r.json());
  chrome.tabs.sendMessage(tab.id, {action: "show-panel", report});
});
```

### Content Script

```javascript
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "show-panel") {
    renderFloatingPanel(request.report);
  }
});
```

### Panel Rendering — Shield First

The panel consumes the **Integration Contract v2.1** JSON directly. The default view uses Shield Mode fields:

- `report.shield_verdict` → large headline with color block
- `report.immediate_action` → one-sentence directive
- `report.trusted_contact_script` → copyable sentence for a caregiver
- `report.scenario_tags` → subtle tags for context

An expandable section exposes the Court Mode view:

- `report.risk_score` → circular gauge
- `report.verdict` → badge
- `report.detective_report.evidence` → Detective tab
- `report.safety_reply` + `report.next_steps` → Clerk tab
- `report.report_id` → footer for traceability

---

## Privacy Design

| Threat | Mitigation |
|--------|------------|
| Text leaked to cloud | Default endpoint is `localhost`. Remote is opt-in. |
| Extension logs history | No history API access. No persistent storage of messages. |
| Selection sent without consent | Only sent on explicit right-click + "Check with Scam Court AI". |
| Panel persists and reveals content | Panel auto-closes on click-outside after 60 seconds. |
| Fingerprinting via endpoint calls | No unique identifiers in requests beyond `report_id` generated server-side. |

---

## Open Questions

1. Should the panel support **image upload** (screenshot of scam message) for future MiniCPM-V integration?
2. Should we add a **"Report to Family Safety Dashboard"** button for multi-user caregiving?
3. Should the safe-reply include **platform-specific formatting** (WhatsApp markdown vs Gmail plain text)?

---

## Status

🚧 **Specification complete. Awaiting post-hackathon implementation.**
