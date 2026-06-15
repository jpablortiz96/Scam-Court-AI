# Chrome Companion Prototype

## What It Does

The Scam Court AI Chrome Companion adds one context-menu command:

> Take this to Scam Court

When a user explicitly selects text and chooses that command, the extension
sends only the selected text to the configured Scam Court Gradio endpoint. It
then injects a small Shield panel into the active tab with:

- `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK`;
- risk score;
- safest immediate action;
- visible evidence summary;
- a button to open the full Scam Court Space.

If the API request fails, the panel returns:

> VERIFY FIRST - could not analyze automatically. Do not click links or share codes.

The prototype never converts an API failure into a low-risk result.

## Privacy Model

The extension is designed around explicit consent:

- **User-triggered only:** analysis starts only after the context-menu click.
- **Selected text only:** Chrome supplies the highlighted text to the service worker.
- **No background monitoring:** there is no persistent content script or DOM observer.
- **No automatic message reading:** the extension does not scan WhatsApp, Gmail, or marketplace pages.
- **No selection storage:** selected message text is not written to extension storage.
- **Minimal browser permissions:** no history, cookies, bookmarks, clipboard, or web-request access.

`content.js` and `styles.css` are injected into the active tab only when the
user invokes the command. The content script renders the result; it does not
read the page or selection.

## Install in Chrome Developer Mode

1. Clone or download the repository.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the `chrome_companion` directory.
6. Optionally pin **Scam Court AI Companion** to the toolbar.

This is a prototype and is not packaged for the Chrome Web Store.

## Configure the Space URL

Open the extension popup and set the Scam Court URL. The default is:

```text
https://huggingface.co/spaces/build-small-hackathon/scam-court-ai
```

The extension derives the application host:

```text
https://build-small-hackathon-scam-court-ai.hf.space
```

It then calls the named Gradio endpoint:

```text
POST /gradio_api/call/analyze_text
GET  /gradio_api/call/analyze_text/{event_id}
```

For local testing, use:

```text
http://localhost:7860
```

The prototype permits public Hugging Face Space hosts and local development
hosts. It does not accept or store authentication tokens.

## API Bridge

The Gradio endpoint is registered as `api_name="analyze_text"` and accepts one
text input. It returns:

```json
{
  "verdict": "VERIFY FIRST",
  "risk_score": 40,
  "recommended_action": "Do not click the link. Open the official carrier website or app manually.",
  "trusted_contact_script": "I received a delivery message with a link...",
  "evidence_summary": [
    "Package delivery message with action link",
    "Contains a link or action request"
  ],
  "report_id": "scr-example"
}
```

The bridge uses the configured text backend and existing risk policy. It does
not invoke MiniCPM-V because browser selection is text-only.

Empty input and backend exceptions return a score-35 `VERIFY FIRST` fallback.

## Test Workflows

Use synthetic text, not real personal messages.

### WhatsApp Web-style test

Select:

```text
Hi Mom, this is my new number. Please Zelle me $450 right now.
```

Expected result: `STOP`.

### Gmail-style test

Select:

```text
FedEx delivery failed. Update your preferences at https://fedex-track.xyz/update
```

Expected result: `VERIFY FIRST`.

### Marketplace-style test

Select:

```text
I cannot meet in person. Send a security deposit today and my courier will collect it.
```

Expected result: `STOP`.

### Benign control

Select:

```text
Are we still meeting for coffee at 3?
```

Expected result: `LOW VISIBLE RISK`, with the normal-caution limitation.

## Limitations

- The full Court button opens the Space but does not prefill the selected text.
- The prototype analyzes text only; screenshot analysis remains in the Space.
- It requires a reachable public Space or local app.
- Chrome internal pages do not allow extension script injection.
- The endpoint is unauthenticated and intended for public prototype use.
- No rate limiting, enterprise policy, localization, or Chrome Web Store packaging is included.

## Future Production Considerations

- explicit runtime host-permission requests for self-hosted endpoints;
- encrypted local configuration and managed enterprise policy;
- rate limiting and abuse controls;
- accessibility and localization review;
- signed releases and a formal privacy policy;
- automated browser tests across Chrome versions;
- transfer to a full Court view without placing sensitive text in a URL;
- optional local-only endpoint as the default production mode.
