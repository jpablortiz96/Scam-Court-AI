(() => {
  if (globalThis.__scamCourtCompanionLoaded) {
    return;
  }
  globalThis.__scamCourtCompanionLoaded = true;

  const PANEL_ID = "scam-court-companion-panel";

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type === "SCAM_COURT_LOADING") {
      renderLoading();
    }
    if (message?.type === "SCAM_COURT_RESULT") {
      renderResult(message.result, message.spaceUrl);
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

  function renderLoading() {
    const panel = createPanel();
    panel.innerHTML = `
      <div class="scam-court-panel__header">
        <strong>Scam Court AI</strong>
        <button class="scam-court-panel__close" type="button" aria-label="Close">×</button>
      </div>
      <div class="scam-court-panel__privacy">Selected text only · User-triggered</div>
      <div class="scam-court-panel__loading">Analyzing the selected text…</div>
    `;
    bindClose(panel);
  }

  function renderResult(result, spaceUrl) {
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

  function bindClose(panel) {
    panel
      .querySelector(".scam-court-panel__close")
      .addEventListener("click", () => panel.remove());
  }
})();
