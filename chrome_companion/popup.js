const DEFAULT_SPACE_URL =
  "https://huggingface.co/spaces/build-small-hackathon/scam-court-ai";

const input = document.getElementById("space-url");
const status = document.getElementById("status");

initialize();

document.getElementById("save").addEventListener("click", async () => {
  const value = input.value.trim().replace(/\/+$/, "");
  if (!isSupportedUrl(value)) {
    showStatus(
      "Use a Hugging Face Space URL, an hf.space URL, localhost, or 127.0.0.1.",
      true
    );
    return;
  }

  await chrome.storage.local.set({ spaceUrl: value });
  showStatus("Space URL saved.", false);
});

document.getElementById("open-space").addEventListener("click", () => {
  const value = input.value.trim() || DEFAULT_SPACE_URL;
  chrome.tabs.create({ url: value });
});

async function initialize() {
  const { spaceUrl = DEFAULT_SPACE_URL } = await chrome.storage.local.get(
    "spaceUrl"
  );
  input.value = spaceUrl;
}

function isSupportedUrl(value) {
  try {
    const parsed = new URL(value);
    return (
      parsed.protocol === "https:" &&
      (parsed.hostname === "huggingface.co" ||
        parsed.hostname.endsWith(".hf.space")) ||
      parsed.protocol === "http:" &&
      (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1")
    );
  } catch {
    return false;
  }
}

function showStatus(message, isError) {
  status.textContent = message;
  status.classList.toggle("error", isError);
}
