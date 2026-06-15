const MENU_ID = "take-to-scam-court";
const DEFAULT_SPACE_URL =
  "https://huggingface.co/spaces/build-small-hackathon/scam-court-ai";
let requestSequence = 0;

const SAFE_FALLBACK = {
  verdict: "VERIFY FIRST",
  risk_score: 35,
  recommended_action:
    "Could not analyze automatically. Do not click links or share codes. Verify through an official channel.",
  trusted_contact_script:
    "Scam Court could not analyze this automatically. Can you help me verify it before I act?",
  evidence_summary: ["Automatic analysis was unavailable."],
  report_id: null,
  fallback: true
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: "Take this to Scam Court",
      contexts: ["selection"]
    });
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID || !tab?.id) {
    return;
  }

  const selectedText = (info.selectionText || "").trim();
  const requestId = `${tab.id}-${Date.now()}-${++requestSequence}`;
  await injectCompanion(tab.id);
  await sendToTab(tab.id, {
    type: "SCAM_COURT_LOADING",
    requestId,
    selectedText
  });

  if (!selectedText) {
    await showResult(
      tab.id,
      SAFE_FALLBACK,
      DEFAULT_SPACE_URL,
      requestId,
      selectedText
    );
    return;
  }

  const { spaceUrl = DEFAULT_SPACE_URL } = await chrome.storage.local.get(
    "spaceUrl"
  );

  try {
    const result = await analyzeSelectedText(spaceUrl, selectedText);
    await showResult(
      tab.id,
      normalizeResult(result),
      spaceUrl,
      requestId,
      selectedText
    );
  } catch (error) {
    console.warn("Scam Court Companion analysis failed:", error);
    await showResult(
      tab.id,
      SAFE_FALLBACK,
      spaceUrl,
      requestId,
      selectedText
    );
  }
});

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type !== "OPEN_FULL_COURT") {
    return;
  }

  const target = normalizeSpacePageUrl(message.spaceUrl || DEFAULT_SPACE_URL);
  chrome.tabs.create({ url: target });
});

async function injectCompanion(tabId) {
  await chrome.scripting.insertCSS({
    target: { tabId },
    files: ["styles.css"]
  });
  await chrome.scripting.executeScript({
    target: { tabId },
    files: ["content.js"]
  });
}

async function sendToTab(tabId, message) {
  try {
    await chrome.tabs.sendMessage(tabId, message);
  } catch (error) {
    console.warn("Scam Court Companion could not update the page:", error);
  }
}

async function showResult(tabId, result, spaceUrl, requestId, selectedText) {
  await sendToTab(tabId, {
    type: "SCAM_COURT_RESULT",
    result,
    spaceUrl: normalizeSpacePageUrl(spaceUrl),
    requestId,
    selectedText
  });
}

function normalizeSpacePageUrl(value) {
  const raw = String(value || DEFAULT_SPACE_URL).trim().replace(/\/+$/, "");
  return raw || DEFAULT_SPACE_URL;
}

function resolveApiBase(spaceUrl) {
  const pageUrl = normalizeSpacePageUrl(spaceUrl);
  const parsed = new URL(pageUrl);
  const match = parsed.pathname.match(/^\/spaces\/([^/]+)\/([^/]+)/);

  if (parsed.hostname === "huggingface.co" && match) {
    const owner = match[1].toLowerCase().replace(/[^a-z0-9-]/g, "-");
    const space = match[2].toLowerCase().replace(/[^a-z0-9-]/g, "-");
    return `https://${owner}-${space}.hf.space`;
  }

  return `${parsed.protocol}//${parsed.host}${parsed.pathname}`.replace(
    /\/+$/,
    ""
  );
}

async function analyzeSelectedText(spaceUrl, selectedText) {
  const apiBase = resolveApiBase(spaceUrl);
  const startResponse = await fetch(
    `${apiBase}/gradio_api/call/analyze_text`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: [selectedText] })
    }
  );

  if (!startResponse.ok) {
    throw new Error(`API start failed with HTTP ${startResponse.status}`);
  }

  const startPayload = await startResponse.json();
  if (!startPayload.event_id) {
    throw new Error("Gradio API did not return an event id.");
  }

  const resultResponse = await fetch(
    `${apiBase}/gradio_api/call/analyze_text/${startPayload.event_id}`
  );
  if (!resultResponse.ok) {
    throw new Error(`API result failed with HTTP ${resultResponse.status}`);
  }

  const eventStream = await resultResponse.text();
  const dataLines = eventStream
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data: "))
    .map((line) => line.slice(6));

  if (!dataLines.length) {
    throw new Error("Gradio API returned no result data.");
  }

  const payload = JSON.parse(dataLines[dataLines.length - 1]);
  return Array.isArray(payload) ? payload[0] : payload;
}

function normalizeResult(result) {
  if (!result || typeof result !== "object") {
    return SAFE_FALLBACK;
  }

  const verdict = String(result.verdict || "VERIFY FIRST").toUpperCase();
  return {
    verdict:
      verdict === "STOP" ||
      verdict === "VERIFY FIRST" ||
      verdict === "LOW VISIBLE RISK"
        ? verdict
        : "VERIFY FIRST",
    risk_score: Number.isFinite(Number(result.risk_score))
      ? Number(result.risk_score)
      : 35,
    recommended_action:
      result.recommended_action ||
      "Pause and verify through an official channel before acting.",
    trusted_contact_script: result.trusted_contact_script || "",
    evidence_summary: Array.isArray(result.evidence_summary)
      ? result.evidence_summary
      : [],
    report_id: result.report_id || null,
    fallback: false
  };
}
