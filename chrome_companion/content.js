(() => {
  if (globalThis.__scamCourtCompanionLoaded) {
    return;
  }
  globalThis.__scamCourtCompanionLoaded = true;

  const PANEL_ID = "scam-court-companion-panel";
  let activeRequestId = null;
  let dismissedRequestId = null;

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type === "SCAM_COURT_LOADING") {
      activeRequestId = message.requestId || null;
      dismissedRequestId = null;
      renderLoading(message.selectedText || "");
    }
    if (message?.type === "SCAM_COURT_RESULT") {
      if (
        message.requestId &&
        (message.requestId !== activeRequestId ||
          message.requestId === dismissedRequestId)
      ) {
        return;
      }
      renderResult(
        message.result,
        message.spaceUrl,
        message.selectedText || ""
      );
    }
  });

  function createPanel() {
    document.getElementById(PANEL_ID)?.remove();

    const panel = document.createElement("aside");
    panel.id = PANEL_ID;
    panel.className = "scam-court-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-live", "polite");
    panel.setAttribute("aria-label", "Scam Court AI selected-text result");
    document.documentElement.appendChild(panel);
    return panel;
  }

  function renderLoading(selectedText) {
    const panel = createPanel();
    panel.innerHTML = `
      <div class="scam-court-panel__header">
        <strong>Scam Court AI</strong>
        <button class="scam-court-panel__close" type="button" aria-label="Close">×</button>
      </div>
      <div class="scam-court-panel__privacy">User-triggered only · Selected text only · No background monitoring</div>
      <section class="scam-court-panel__selected" hidden>
        <span>Analyzing selection</span>
        <p></p>
      </section>
      <div class="scam-court-panel__loading">Analyzing the selected text…</div>
    `;
    setSelectedText(panel, selectedText);
    bindClose(panel);
  }

  function renderResult(result, spaceUrl, selectedText) {
    const panel = createPanel();
    const verdict = result?.verdict || "VERIFY FIRST";
    const kind =
      verdict === "STOP"
        ? "stop"
        : verdict === "LOW VISIBLE RISK"
          ? "safe"
          : "verify";
    const evidence = Array.isArray(result?.evidence_summary)
      ? result.evidence_summary
      : [];

    panel.innerHTML = `
      <div class="scam-court-panel__header">
        <strong>Scam Court AI</strong>
        <button class="scam-court-panel__close" type="button" aria-label="Close">×</button>
      </div>
      <div class="scam-court-panel__privacy">User-triggered only · Selected text only · No background monitoring</div>
      <section class="scam-court-panel__selected" hidden>
        <span>Analyzed selection</span>
        <p></p>
      </section>
      <div class="scam-court-panel__verdict scam-court-panel__verdict--${kind}"></div>
      <div class="scam-court-panel__score"></div>
      <section class="scam-court-panel__section">
        <span>Safest action</span>
        <p class="scam-court-panel__action"></p>
      </section>
      <section class="scam-court-panel__section scam-court-panel__evidence-section">
        <span>Visible evidence</span>
        <ul class="scam-court-panel__evidence"></ul>
      </section>
      <button class="scam-court-panel__court-button" type="button">Open full Court explanation</button>
      <p class="scam-court-panel__notice">No messages are read unless you explicitly send selected text to Scam Court.</p>
    `;

    setSelectedText(panel, selectedText);
    panel.querySelector(".scam-court-panel__verdict").textContent = verdict;
    panel.querySelector(".scam-court-panel__score").textContent =
      `Risk score: ${Number(result?.risk_score ?? 35)}/100`;
    panel.querySelector(".scam-court-panel__action").textContent =
      result?.recommended_action ||
      "Could not analyze automatically. Do not click links or share codes.";

    const evidenceList = panel.querySelector(".scam-court-panel__evidence");
    for (const item of evidence.slice(0, 4)) {
      const listItem = document.createElement("li");
      listItem.textContent = String(item);
      evidenceList.appendChild(listItem);
    }
    if (!evidence.length) {
      panel.querySelector(".scam-court-panel__evidence-section").hidden = true;
    }

    panel
      .querySelector(".scam-court-panel__court-button")
      .addEventListener("click", () => {
        chrome.runtime.sendMessage({
          type: "OPEN_FULL_COURT",
          spaceUrl
        });
      });
    bindClose(panel);
  }

  function setSelectedText(panel, selectedText) {
    const section = panel.querySelector(".scam-court-panel__selected");
    const text = String(selectedText || "").trim();
    if (!section || !text) {
      return;
    }
    section.hidden = false;
    section.querySelector("p").textContent =
      text.length > 220 ? `${text.slice(0, 217)}…` : text;
  }

  function bindClose(panel) {
    panel
      .querySelector(".scam-court-panel__close")
      .addEventListener("click", () => {
        panel.remove();
        dismissedRequestId = activeRequestId;
      });
  }
})();
