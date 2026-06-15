# Scam Court AI Chrome Companion Prototype

This Manifest V3 extension demonstrates explicit selected-text analysis inside
a browser workflow. It is a local prototype for demos and review, not a Chrome
Web Store production release.

## Privacy Contract

- User-triggered only.
- Selected text only.
- No background page monitoring.
- No automatic message reading.
- No history, cookie, bookmark, clipboard, or web-request permissions.
- Selected text is not stored by the extension.
- If analysis fails, the result is `VERIFY FIRST`, never low risk.

There is no persistent content script. `content.js` and `styles.css` are
injected into the active tab only after the user selects text and clicks the
context-menu command.

## Install

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the repository's `chrome_companion` folder.
5. Pin **Scam Court AI Companion** if desired.

## Use

1. Select suspicious text on a normal webpage.
2. Right-click the selection.
3. Choose **Take this to Scam Court**.
4. Review the Shield verdict and safest action in the injected panel.
5. Choose **Open full Court explanation** to open the configured Space.

The extension cannot inject into Chrome internal pages such as
`chrome://extensions`.

## Configuration

The popup stores one configurable Space URL. The default is:

```text
https://huggingface.co/spaces/build-small-hackathon/scam-court-ai
```

The background worker converts a Hugging Face Space page URL to its
corresponding `hf.space` application host and calls:

```text
POST /gradio_api/call/analyze_text
GET  /gradio_api/call/analyze_text/{event_id}
```

Local development is also supported:

```text
http://localhost:7860
```

Only Hugging Face and local HTTP hosts are included in the prototype's host
permissions.

## API Result

The named Gradio endpoint returns:

```json
{
  "verdict": "VERIFY FIRST",
  "risk_score": 40,
  "recommended_action": "Do not click the link...",
  "trusted_contact_script": "I received a delivery message...",
  "evidence_summary": ["Package delivery message with action link"],
  "report_id": "scr-example"
}
```

## Prototype Limitations

- The full Court button opens the Space but does not transfer selected text.
- The extension depends on the Space being public and its Gradio API being reachable.
- Arbitrary self-hosted domains are not included in host permissions.
- The prototype has no image upload path.
- Chrome may suspend the Manifest V3 service worker between requests.
- No Chrome Web Store packaging, icons, localization, or automated browser tests are included.
