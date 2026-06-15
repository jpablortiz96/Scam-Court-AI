"""Premium, responsive visual system for the Gradio application."""

from __future__ import annotations

import urllib.parse


PAGE_JS = """
() => {
  const setTheme = (theme) => {
    const value = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-sc-theme", value);
    document.body.setAttribute("data-sc-theme", value);
  };
  const setLanguage = (lang) => {
    const value = lang === "es" ? "es" : "en";
    document.documentElement.setAttribute("data-sc-lang", value);
    document.body.setAttribute("data-sc-lang", value);
    document.documentElement.lang = value;
  };
  window.scamCourtSetTheme = setTheme;
  window.scamCourtSetLanguage = setLanguage;
  const syncUiState = () => {
    const marker = document.querySelector("#sc-ui-state");
    setTheme(marker?.dataset?.theme || "dark");
    setLanguage(marker?.dataset?.lang || "en");
  };
  const observer = new MutationObserver(syncUiState);
  observer.observe(document.body, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["data-theme", "data-lang"],
  });
  syncUiState();
}
"""


def _role_background_rules(role_svgs: dict[str, str]) -> str:
    rules: list[str] = []
    for role, svg in role_svgs.items():
        uri = urllib.parse.quote(svg)
        rules.append(
            f"""
.role-btn-{role},
.role-btn-{role} button {{
  background-image: url("data:image/svg+xml;charset=utf-8,{uri}") !important;
  background-position: center 18px !important;
  background-repeat: no-repeat !important;
  background-size: 54px 54px !important;
}}
"""
        )
    return "\n".join(rules)


def build_css(role_svgs: dict[str, str]) -> str:
    role_rules = ""
    return f"""
:root,
html[data-sc-theme="dark"] {{
  color-scheme: dark;
  --sc-bg: #080816;
  --sc-bg-deep: #05050d;
  --sc-surface: rgba(21, 21, 48, 0.82);
  --sc-surface-strong: rgba(27, 27, 60, 0.96);
  --sc-surface-soft: rgba(255, 255, 255, 0.045);
  --sc-border: rgba(191, 186, 255, 0.14);
  --sc-border-strong: rgba(191, 186, 255, 0.25);
  --sc-text: #f7f5ff;
  --sc-text-soft: #c8c5dd;
  --sc-text-muted: #918da9;
  --sc-indigo: #8d83ff;
  --sc-indigo-strong: #7165f4;
  --sc-indigo-soft: rgba(141, 131, 255, 0.15);
  --sc-cyan: #6fe1d2;
  --sc-gold: #f4c76d;
  --sc-danger: #ff727f;
  --sc-danger-bg: rgba(255, 86, 105, 0.13);
  --sc-warning: #ffc465;
  --sc-warning-bg: rgba(255, 177, 65, 0.13);
  --sc-safe: #6ee7a4;
  --sc-safe-bg: rgba(74, 211, 137, 0.12);
  --sc-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
  --sc-shadow-soft: 0 16px 42px rgba(0, 0, 0, 0.22);
  --body-background-fill: var(--sc-bg);
  --background-fill-primary: var(--sc-surface-strong);
  --background-fill-secondary: var(--sc-surface);
  --border-color-primary: var(--sc-border);
  --body-text-color: var(--sc-text);
  --body-text-color-subdued: var(--sc-text-soft);
  --input-background-fill: rgba(8, 8, 22, 0.72);
  --input-border-color: var(--sc-border);
  --button-secondary-background-fill: var(--sc-surface-soft);
  --button-secondary-text-color: var(--sc-text);
}}

html[data-sc-theme="light"],
body:has(#sc-ui-state[data-theme="light"]) {{
  color-scheme: light;
  --sc-bg: #f5f2fb;
  --sc-bg-deep: #ece7f7;
  --sc-surface: rgba(255, 255, 255, 0.88);
  --sc-surface-strong: #ffffff;
  --sc-surface-soft: rgba(44, 32, 91, 0.055);
  --sc-border: rgba(52, 38, 103, 0.13);
  --sc-border-strong: rgba(73, 54, 145, 0.24);
  --sc-text: #201a38;
  --sc-text-soft: #564e70;
  --sc-text-muted: #77708d;
  --sc-indigo: #6256d9;
  --sc-indigo-strong: #5144ca;
  --sc-indigo-soft: rgba(98, 86, 217, 0.12);
  --sc-cyan: #157f7b;
  --sc-gold: #a86c00;
  --sc-danger: #bd3046;
  --sc-danger-bg: rgba(203, 49, 73, 0.09);
  --sc-warning: #9c5b00;
  --sc-warning-bg: rgba(202, 116, 0, 0.1);
  --sc-safe: #147343;
  --sc-safe-bg: rgba(28, 145, 84, 0.09);
  --sc-shadow: 0 24px 60px rgba(57, 43, 108, 0.13);
  --sc-shadow-soft: 0 14px 34px rgba(57, 43, 108, 0.1);
  --body-background-fill: var(--sc-bg);
  --background-fill-primary: var(--sc-surface-strong);
  --background-fill-secondary: var(--sc-surface);
  --border-color-primary: var(--sc-border);
  --body-text-color: var(--sc-text);
  --body-text-color-subdued: var(--sc-text-soft);
  --input-background-fill: #ffffff;
  --input-border-color: var(--sc-border);
  --button-secondary-background-fill: rgba(55, 42, 108, 0.055);
  --button-secondary-text-color: var(--sc-text);
}}

body:has(#sc-ui-state[data-theme="light"]) {{
  color-scheme: light;
}}

html {{
  min-width: 320px;
  background: var(--sc-bg) !important;
}}

.ui-state-marker {{
  display: none !important;
}}

body {{
  min-width: 320px;
  min-height: 100vh;
  overflow-x: hidden;
  background:
    radial-gradient(circle at 12% -5%, rgba(107, 79, 255, 0.24), transparent 32rem),
    radial-gradient(circle at 88% 10%, rgba(44, 198, 190, 0.12), transparent 28rem),
    radial-gradient(circle at 50% 105%, rgba(111, 77, 255, 0.17), transparent 36rem),
    linear-gradient(180deg, var(--sc-bg) 0%, var(--sc-bg-deep) 100%) !important;
  color: var(--sc-text) !important;
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}}

body::before,
body::after {{
  content: "";
  position: fixed;
  z-index: -1;
  width: 34rem;
  height: 34rem;
  border-radius: 999px;
  filter: blur(90px);
  opacity: 0.2;
  pointer-events: none;
  animation: sc-drift 16s ease-in-out infinite alternate;
}}

body::before {{
  top: -18rem;
  left: -12rem;
  background: #684dff;
}}

body::after {{
  right: -16rem;
  bottom: -20rem;
  background: #2eaaa5;
  animation-delay: -7s;
}}

gradio-app {{
  background: transparent !important;
}}

.gradio-container {{
  width: 100% !important;
  max-width: 1320px !important;
  margin: 0 auto !important;
  padding: 0 28px 44px !important;
  background: transparent !important;
}}

.contain,
.wrap {{
  max-width: 100%;
}}

footer {{
  display: none !important;
}}

/* Hero */
#sc-hero {{
  position: relative;
  padding: 68px 20px 34px;
  text-align: center;
  animation: sc-rise 0.65s ease both;
}}

#sc-hero::after {{
  content: "";
  display: block;
  width: min(360px, 72vw);
  height: 1px;
  margin: 28px auto 0;
  background: linear-gradient(90deg, transparent, rgba(167, 157, 255, 0.62), transparent);
}}

#sc-hero h1 {{
  margin: 0;
  color: var(--sc-text);
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.45rem, 5vw, 4.6rem);
  font-weight: 600;
  letter-spacing: -0.055em;
  line-height: 0.98;
  white-space: nowrap;
}}

#sc-hero p {{
  max-width: 680px;
  margin: 17px auto 0;
  color: var(--sc-text-soft);
  font-size: clamp(1rem, 1.5vw, 1.16rem);
  line-height: 1.65;
}}

/* Main navigation */
.mode-tabs .tab-wrapper {{
  position: sticky;
  top: 10px;
  z-index: 30;
  height: auto !important;
  min-height: 72px;
  align-items: center;
  width: min(920px, 100%);
  margin: 0 auto 28px !important;
  padding: 8px !important;
  overflow: visible !important;
  box-sizing: border-box;
  border: 1px solid var(--sc-border) !important;
  border-radius: 18px !important;
  background: color-mix(in srgb, var(--sc-surface-strong) 90%, transparent) !important;
  box-shadow: var(--sc-shadow-soft);
  backdrop-filter: blur(20px);
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] {{
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: center;
  gap: 6px;
  width: 100%;
  min-height: 54px;
  padding: 2px !important;
  overflow: visible !important;
  box-sizing: border-box;
}}

.mode-tabs .tab-wrapper > .overflow-menu {{
  flex: 0 0 auto;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
  min-width: 0 !important;
  min-height: 48px !important;
  align-self: center;
  margin: 0 !important;
  padding: 10px 12px !important;
  overflow: hidden;
  border: 0 !important;
  border-radius: 13px !important;
  background: transparent !important;
  color: var(--sc-text-muted) !important;
  font-size: 0.88rem !important;
  font-weight: 700 !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: background 180ms ease, color 180ms ease, transform 180ms ease !important;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button:hover {{
  color: var(--sc-text) !important;
  background: var(--sc-surface-soft) !important;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button.selected {{
  color: #fff !important;
  background: linear-gradient(135deg, var(--sc-indigo-strong), #766bf2) !important;
  box-shadow: 0 8px 22px rgba(78, 63, 194, 0.28);
}}

/* Section intros and panels */
.mode-intro {{
  margin: 8px 0 24px;
  padding: 0 4px;
  animation: sc-rise 0.45s ease both;
}}

.mode-eyebrow,
.section-kicker {{
  margin-bottom: 8px;
  color: var(--sc-cyan);
  font-size: 0.73rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}}

.mode-intro h2 {{
  max-width: 860px;
  margin: 0;
  color: var(--sc-text);
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.75rem, 3vw, 2.65rem);
  font-weight: 600;
  letter-spacing: -0.035em;
  line-height: 1.08;
}}

.mode-intro p {{
  max-width: 760px;
  margin: 12px 0 0;
  color: var(--sc-text-soft);
  font-size: 1rem;
  line-height: 1.65;
}}

.sc-panel {{
  position: relative;
  min-width: 0;
  padding: 24px !important;
  overflow: hidden;
  border: 1px solid var(--sc-border) !important;
  border-radius: 24px !important;
  background: linear-gradient(145deg, var(--sc-surface), color-mix(in srgb, var(--sc-surface-strong) 82%, transparent)) !important;
  box-shadow: var(--sc-shadow-soft);
  backdrop-filter: blur(20px);
  animation: sc-rise 0.55s ease both;
}}

.sc-panel::before {{
  content: "";
  position: absolute;
  top: 0;
  left: 28px;
  right: 28px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(196, 190, 255, 0.52), transparent);
  pointer-events: none;
}}

.section-label {{
  margin: 0 0 10px;
  color: var(--sc-text);
  font-size: 0.86rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}}

.helper-copy {{
  margin: 8px 0 0;
  color: var(--sc-text-muted);
  font-size: 0.78rem;
  line-height: 1.55;
}}

.quick-label {{
  margin: 20px 0 9px;
  color: var(--sc-text-muted);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}}

/* Inputs and controls */
textarea,
input,
[data-testid="textbox"] textarea {{
  border: 1px solid var(--sc-border) !important;
  border-radius: 16px !important;
  background: color-mix(in srgb, var(--sc-bg) 70%, transparent) !important;
  color: var(--sc-text) !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.025);
}}

textarea:focus,
input:focus {{
  border-color: var(--sc-indigo) !important;
  box-shadow: 0 0 0 4px var(--sc-indigo-soft) !important;
}}

textarea::placeholder,
input::placeholder {{
  color: var(--sc-text-muted) !important;
  opacity: 0.9;
}}

.image-input {{
  min-height: 224px !important;
  overflow: hidden;
  border: 1px dashed var(--sc-border-strong) !important;
  border-radius: 18px !important;
  background: color-mix(in srgb, var(--sc-bg) 58%, transparent) !important;
}}

.image-input button {{
  min-height: 44px !important;
}}

.image-input .upload-container button .wrap {{
  color: transparent !important;
  font-size: 0 !important;
}}

.image-input .upload-container button .icon-wrap {{
  display: block !important;
  margin: 0 auto 10px !important;
  color: var(--sc-text-muted) !important;
}}

.image-input .upload-container button .or {{
  display: none !important;
}}

.image-input .upload-container button .wrap::after {{
  content: "Drop a screenshot here or click to upload";
  display: block;
  max-width: 240px;
  color: var(--sc-text-muted);
  font-size: 0.86rem;
  font-weight: 650;
  line-height: 1.5;
  text-align: center;
}}

body:has(#sc-ui-state[data-lang="es"]) .image-input .upload-container button .wrap::after {{
  content: "Suelta una captura aquí o haz clic para subirla";
}}

button.primary,
.primary-btn button {{
  min-height: 50px !important;
  border: 0 !important;
  border-radius: 15px !important;
  background: linear-gradient(135deg, var(--sc-indigo-strong), #8176ff) !important;
  color: #fff !important;
  font-size: 0.94rem !important;
  font-weight: 800 !important;
  box-shadow: 0 12px 28px rgba(80, 65, 200, 0.25) !important;
  transition: transform 180ms ease, filter 180ms ease, box-shadow 180ms ease !important;
}}

button.primary:hover,
.primary-btn button:hover {{
  filter: brightness(1.08);
  transform: translateY(-2px);
  box-shadow: 0 16px 34px rgba(80, 65, 200, 0.33) !important;
}}

button.secondary,
.secondary-btn button {{
  min-height: 48px !important;
  border: 1px solid var(--sc-border) !important;
  border-radius: 15px !important;
  background: var(--sc-surface-soft) !important;
  color: var(--sc-text-soft) !important;
  font-weight: 700 !important;
  transition: border-color 180ms ease, background 180ms ease, color 180ms ease, transform 180ms ease !important;
}}

button.secondary:hover,
.secondary-btn button:hover {{
  border-color: var(--sc-border-strong) !important;
  background: var(--sc-indigo-soft) !important;
  color: var(--sc-text) !important;
  transform: translateY(-1px);
}}

.example-grid {{
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px !important;
}}

.example-grid .example-btn,
.example-btn button {{
  min-height: 40px !important;
  justify-content: flex-start !important;
  border: 1px solid var(--sc-border) !important;
  border-radius: 12px !important;
  background: transparent !important;
  color: var(--sc-text-soft) !important;
  font-size: 0.79rem !important;
  font-weight: 650 !important;
  text-align: left !important;
}}

.example-grid .example-btn:hover,
.example-btn button:hover {{
  border-color: var(--sc-border-strong) !important;
  background: var(--sc-indigo-soft) !important;
  color: var(--sc-text) !important;
}}

/* Shield result */
.shield-empty,
.call-empty,
.court-empty {{
  display: grid;
  min-height: 310px;
  place-content: center;
  padding: 36px;
  border: 1px solid var(--sc-border);
  border-radius: 24px;
  background:
    radial-gradient(circle at 50% 15%, var(--sc-indigo-soft), transparent 48%),
    var(--sc-surface);
  color: var(--sc-text-soft);
  text-align: center;
  box-shadow: var(--sc-shadow-soft);
}}

.empty-emblem {{
  display: grid;
  width: 68px;
  height: 68px;
  margin: 0 auto 18px;
  place-items: center;
  border: 1px solid var(--sc-border-strong);
  border-radius: 22px;
  background: var(--sc-indigo-soft);
  color: var(--sc-indigo);
}}

.empty-emblem svg {{
  width: 34px;
  height: 34px;
}}

.empty-title {{
  color: var(--sc-text);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.45rem;
  font-weight: 600;
}}

.empty-body {{
  max-width: 520px;
  margin: 10px auto 0;
  font-size: 0.94rem;
  line-height: 1.65;
}}

.shield-card {{
  position: relative;
  padding: clamp(26px, 4vw, 46px);
  overflow: hidden;
  border: 1px solid;
  border-radius: 28px;
  box-shadow: var(--sc-shadow);
  animation: sc-verdict 0.52s cubic-bezier(0.2, 0.78, 0.2, 1) both;
}}

.shield-card::after {{
  content: "";
  position: absolute;
  z-index: 0;
  width: 360px;
  height: 360px;
  top: -230px;
  right: -130px;
  border-radius: 999px;
  background: currentColor;
  filter: blur(80px);
  opacity: 0.13;
  pointer-events: none;
}}

.shield-card.stop {{
  border-color: color-mix(in srgb, var(--sc-danger) 35%, transparent);
  background: linear-gradient(145deg, var(--sc-danger-bg), var(--sc-surface-strong));
  color: var(--sc-danger);
}}

.shield-card.verify {{
  border-color: color-mix(in srgb, var(--sc-warning) 36%, transparent);
  background: linear-gradient(145deg, var(--sc-warning-bg), var(--sc-surface-strong));
  color: var(--sc-warning);
}}

.shield-card.safe {{
  border-color: color-mix(in srgb, var(--sc-safe) 34%, transparent);
  background: linear-gradient(145deg, var(--sc-safe-bg), var(--sc-surface-strong));
  color: var(--sc-safe);
}}

.shield-card > * {{
  position: relative;
  z-index: 1;
}}

.verdict-topline {{
  display: flex;
  align-items: center;
  gap: 15px;
}}

.verdict-icon {{
  display: grid;
  flex: 0 0 auto;
  width: 56px;
  height: 56px;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 18px;
  background: color-mix(in srgb, currentColor 9%, transparent);
}}

.verdict-icon svg {{
  width: 30px;
  height: 30px;
}}

.verdict-label {{
  color: currentColor;
  font-size: clamp(1.8rem, 4vw, 3.2rem);
  font-weight: 900;
  letter-spacing: -0.045em;
  line-height: 1;
}}

.verdict-score {{
  margin-top: 7px;
  color: var(--sc-text-soft);
  font-size: 0.83rem;
  font-weight: 750;
}}

.action-block {{
  margin-top: 26px;
  padding-top: 22px;
  border-top: 1px solid var(--sc-border);
}}

.result-label {{
  margin-bottom: 8px;
  color: var(--sc-text-muted);
  font-size: 0.69rem;
  font-weight: 850;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}}

.action-copy {{
  max-width: 760px;
  color: var(--sc-text);
  font-size: clamp(1.08rem, 2vw, 1.35rem);
  font-weight: 720;
  line-height: 1.55;
}}

.trusted-card {{
  margin-top: 20px;
  padding: 18px 20px;
  border: 1px solid var(--sc-border);
  border-radius: 18px;
  background: var(--sc-surface-soft);
  color: var(--sc-text-soft);
  font-size: 0.96rem;
  line-height: 1.62;
}}

.court-hint {{
  margin-top: 16px;
  color: var(--sc-text-muted);
  font-size: 0.82rem;
}}

.shield-guide {{
  margin-top: 18px;
  padding: 20px;
  border: 1px solid var(--sc-border);
  border-radius: 22px;
  background: var(--sc-surface);
  box-shadow: var(--sc-shadow-soft);
}}

.guide-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}}

.guide-card {{
  min-width: 0;
  padding: 13px;
  border: 1px solid var(--sc-border);
  border-radius: 15px;
  background: var(--sc-surface-soft);
  color: var(--sc-text-muted);
  font-size: 0.75rem;
  line-height: 1.5;
}}

.guide-state {{
  margin-bottom: 6px;
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.04em;
}}

.guide-card.stop .guide-state {{ color: var(--sc-danger); }}
.guide-card.verify .guide-state {{ color: var(--sc-warning); }}
.guide-card.safe .guide-state {{ color: var(--sc-safe); }}

/* Vision Witness */
.vision-card {{
  margin-top: 18px;
  padding: 20px;
  border: 1px solid var(--sc-border);
  border-radius: 22px;
  background: var(--sc-surface);
  box-shadow: var(--sc-shadow-soft);
  animation: sc-rise 0.45s ease both;
}}

.vision-heading {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}}

.vision-title {{
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--sc-text);
  font-weight: 820;
}}

.vision-title svg {{
  width: 22px;
  height: 22px;
  color: var(--sc-cyan);
}}

.status-pill {{
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 5px 10px;
  border: 1px solid var(--sc-border);
  border-radius: 999px;
  color: var(--sc-text-soft);
  font-size: 0.68rem;
  font-weight: 800;
}}

.status-pill.ok {{
  border-color: color-mix(in srgb, var(--sc-safe) 32%, transparent);
  background: var(--sc-safe-bg);
  color: var(--sc-safe);
}}

.status-pill.warn {{
  border-color: color-mix(in srgb, var(--sc-warning) 32%, transparent);
  background: var(--sc-warning-bg);
  color: var(--sc-warning);
}}

.vision-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}}

.vision-field {{
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--sc-border);
  border-radius: 15px;
  background: var(--sc-surface-soft);
  color: var(--sc-text-soft);
  font-size: 0.88rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
}}

.vision-field.wide {{
  grid-column: 1 / -1;
}}

.vision-field ul {{
  margin: 7px 0 0;
  padding-left: 19px;
}}

.vision-privacy {{
  margin-top: 12px;
  color: var(--sc-text-muted);
  font-size: 0.72rem;
  line-height: 1.5;
}}

/* Court */
.case-summary {{
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  padding: 24px;
  border: 1px solid var(--sc-border);
  border-radius: 24px;
  background: var(--sc-surface);
  box-shadow: var(--sc-shadow-soft);
}}

.score-orbit {{
  display: grid;
  width: 132px;
  height: 132px;
  place-content: center;
  border: 8px solid var(--sc-indigo-soft);
  border-top-color: var(--score-color, var(--sc-indigo));
  border-radius: 999px;
  color: var(--sc-text);
  text-align: center;
  transform: rotate(12deg);
}}

.score-orbit > div {{
  transform: rotate(-12deg);
}}

.score-number {{
  font-size: 2.2rem;
  font-weight: 900;
  letter-spacing: -0.05em;
  line-height: 1;
}}

.score-caption {{
  margin-top: 5px;
  color: var(--sc-text-muted);
  font-size: 0.62rem;
  font-weight: 850;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}}

.case-verdict {{
  color: var(--score-color, var(--sc-text));
  font-size: clamp(1.45rem, 3vw, 2.25rem);
  font-weight: 900;
  letter-spacing: -0.035em;
}}

.case-rationale {{
  margin-top: 9px;
  color: var(--sc-text-soft);
  font-size: 0.94rem;
  line-height: 1.6;
}}

.case-meta {{
  margin-top: 12px;
  color: var(--sc-text-muted);
  font-size: 0.76rem;
  font-weight: 750;
}}

.role-section-label {{
  margin: 24px 0 11px;
  color: var(--sc-text);
  font-size: 0.82rem;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.role-selector {{
  display: grid !important;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px !important;
  overflow: visible !important;
}}

.role-card {{
  position: relative;
  min-width: 0 !important;
  padding: 13px 10px 9px !important;
  overflow: hidden;
  border: 1px solid var(--sc-border) !important;
  border-radius: 19px !important;
  background: var(--sc-surface) !important;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease !important;
}}

.role-card:hover {{
  border-color: var(--sc-border-strong) !important;
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.16);
  transform: translateY(-3px);
}}

.role-card:has(.role-btn.primary) {{
  border-color: var(--sc-indigo) !important;
  background: var(--sc-indigo-soft) !important;
  box-shadow: inset 0 0 0 1px rgba(141, 131, 255, 0.18), 0 12px 30px rgba(71, 57, 174, 0.18);
}}

.role-selector-emblem {{
  display: grid;
  width: 52px;
  height: 52px;
  margin: 0 auto 3px;
  place-items: center;
}}

.role-selector-emblem svg {{
  width: 50px;
  height: 50px;
}}

.role-btn {{
  min-width: 0 !important;
}}

.role-btn,
.role-btn button {{
  position: relative;
  min-height: 58px !important;
  padding: 8px 5px 27px !important;
  overflow: hidden;
  border: 0 !important;
  border-radius: 12px !important;
  background: transparent !important;
  color: var(--sc-text) !important;
  font-size: 0.82rem !important;
  font-weight: 820 !important;
  line-height: 1.15 !important;
  box-shadow: none !important;
  transition: color 180ms ease, background 180ms ease !important;
}}

.role-btn::after,
.role-btn button::after {{
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 10px;
  color: var(--sc-text-muted);
  font-size: 0.56rem;
  font-weight: 750;
  letter-spacing: 0.03em;
  line-height: 1.25;
}}

body:has(#sc-ui-state[data-lang="en"]) .role-btn-detective::after,
body:has(#sc-ui-state[data-lang="en"]) .role-btn-detective button::after {{ content: "Sharp, observant, factual"; }}
body:has(#sc-ui-state[data-lang="en"]) .role-btn-prosecutor::after,
body:has(#sc-ui-state[data-lang="en"]) .role-btn-prosecutor button::after {{ content: "Builds the risk case"; }}
body:has(#sc-ui-state[data-lang="en"]) .role-btn-defender::after,
body:has(#sc-ui-state[data-lang="en"]) .role-btn-defender button::after {{ content: "Tests innocent explanations"; }}
body:has(#sc-ui-state[data-lang="en"]) .role-btn-judge::after,
body:has(#sc-ui-state[data-lang="en"]) .role-btn-judge button::after {{ content: "Weighs the full record"; }}
body:has(#sc-ui-state[data-lang="en"]) .role-btn-clerk::after,
body:has(#sc-ui-state[data-lang="en"]) .role-btn-clerk button::after {{ content: "Turns findings into action"; }}
body:has(#sc-ui-state[data-lang="es"]) .role-btn-detective::after,
body:has(#sc-ui-state[data-lang="es"]) .role-btn-detective button::after {{ content: "Agudo, observador, factual"; }}
body:has(#sc-ui-state[data-lang="es"]) .role-btn-prosecutor::after,
body:has(#sc-ui-state[data-lang="es"]) .role-btn-prosecutor button::after {{ content: "Construye el caso de riesgo"; }}
body:has(#sc-ui-state[data-lang="es"]) .role-btn-defender::after,
body:has(#sc-ui-state[data-lang="es"]) .role-btn-defender button::after {{ content: "Prueba explicaciones inocentes"; }}
body:has(#sc-ui-state[data-lang="es"]) .role-btn-judge::after,
body:has(#sc-ui-state[data-lang="es"]) .role-btn-judge button::after {{ content: "Evalúa todo el expediente"; }}
body:has(#sc-ui-state[data-lang="es"]) .role-btn-clerk::after,
body:has(#sc-ui-state[data-lang="es"]) .role-btn-clerk button::after {{ content: "Convierte hallazgos en acciones"; }}

.role-btn:hover,
.role-btn button:hover {{
  z-index: 2;
  background: var(--sc-surface-soft) !important;
  box-shadow: none !important;
  transform: none;
}}

.role-btn.primary,
.role-btn button.primary {{
  background: var(--sc-indigo-strong) !important;
  color: #fff !important;
  box-shadow: none !important;
}}

.role-panel {{
  margin-top: 12px;
  padding: 26px;
  border: 1px solid var(--sc-border);
  border-radius: 24px;
  background: var(--sc-surface);
  box-shadow: var(--sc-shadow-soft);
  animation: sc-role 0.35s ease both;
}}

.role-header {{
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--sc-border);
}}

.role-avatar {{
  display: grid;
  flex: 0 0 auto;
  width: 64px;
  height: 64px;
  place-items: center;
  border-radius: 20px;
  background: var(--sc-indigo-soft);
}}

.role-avatar svg {{
  width: 56px;
  height: 56px;
}}

.role-title {{
  color: var(--sc-text);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.42rem;
  font-weight: 600;
}}

.role-subtitle {{
  margin-top: 4px;
  color: var(--sc-text-muted);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}}

.role-body {{
  padding-top: 18px;
  color: var(--sc-text-soft);
  font-size: 0.96rem;
  line-height: 1.72;
}}

.role-body strong {{
  color: var(--sc-text);
}}

.role-body ul,
.role-body ol {{
  margin: 10px 0 0;
  padding-left: 21px;
}}

.role-body li {{
  margin: 8px 0;
}}

/* Suspicious call */
.call-factor {{
  display: block !important;
  margin: 8px 0 !important;
  padding: 15px 16px !important;
  border: 1px solid var(--sc-border) !important;
  border-radius: 16px !important;
  background: var(--sc-surface-soft) !important;
  transition: border-color 170ms ease, background 170ms ease, transform 170ms ease !important;
}}

.call-factor:hover {{
  border-color: var(--sc-border-strong) !important;
  transform: translateY(-1px);
}}

.call-factor:has(input:checked) {{
  border-color: var(--sc-indigo) !important;
  background: var(--sc-indigo-soft) !important;
  box-shadow: inset 0 0 0 1px rgba(141, 131, 255, 0.16);
}}

.call-factor label {{
  color: var(--sc-text-soft) !important;
  font-size: 0.96rem !important;
  font-weight: 680 !important;
  line-height: 1.45 !important;
}}

.call-factor:has(input:checked) label {{
  color: var(--sc-text) !important;
}}

.call-factor input {{
  width: 22px !important;
  height: 22px !important;
  accent-color: var(--sc-indigo) !important;
}}

.warning-tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}}

.warning-tag {{
  padding: 7px 10px;
  border: 1px solid var(--sc-border);
  border-radius: 999px;
  background: var(--sc-surface-soft);
  color: var(--sc-text-soft);
  font-size: 0.72rem;
  font-weight: 750;
}}

/* Companion */
.prototype-note {{
  margin-bottom: 16px;
  padding: 11px 14px;
  border: 1px solid var(--sc-border);
  border-radius: 14px;
  background: var(--sc-indigo-soft);
  color: var(--sc-text-soft);
  font-size: 0.78rem;
  line-height: 1.5;
}}

.companion-tabs .tab-wrapper {{
  width: fit-content;
  margin-bottom: 14px !important;
  padding: 4px !important;
  border: 1px solid var(--sc-border) !important;
  border-radius: 14px !important;
  background: var(--sc-surface) !important;
}}

.companion-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
  min-height: 42px !important;
  border-radius: 11px !important;
  color: var(--sc-text-muted) !important;
  font-size: 0.8rem !important;
  font-weight: 750 !important;
}}

.companion-tabs .tab-wrapper > .tab-container[role="tablist"] button.selected {{
  background: var(--sc-indigo-soft) !important;
  color: var(--sc-text) !important;
}}

.companion-shell {{
  max-width: 620px;
  margin: 0 auto;
  overflow: hidden;
  border: 1px solid var(--sc-border);
  border-radius: 26px;
  background: var(--sc-surface-strong);
  box-shadow: var(--sc-shadow);
  animation: sc-rise 0.45s ease both;
}}

.companion-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 15px 18px;
  border-bottom: 1px solid var(--sc-border);
  color: var(--sc-text);
  font-size: 0.84rem;
  font-weight: 850;
}}

.prototype-badge {{
  padding: 4px 8px;
  border: 1px solid var(--sc-border);
  border-radius: 999px;
  color: var(--sc-text-muted);
  font-size: 0.6rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.conversation {{
  padding: 20px;
  background:
    radial-gradient(circle at 90% 10%, var(--sc-indigo-soft), transparent 52%),
    color-mix(in srgb, var(--sc-bg) 62%, transparent);
}}

.message-card {{
  max-width: 82%;
  padding: 14px 16px;
  border: 1px solid var(--sc-border);
  border-radius: 18px 18px 18px 5px;
  background: var(--sc-surface);
  color: var(--sc-text);
  font-size: 0.91rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
}}

.message-meta {{
  margin-bottom: 6px;
  color: var(--sc-text-muted);
  font-size: 0.67rem;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}}

.companion-result {{
  margin: 16px 20px 20px;
  padding: 18px;
  border: 1px solid var(--sc-border);
  border-radius: 18px;
  background: var(--sc-surface-soft);
}}

.mini-verdict {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--sc-text);
  font-weight: 900;
}}

.mini-score {{
  color: var(--sc-text-muted);
  font-size: 0.74rem;
}}

.safe-reply {{
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--sc-border);
  color: var(--sc-text-soft);
  font-size: 0.86rem;
  line-height: 1.58;
}}

.companion-cta {{
  margin-top: 13px;
  color: var(--sc-cyan);
  font-size: 0.78rem;
  font-weight: 800;
}}

.companion-empty {{
  min-height: 300px;
  padding: 42px 28px;
  border: 1px dashed var(--sc-border-strong);
  border-radius: 24px;
  background: var(--sc-surface);
  color: var(--sc-text-muted);
  text-align: center;
  display: grid;
  place-content: center;
  line-height: 1.65;
}}

/* Utility dock */
.utility-dock {{
  margin-top: 38px !important;
  padding: 22px !important;
  border: 1px solid var(--sc-border) !important;
  border-radius: 26px !important;
  background: color-mix(in srgb, var(--sc-surface-strong) 88%, transparent) !important;
  box-shadow: var(--sc-shadow);
  backdrop-filter: blur(22px);
}}

.utility-dock,
.utility-dock > .styler,
.utility-dock .form {{
  background: transparent !important;
}}

.utility-dock > .row {{
  align-items: center !important;
  justify-content: space-between !important;
  gap: 14px !important;
}}

.utility-dock > .row > .block:first-child {{
  flex: 1 1 300px !important;
}}

.utility-dock > .row > .form {{
  flex: 0 1 460px !important;
  min-width: min(320px, 100%) !important;
}}

.utility-brand {{
  min-width: 260px;
  padding: 5px 0;
}}

.utility-brand-name {{
  color: var(--sc-text);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.2rem;
  font-weight: 650;
}}

.utility-status {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 7px;
  color: var(--sc-text-soft);
  font-size: 0.75rem;
  font-weight: 700;
}}

.status-dot {{
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--sc-safe);
  box-shadow: 0 0 12px color-mix(in srgb, var(--sc-safe) 72%, transparent);
}}

.settings-control {{
  min-width: 170px !important;
  max-width: 220px !important;
}}

.settings-control label {{
  color: var(--sc-text-muted) !important;
  font-size: 0.66rem !important;
  font-weight: 850 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
}}

.settings-control input {{
  min-height: 44px !important;
}}

.utility-accordion {{
  margin-top: 12px !important;
  overflow: hidden;
  border: 1px solid var(--sc-border) !important;
  border-radius: 16px !important;
  background: var(--sc-surface-soft) !important;
}}

.diagnostic-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}}

.diagnostic-item {{
  min-width: 0;
  padding: 13px;
  border: 1px solid var(--sc-border);
  border-radius: 14px;
  background: var(--sc-surface);
}}

.diagnostic-label {{
  color: var(--sc-text-muted);
  font-size: 0.62rem;
  font-weight: 850;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}}

.diagnostic-value {{
  margin-top: 6px;
  color: var(--sc-text);
  font-size: 0.78rem;
  font-weight: 720;
  line-height: 1.4;
  overflow-wrap: anywhere;
}}

.api-card {{
  padding: 4px 2px;
  color: var(--sc-text-soft);
  font-size: 0.88rem;
  line-height: 1.65;
}}

.api-contract {{
  margin-bottom: 9px;
  color: var(--sc-text);
  font-weight: 850;
}}

.footer-tagline {{
  margin-top: 15px;
  color: var(--sc-text-muted);
  font-size: 0.7rem;
  line-height: 1.5;
  text-align: center;
}}

/* Gradio accordion/code cleanup */
.gr-accordion,
.gradio-accordion {{
  border-color: var(--sc-border) !important;
  background: var(--sc-surface) !important;
}}

.json-code textarea,
.json-code code {{
  font-size: 0.78rem !important;
}}

/* Responsive: desktop >=1200, laptop 900-1199, tablet 640-899, mobile <=639 */
@media (max-width: 1199px) {{
  .gradio-container {{
    max-width: 1080px !important;
    padding-inline: 22px !important;
  }}

  .diagnostic-grid {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}

@media (max-width: 899px) {{
  #sc-hero {{
    padding-top: 48px;
  }}

  .mode-tabs .tab-wrapper {{
    position: relative;
    top: auto;
  }}

  .sc-panel {{
    padding: 20px !important;
  }}

  .role-selector {{
    display: flex !important;
    gap: 9px !important;
    padding-bottom: 8px;
    overflow-x: auto !important;
    scroll-snap-type: x proximity;
  }}

  .role-btn {{
    min-width: 0 !important;
  }}

  .role-card {{
    flex: 0 0 148px !important;
    scroll-snap-align: start;
  }}

  .utility-brand {{
    min-width: 100%;
  }}

  .vision-grid {{
    grid-template-columns: 1fr;
  }}

  .vision-field.wide {{
    grid-column: auto;
  }}
}}

@media (max-width: 639px) {{
  .gradio-container {{
    padding: 0 12px 28px !important;
  }}

  #sc-hero {{
    padding: 38px 10px 24px;
  }}

  #sc-hero h1 {{
    font-size: clamp(2.05rem, 10.5vw, 2.65rem);
  }}

  #sc-hero p {{
    font-size: 0.94rem;
  }}

  .mode-tabs .tab-wrapper {{
    gap: 4px;
    margin-bottom: 20px !important;
    padding: 5px !important;
    border-radius: 15px !important;
  }}

  .mode-tabs .tab-wrapper > .tab-container[role="tablist"] {{
    gap: 3px !important;
  }}

  .mode-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
    min-height: 48px !important;
    padding: 7px 4px !important;
    font-size: 0.67rem !important;
    line-height: 1.2 !important;
    white-space: normal !important;
  }}

  .mode-intro {{
    margin-bottom: 18px;
  }}

  .mode-intro p {{
    font-size: 0.91rem;
  }}

  .sc-panel {{
    padding: 16px !important;
    border-radius: 20px !important;
  }}

  .shield-card {{
    padding: 24px 19px;
    border-radius: 22px;
  }}

  .verdict-topline {{
    align-items: flex-start;
  }}

  .verdict-icon {{
    width: 48px;
    height: 48px;
    border-radius: 15px;
  }}

  .trusted-card {{
    padding: 15px;
  }}

  .case-summary {{
    grid-template-columns: 1fr;
    justify-items: center;
    padding: 20px;
    text-align: center;
  }}

  .score-orbit {{
    width: 112px;
    height: 112px;
  }}

  .role-card {{
    flex-basis: 132px !important;
  }}

  .role-btn button {{
    min-height: 58px !important;
  }}

  .role-btn {{
    min-height: 58px !important;
    padding-top: 8px !important;
  }}

  .role-panel {{
    padding: 20px 17px;
  }}

  .role-avatar {{
    width: 54px;
    height: 54px;
    border-radius: 17px;
  }}

  .role-avatar svg {{
    width: 48px;
    height: 48px;
  }}

  .role-title {{
    font-size: 1.2rem;
  }}

  .message-card {{
    max-width: 94%;
  }}

  .utility-dock {{
    padding: 16px !important;
    border-radius: 20px !important;
  }}

  .settings-control {{
    width: 100% !important;
    max-width: none !important;
  }}

  .example-grid {{
    grid-template-columns: 1fr;
  }}

  .diagnostic-grid {{
    grid-template-columns: 1fr;
  }}

  .vision-heading {{
    align-items: flex-start;
    flex-direction: column;
  }}

  #sc-hero,
  .mode-intro {{
    animation: none !important;
  }}

  .guide-grid {{
    grid-template-columns: 1fr;
  }}
}}

@keyframes sc-rise {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes sc-verdict {{
  from {{ opacity: 0; transform: translateY(16px) scale(0.985); }}
  to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}

@keyframes sc-role {{
  from {{ opacity: 0; transform: translateX(8px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes sc-drift {{
  from {{ transform: translate3d(0, 0, 0) scale(0.92); }}
  to {{ transform: translate3d(28px, 18px, 0) scale(1.08); }}
}}

/* Premium refinement layer */
:root,
html[data-sc-theme="dark"],
body:has(#sc-ui-state[data-theme="dark"]) {{
  --sc-bg: #07090d;
  --sc-bg-deep: #030507;
  --sc-surface: rgba(16, 21, 27, 0.9);
  --sc-surface-strong: #121820;
  --sc-surface-soft: rgba(255, 246, 228, 0.05);
  --sc-surface-raised: #182029;
  --sc-border: rgba(235, 211, 171, 0.13);
  --sc-border-strong: rgba(235, 211, 171, 0.25);
  --sc-text: #f5f0e7;
  --sc-text-soft: #c8c0b4;
  --sc-text-muted: #918b82;
  --sc-indigo: #e1ae5d;
  --sc-indigo-strong: #c88731;
  --sc-indigo-soft: rgba(225, 174, 93, 0.12);
  --sc-cyan: #65c9bf;
  --sc-gold: #e1ae5d;
  --sc-danger: #ff747b;
  --sc-danger-bg: rgba(255, 78, 91, 0.12);
  --sc-warning: #efb45c;
  --sc-warning-bg: rgba(226, 151, 48, 0.13);
  --sc-safe: #70d5a0;
  --sc-safe-bg: rgba(74, 190, 126, 0.12);
  --sc-shadow: 0 30px 80px rgba(0, 0, 0, 0.42);
  --sc-shadow-soft: 0 18px 48px rgba(0, 0, 0, 0.28);
  --sc-ring: 0 0 0 4px rgba(225, 174, 93, 0.13);
  --sc-radius-sm: 13px;
  --sc-radius-md: 19px;
  --sc-radius-lg: 27px;
  --sc-radius-xl: 32px;
  --block-background-fill: var(--sc-surface-strong);
  --block-border-color: var(--sc-border);
  --block-label-background-fill: var(--sc-surface-raised);
  --panel-background-fill: var(--sc-surface);
  --input-background-fill: var(--sc-bg-deep);
  --input-border-color: var(--sc-border);
  --button-secondary-background-fill: var(--sc-surface-raised);
  --button-secondary-text-color: var(--sc-text);
}}

html[data-sc-theme="light"],
body:has(#sc-ui-state[data-theme="light"]) {{
  --sc-bg: #f5f0e7;
  --sc-bg-deep: #e9e1d5;
  --sc-surface: rgba(255, 253, 248, 0.91);
  --sc-surface-strong: #fffdf8;
  --sc-surface-soft: rgba(84, 58, 27, 0.055);
  --sc-surface-raised: #ffffff;
  --sc-border: rgba(83, 58, 29, 0.15);
  --sc-border-strong: rgba(127, 82, 29, 0.29);
  --sc-text: #241e18;
  --sc-text-soft: #514940;
  --sc-text-muted: #746c62;
  --sc-indigo: #9d651c;
  --sc-indigo-strong: #8b5312;
  --sc-indigo-soft: rgba(157, 101, 28, 0.11);
  --sc-cyan: #176f69;
  --sc-gold: #9d651c;
  --sc-danger: #b52d3f;
  --sc-danger-bg: rgba(190, 43, 62, 0.08);
  --sc-warning: #8e5200;
  --sc-warning-bg: rgba(184, 106, 0, 0.09);
  --sc-safe: #17683f;
  --sc-safe-bg: rgba(23, 125, 72, 0.08);
  --sc-shadow: 0 28px 70px rgba(77, 55, 27, 0.16);
  --sc-shadow-soft: 0 16px 42px rgba(77, 55, 27, 0.11);
  --sc-ring: 0 0 0 4px rgba(157, 101, 28, 0.12);
  --block-background-fill: var(--sc-surface-strong);
  --block-border-color: var(--sc-border);
  --block-label-background-fill: #f7f0e5;
  --panel-background-fill: var(--sc-surface);
  --input-background-fill: #ffffff;
  --input-border-color: var(--sc-border);
  --button-secondary-background-fill: rgba(84, 58, 27, 0.055);
  --button-secondary-text-color: var(--sc-text);
}}

body {{
  background:
    radial-gradient(circle at 14% -8%, rgba(194, 132, 49, 0.16), transparent 29rem),
    radial-gradient(circle at 92% 8%, rgba(39, 148, 139, 0.11), transparent 27rem),
    linear-gradient(180deg, var(--sc-bg) 0%, var(--sc-bg-deep) 100%) !important;
}}

body::before {{
  top: -22rem;
  left: -15rem;
  background: #bd7726;
  opacity: 0.12;
}}

body::after {{
  right: -18rem;
  bottom: -22rem;
  background: #23857e;
  opacity: 0.11;
}}

html[data-sc-theme="light"] body,
body:has(#sc-ui-state[data-theme="light"]) {{
  background:
    radial-gradient(circle at 9% -2%, rgba(190, 126, 38, 0.15), transparent 30rem),
    radial-gradient(circle at 94% 8%, rgba(49, 139, 130, 0.1), transparent 29rem),
    linear-gradient(180deg, #faf6ef 0%, var(--sc-bg) 48%, var(--sc-bg-deep) 100%) !important;
}}

.gradio-container {{
  max-width: 1280px !important;
  padding: 0 30px 54px !important;
}}

#sc-hero {{
  padding: 74px 20px 40px;
}}

#sc-hero::after {{
  width: min(420px, 76vw);
  margin-top: 30px;
  background: linear-gradient(
    90deg,
    transparent,
    color-mix(in srgb, var(--sc-gold) 55%, transparent),
    transparent
  );
}}

#sc-hero h1 {{
  color: var(--sc-text);
  font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: clamp(2.7rem, 5.1vw, 4.75rem);
  font-weight: 600;
  letter-spacing: -0.048em;
  line-height: 0.96;
  text-shadow: 0 12px 38px rgba(0, 0, 0, 0.22);
}}

#sc-hero p {{
  max-width: 650px;
  margin-top: 19px;
  color: var(--sc-text-soft);
  font-size: clamp(1rem, 1.45vw, 1.13rem);
  line-height: 1.7;
}}

.mode-tabs .tab-wrapper {{
  width: min(870px, 100%);
  margin-bottom: 34px !important;
  padding: 9px !important;
  border-color: var(--sc-border-strong) !important;
  border-radius: 999px !important;
  background:
    linear-gradient(180deg, var(--sc-surface-raised), var(--sc-surface-strong)) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.045) inset,
    var(--sc-shadow-soft);
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] {{
  gap: 7px;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
  display: flex !important;
  min-height: 50px !important;
  align-items: center;
  justify-content: center;
  gap: 9px;
  border-radius: 999px !important;
  color: var(--sc-text-muted) !important;
  font-size: 0.86rem !important;
  letter-spacing: 0.005em;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button::before {{
  content: "";
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border: 1px solid currentColor;
  border-radius: 999px;
  opacity: 0.7;
  transition: background 180ms ease, transform 180ms ease, opacity 180ms ease;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button:hover {{
  background: var(--sc-surface-soft) !important;
  color: var(--sc-text) !important;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button.selected {{
  background: linear-gradient(135deg, #f1c77e, #cf8b32) !important;
  color: #211407 !important;
  box-shadow:
    0 10px 24px rgba(157, 93, 20, 0.24),
    0 1px 0 rgba(255, 255, 255, 0.46) inset;
}}

.mode-tabs .tab-wrapper > .tab-container[role="tablist"] button.selected::before {{
  border-color: #211407;
  background: #211407;
  opacity: 1;
  transform: scale(1.16);
}}

.mode-tabs .tab-wrapper > .overflow-menu {{
  display: none !important;
}}

.mode-intro {{
  max-width: 960px;
  margin: 10px 0 27px;
}}

.mode-eyebrow,
.section-kicker {{
  color: var(--sc-cyan);
  letter-spacing: 0.18em;
}}

.mode-intro h2 {{
  color: var(--sc-text);
  font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: clamp(1.95rem, 3.15vw, 2.85rem);
  font-weight: 600;
  letter-spacing: -0.04em;
}}

.mode-intro p {{
  max-width: 720px;
  color: var(--sc-text-soft);
  line-height: 1.72;
}}

.mode-layout {{
  gap: 22px !important;
  align-items: flex-start !important;
}}

.result-column {{
  min-width: 0 !important;
  gap: 16px !important;
}}

.sc-panel {{
  padding: 26px !important;
  border-color: var(--sc-border) !important;
  border-radius: var(--sc-radius-lg) !important;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--sc-surface-raised) 88%, transparent), var(--sc-surface)) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.045) inset,
    var(--sc-shadow-soft);
}}

.sc-panel::before {{
  left: 34px;
  right: 34px;
  background: linear-gradient(
    90deg,
    transparent,
    color-mix(in srgb, var(--sc-gold) 50%, transparent),
    transparent
  );
}}

.evidence-panel {{
  background:
    radial-gradient(circle at 100% 0, var(--sc-indigo-soft), transparent 46%),
    linear-gradient(145deg, color-mix(in srgb, var(--sc-surface-raised) 90%, transparent), var(--sc-surface)) !important;
}}

.section-label {{
  margin-bottom: 12px;
  font-size: 0.88rem;
  letter-spacing: 0.01em;
}}

.quick-label {{
  margin-top: 22px;
  color: var(--sc-text-muted);
  letter-spacing: 0.15em;
}}

textarea,
input,
[data-testid="textbox"] textarea {{
  border-color: var(--sc-border) !important;
  border-radius: 17px !important;
  background: color-mix(in srgb, var(--sc-bg-deep) 76%, transparent) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.025) inset,
    0 12px 30px rgba(0, 0, 0, 0.08);
}}

html[data-sc-theme="light"] textarea,
html[data-sc-theme="light"] input,
body:has(#sc-ui-state[data-theme="light"]) textarea,
body:has(#sc-ui-state[data-theme="light"]) input {{
  background: rgba(255, 255, 255, 0.82) !important;
}}

#shield-message,
#court-message,
#companion-message {{
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}}

textarea:focus,
input:focus {{
  border-color: var(--sc-gold) !important;
  box-shadow: var(--sc-ring) !important;
}}

.image-input {{
  min-height: 208px !important;
  border-color: var(--sc-border-strong) !important;
  border-radius: 19px !important;
  background:
    radial-gradient(circle at 50% 25%, var(--sc-indigo-soft), transparent 45%),
    color-mix(in srgb, var(--sc-bg-deep) 75%, transparent) !important;
}}

button.primary,
.primary-btn button {{
  min-height: 52px !important;
  border-radius: 15px !important;
  background: linear-gradient(135deg, #f1c77e 0%, #d08a31 100%) !important;
  color: #211407 !important;
  box-shadow:
    0 13px 30px rgba(157, 93, 20, 0.24),
    0 1px 0 rgba(255, 255, 255, 0.45) inset !important;
}}

button.primary:hover,
.primary-btn button:hover {{
  filter: brightness(1.04) saturate(1.04);
  box-shadow:
    0 17px 38px rgba(157, 93, 20, 0.31),
    0 1px 0 rgba(255, 255, 255, 0.5) inset !important;
}}

button:focus-visible,
textarea:focus-visible,
input:focus-visible,
[role="tab"]:focus-visible {{
  outline: 2px solid var(--sc-gold) !important;
  outline-offset: 3px !important;
}}

button.secondary,
.secondary-btn button {{
  border-color: var(--sc-border) !important;
  background: color-mix(in srgb, var(--sc-surface-raised) 80%, transparent) !important;
  color: var(--sc-text-soft) !important;
}}

button.secondary:hover,
.secondary-btn button:hover {{
  border-color: var(--sc-border-strong) !important;
  background: var(--sc-indigo-soft) !important;
  color: var(--sc-text) !important;
}}

.example-grid {{
  gap: 9px !important;
}}

.example-grid .example-btn,
.example-btn button {{
  min-height: 42px !important;
  border-radius: 13px !important;
  background: rgba(0, 0, 0, 0.04) !important;
}}

.shield-empty,
.call-empty,
.court-empty {{
  min-height: 338px;
  padding: 42px;
  border-color: var(--sc-border);
  border-radius: var(--sc-radius-lg);
  background:
    radial-gradient(circle at 50% 12%, var(--sc-indigo-soft), transparent 43%),
    linear-gradient(145deg, var(--sc-surface-raised), var(--sc-surface));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.04) inset,
    var(--sc-shadow-soft);
}}

.empty-emblem {{
  position: relative;
  width: 72px;
  height: 72px;
  margin-bottom: 21px;
  border-color: var(--sc-border-strong);
  border-radius: 999px;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.09), transparent 35%),
    var(--sc-indigo-soft);
  color: var(--sc-gold);
  box-shadow: 0 0 0 8px color-mix(in srgb, var(--sc-indigo-soft) 65%, transparent);
}}

.empty-title {{
  color: var(--sc-text);
  font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: 1.55rem;
}}

.shield-card {{
  padding: clamp(29px, 4vw, 48px);
  border-radius: var(--sc-radius-xl);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.045) inset,
    var(--sc-shadow);
}}

.shield-card::before {{
  content: "";
  position: absolute;
  top: 26px;
  bottom: 26px;
  left: 0;
  width: 3px;
  border-radius: 0 999px 999px 0;
  background: currentColor;
  opacity: 0.8;
}}

.verdict-icon {{
  width: 60px;
  height: 60px;
  border-radius: 999px;
  box-shadow: 0 0 0 7px color-mix(in srgb, currentColor 7%, transparent);
}}

.verdict-label {{
  font-size: clamp(2rem, 4.2vw, 3.35rem);
}}

.action-block {{
  margin-top: 29px;
  padding-top: 25px;
}}

.trusted-card {{
  border-radius: var(--sc-radius-md);
  background: color-mix(in srgb, var(--sc-surface-raised) 78%, transparent);
}}

.shield-guide {{
  margin-top: 0;
  padding: 21px;
  border-radius: 23px;
  background: linear-gradient(145deg, var(--sc-surface-raised), var(--sc-surface));
}}

.guide-card {{
  position: relative;
  min-height: 104px;
  padding: 15px 15px 15px 17px;
  border-radius: 15px;
  background: color-mix(in srgb, var(--sc-surface-raised) 76%, transparent);
}}

.guide-card::before {{
  content: "";
  position: absolute;
  top: 14px;
  bottom: 14px;
  left: 0;
  width: 2px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.72;
}}

.guide-card.stop {{ color: var(--sc-danger); }}
.guide-card.verify {{ color: var(--sc-warning); }}
.guide-card.safe {{ color: var(--sc-safe); }}
.guide-card > div:last-child {{ color: var(--sc-text-soft); }}

.vision-card {{
  border-radius: 23px;
  background: linear-gradient(145deg, var(--sc-surface-raised), var(--sc-surface));
}}

.case-summary {{
  gap: 25px;
  padding: 27px;
  border-radius: var(--sc-radius-lg);
  background:
    radial-gradient(circle at 0 50%, var(--sc-indigo-soft), transparent 38%),
    linear-gradient(145deg, var(--sc-surface-raised), var(--sc-surface));
}}

.score-orbit {{
  width: 126px;
  height: 126px;
  border: 7px solid color-mix(in srgb, var(--score-color, var(--sc-gold)) 19%, var(--sc-surface));
  border-top-color: var(--score-color, var(--sc-gold));
  border-right-color: color-mix(in srgb, var(--score-color, var(--sc-gold)) 58%, var(--sc-surface));
  transform: none;
  box-shadow:
    0 0 0 1px var(--sc-border),
    0 16px 34px rgba(0, 0, 0, 0.16);
}}

.score-orbit > div {{
  transform: none;
}}

.case-verdict {{
  font-size: clamp(1.55rem, 3vw, 2.35rem);
}}

.role-section-label {{
  margin-top: 28px;
  color: var(--sc-text-muted);
  font-size: 0.74rem;
  letter-spacing: 0.15em;
}}

.role-selector {{
  gap: 12px !important;
}}

.role-card {{
  min-height: 174px;
  padding: 14px 11px 10px !important;
  border-radius: 21px !important;
  background:
    linear-gradient(160deg, color-mix(in srgb, var(--sc-surface-raised) 92%, transparent), var(--sc-surface)) !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.035) inset;
}}

.role-card:hover {{
  border-color: var(--sc-border-strong) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.04) inset,
    0 20px 38px rgba(0, 0, 0, 0.2);
  transform: translateY(-4px);
}}

.role-card:has(.role-btn.primary),
.role-card:has(button.primary) {{
  border-color: color-mix(in srgb, var(--sc-gold) 72%, transparent) !important;
  background:
    radial-gradient(circle at 50% 0, var(--sc-indigo-soft), transparent 52%),
    linear-gradient(160deg, var(--sc-surface-raised), var(--sc-surface)) !important;
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--sc-gold) 22%, transparent) inset,
    0 17px 38px rgba(119, 73, 17, 0.2);
}}

.role-selector-emblem {{
  width: 66px;
  height: 66px;
  margin-bottom: 2px;
  border-radius: 999px;
  background: radial-gradient(circle, var(--sc-indigo-soft), transparent 68%);
  filter: drop-shadow(0 10px 18px rgba(0, 0, 0, 0.22));
}}

.role-selector-emblem svg {{
  width: 62px;
  height: 62px;
}}

.role-btn,
.role-btn button {{
  min-height: 72px !important;
  padding: 10px 4px 32px !important;
  color: var(--sc-text) !important;
  font-size: 0.84rem !important;
}}

.role-btn::after,
.role-btn button::after {{
  bottom: 10px;
  color: var(--sc-text-muted);
  font-size: 0.57rem;
  letter-spacing: 0.015em;
}}

.role-btn.primary,
.role-btn button.primary {{
  background: transparent !important;
  color: var(--sc-gold) !important;
  box-shadow: none !important;
}}

.role-btn.primary::before,
.role-btn button.primary::before {{
  content: "";
  position: absolute;
  top: 0;
  left: 50%;
  width: 22px;
  height: 2px;
  border-radius: 999px;
  background: var(--sc-gold);
  transform: translateX(-50%);
}}

.role-panel {{
  margin-top: 15px;
  padding: 29px;
  border-radius: var(--sc-radius-lg);
  background:
    radial-gradient(circle at 0 0, var(--sc-indigo-soft), transparent 34%),
    linear-gradient(145deg, var(--sc-surface-raised), var(--sc-surface));
}}

.role-header {{
  gap: 18px;
  padding-bottom: 21px;
}}

.role-avatar {{
  width: 70px;
  height: 70px;
  border: 1px solid var(--sc-border-strong);
  border-radius: 999px;
  background: var(--sc-surface-strong);
  box-shadow: 0 0 0 7px var(--sc-indigo-soft);
}}

.role-title {{
  font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: 1.55rem;
}}

.role-body {{
  padding-top: 21px;
  font-size: 0.98rem;
  line-height: 1.78;
}}

.call-panel {{
  background:
    radial-gradient(circle at 100% 0, rgba(255, 116, 123, 0.075), transparent 45%),
    linear-gradient(145deg, color-mix(in srgb, var(--sc-surface-raised) 90%, transparent), var(--sc-surface)) !important;
}}

.call-factor {{
  position: relative;
  margin: 9px 0 !important;
  padding: 17px 18px !important;
  border-radius: 17px !important;
  background: color-mix(in srgb, var(--sc-surface-raised) 78%, transparent) !important;
}}

.call-factor:hover {{
  border-color: var(--sc-border-strong) !important;
  background: var(--sc-surface-raised) !important;
}}

.call-factor:has(input:checked) {{
  border-color: color-mix(in srgb, var(--sc-gold) 68%, transparent) !important;
  background:
    linear-gradient(90deg, var(--sc-indigo-soft), color-mix(in srgb, var(--sc-surface-raised) 82%, transparent)) !important;
  box-shadow:
    3px 0 0 var(--sc-gold) inset,
    0 0 0 1px color-mix(in srgb, var(--sc-gold) 12%, transparent);
}}

.call-factor label {{
  font-size: 0.98rem !important;
  line-height: 1.5 !important;
}}

.call-factor input {{
  accent-color: var(--sc-gold) !important;
}}

.prototype-note {{
  width: fit-content;
  margin-bottom: 18px;
  padding: 9px 13px;
  border-color: var(--sc-border-strong);
  border-radius: 999px;
  background: var(--sc-indigo-soft);
  color: var(--sc-text-soft);
}}

.companion-tabs .tab-wrapper {{
  width: 100%;
  margin-bottom: 16px !important;
  padding: 5px !important;
  border-radius: 16px !important;
  background: linear-gradient(180deg, var(--sc-surface-raised), var(--sc-surface)) !important;
}}

.companion-tabs .tab-wrapper > .tab-container[role="tablist"] {{
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  width: 100%;
  gap: 5px;
}}

.companion-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
  min-width: 0 !important;
  border-radius: 12px !important;
}}

.companion-tabs .tab-wrapper > .tab-container[role="tablist"] button.selected {{
  background: var(--sc-indigo-soft) !important;
  color: var(--sc-gold) !important;
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sc-gold) 22%, transparent) inset;
}}

.companion-shell {{
  max-width: 680px;
  border-color: var(--sc-border-strong);
  border-radius: 29px;
  background: linear-gradient(160deg, var(--sc-surface-raised), var(--sc-surface-strong));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.045) inset,
    var(--sc-shadow);
}}

.companion-header {{
  min-height: 58px;
  padding: 15px 20px;
  background: color-mix(in srgb, var(--sc-surface-raised) 86%, transparent);
}}

.platform-name {{
  display: inline-flex;
  align-items: center;
  gap: 9px;
}}

.platform-name::before {{
  content: "";
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: var(--platform-color, var(--sc-cyan));
  box-shadow: 0 0 13px color-mix(in srgb, var(--platform-color, var(--sc-cyan)) 66%, transparent);
}}

.platform-whatsapp {{ --platform-color: #58c58a; }}
.platform-sms {{ --platform-color: #63a8e8; }}
.platform-marketplace {{ --platform-color: #e2a552; }}

.prototype-badge {{
  border-color: var(--sc-border);
  background: var(--sc-surface-soft);
}}

.conversation {{
  min-height: 174px;
  padding: 24px;
  background:
    radial-gradient(circle at 92% 5%, color-mix(in srgb, var(--platform-color, var(--sc-cyan)) 11%, transparent), transparent 50%),
    color-mix(in srgb, var(--sc-bg-deep) 68%, transparent);
}}

.message-card {{
  padding: 16px 18px;
  border-radius: 19px 19px 19px 6px;
  background: var(--sc-surface-raised);
  box-shadow: 0 13px 30px rgba(0, 0, 0, 0.13);
}}

.message-placeholder {{
  border-style: dashed;
  color: var(--sc-text-muted);
}}

.companion-result {{
  margin: 18px 22px 22px;
  padding: 20px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--sc-surface-raised) 78%, transparent);
}}

.companion-result-empty {{
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}}

.empty-review-icon {{
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border: 1px solid var(--sc-border-strong);
  border-radius: 999px;
  background: var(--sc-indigo-soft);
  color: var(--sc-gold);
}}

.empty-review-icon svg {{
  width: 26px;
  height: 26px;
}}

.companion-empty-title {{
  color: var(--sc-text);
  font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: 1.2rem;
  font-weight: 600;
}}

.companion-empty-copy {{
  margin-top: 5px;
  color: var(--sc-text-soft);
  font-size: 0.83rem;
  line-height: 1.55;
}}

.companion-empty-foot {{
  padding: 0 22px 22px;
  color: var(--sc-text-muted);
  font-size: 0.73rem;
  line-height: 1.55;
  text-align: center;
}}

.companion-preview-column {{
  align-self: stretch;
}}

.utility-dock {{
  margin-top: 52px !important;
  padding: 24px !important;
  border-color: var(--sc-border-strong) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(circle at 0 0, var(--sc-indigo-soft), transparent 36%),
    linear-gradient(145deg, color-mix(in srgb, var(--sc-surface-raised) 92%, transparent), var(--sc-surface-strong)) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.045) inset,
    var(--sc-shadow);
}}

.utility-topbar {{
  gap: 18px !important;
}}

.utility-topbar > .form {{
  flex: 0 1 470px !important;
  gap: 8px !important;
  padding: 8px !important;
  border: 1px solid var(--sc-border) !important;
  border-radius: 20px !important;
  background: var(--sc-surface-soft) !important;
}}

.utility-brand {{
  display: flex;
  min-width: 280px;
  align-items: center;
  gap: 14px;
  padding: 4px 0;
}}

.utility-brand-mark {{
  display: grid;
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--sc-border-strong);
  border-radius: 999px;
  background: var(--sc-indigo-soft);
  color: var(--sc-gold);
  box-shadow: 0 0 0 7px color-mix(in srgb, var(--sc-indigo-soft) 55%, transparent);
}}

.utility-brand-mark svg {{
  width: 26px;
  height: 26px;
}}

.utility-brand-name {{
  font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: 1.22rem;
}}

.utility-status {{
  margin-top: 5px;
}}

.utility-privacy {{
  margin-top: 5px;
  color: var(--sc-text-muted);
  font-size: 0.67rem;
  line-height: 1.45;
}}

.settings-control {{
  min-width: 0 !important;
  max-width: none !important;
  padding: 3px 5px !important;
  border: 0 !important;
  border-radius: 14px !important;
  background: transparent !important;
  box-shadow: none !important;
}}

.settings-control label {{
  padding-inline: 3px;
  color: var(--sc-text-muted) !important;
}}

.settings-control input {{
  min-height: 42px !important;
  border-radius: 12px !important;
  background: var(--sc-surface-strong) !important;
}}

.utility-accordion {{
  margin-top: 13px !important;
  border-color: var(--sc-border) !important;
  border-radius: 17px !important;
  background: color-mix(in srgb, var(--sc-surface-raised) 72%, transparent) !important;
}}

.utility-accordion:hover {{
  border-color: var(--sc-border-strong) !important;
}}

.utility-accordion button {{
  color: var(--sc-text) !important;
}}

.diagnostic-grid {{
  gap: 11px;
}}

.diagnostic-item {{
  padding: 15px;
  border-radius: 15px;
  background: var(--sc-surface-strong);
}}

.api-card {{
  padding: 8px 5px 6px;
}}

.json-code,
.json-code .cm-editor,
.json-code .cm-scroller {{
  max-height: 430px !important;
}}

.api-contract {{
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
}}

.api-status-dot {{
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--sc-safe);
  box-shadow: 0 0 12px color-mix(in srgb, var(--sc-safe) 65%, transparent);
}}

.api-copy {{
  max-width: 880px;
}}

.api-meta {{
  margin-top: 8px;
  color: var(--sc-text-muted);
  font-size: 0.79rem;
}}

.api-export-hint {{
  margin-top: 11px;
  color: var(--sc-cyan);
  font-size: 0.81rem;
  font-weight: 780;
}}

.footer-tagline {{
  margin-top: 19px;
  color: var(--sc-text-muted);
}}

html[data-sc-theme="light"] .sc-panel,
html[data-sc-theme="light"] .shield-empty,
html[data-sc-theme="light"] .call-empty,
html[data-sc-theme="light"] .court-empty,
html[data-sc-theme="light"] .shield-guide,
html[data-sc-theme="light"] .case-summary,
html[data-sc-theme="light"] .role-panel,
html[data-sc-theme="light"] .companion-shell,
body:has(#sc-ui-state[data-theme="light"]) .sc-panel,
body:has(#sc-ui-state[data-theme="light"]) .shield-empty,
body:has(#sc-ui-state[data-theme="light"]) .call-empty,
body:has(#sc-ui-state[data-theme="light"]) .court-empty,
body:has(#sc-ui-state[data-theme="light"]) .shield-guide,
body:has(#sc-ui-state[data-theme="light"]) .case-summary,
body:has(#sc-ui-state[data-theme="light"]) .role-panel,
body:has(#sc-ui-state[data-theme="light"]) .companion-shell {{
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    var(--sc-shadow-soft);
}}

@media (max-width: 899px) {{
  .gradio-container {{
    padding-inline: 20px !important;
  }}

  .mode-layout {{
    gap: 18px !important;
  }}

  .role-card {{
    flex-basis: 154px !important;
  }}

  .utility-topbar {{
    align-items: stretch !important;
  }}

  .utility-topbar > .form {{
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }}
}}

@media (max-width: 639px) {{
  .gradio-container {{
    padding: 0 13px 30px !important;
  }}

  #sc-hero {{
    padding: 42px 9px 27px;
  }}

  #sc-hero h1 {{
    font-size: clamp(2.1rem, 9.8vw, 2.5rem);
    white-space: nowrap;
  }}

  #sc-hero p {{
    max-width: 310px;
    font-size: 0.92rem;
  }}

  .mode-tabs .tab-wrapper {{
    display: flex !important;
    align-items: center;
    gap: 5px;
    padding: 7px !important;
    overflow: visible !important;
    border-radius: 18px !important;
  }}

  .mode-tabs .tab-wrapper > .tab-container[role="tablist"] {{
    flex: 1 1 auto;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    align-items: center;
    row-gap: 5px;
    padding: 2px !important;
    overflow: visible !important;
  }}

  .mode-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
    display: flex !important;
    min-height: 46px !important;
    padding: 7px 3px !important;
    gap: 0;
    border-radius: 13px !important;
    font-size: 0.66rem !important;
    line-height: 1.15 !important;
  }}

  .mode-tabs .tab-wrapper > .tab-container[role="tablist"] button::before {{
    display: none;
  }}

  .mode-tabs .tab-wrapper > .overflow-menu {{
    display: flex !important;
    flex: 0 0 48px;
  }}

  .mode-tabs .tab-wrapper > .overflow-menu > button {{
    width: 48px !important;
    min-width: 48px !important;
    min-height: 46px !important;
    border: 0 !important;
    border-radius: 13px !important;
    background: var(--sc-surface-soft) !important;
    color: var(--sc-text-soft) !important;
  }}

  .mode-tabs .tab-wrapper > .overflow-menu > button:hover {{
    background: var(--sc-indigo-soft) !important;
    color: var(--sc-text) !important;
  }}

  .mode-tabs .overflow-dropdown {{
    min-width: 170px !important;
    padding: 6px !important;
    border: 1px solid var(--sc-border-strong) !important;
    border-radius: 15px !important;
    background: var(--sc-surface-raised) !important;
    box-shadow: var(--sc-shadow-soft);
  }}

  .mode-tabs .overflow-dropdown button {{
    width: 100% !important;
    min-height: 42px !important;
    padding: 9px 12px !important;
    border-radius: 10px !important;
    color: var(--sc-text-soft) !important;
    text-align: left !important;
  }}

  .mode-intro {{
    margin-bottom: 20px;
  }}

  .mode-intro h2 {{
    font-size: clamp(1.82rem, 8.5vw, 2.28rem);
  }}

  .sc-panel {{
    padding: 18px !important;
    border-radius: 22px !important;
  }}

  .shield-empty,
  .call-empty,
  .court-empty {{
    min-height: 300px;
    padding: 31px 21px;
    border-radius: 23px;
  }}

  .shield-card {{
    padding: 26px 21px;
    border-radius: 24px;
  }}

  .shield-card::before {{
    top: 22px;
    bottom: 22px;
  }}

  .verdict-icon {{
    width: 50px;
    height: 50px;
  }}

  .guide-card {{
    min-height: 0;
  }}

  .role-card {{
    flex-basis: 142px !important;
    min-height: 170px;
  }}

  .role-panel {{
    padding: 23px 19px;
  }}

  .companion-tabs .tab-wrapper > .tab-container[role="tablist"] button {{
    font-size: 0.69rem !important;
  }}

  .companion-shell {{
    border-radius: 23px;
  }}

  .conversation {{
    min-height: 150px;
    padding: 19px;
  }}

  .companion-result {{
    margin: 15px 17px 17px;
    padding: 17px;
  }}

  .companion-result-empty {{
    grid-template-columns: 1fr;
    text-align: center;
  }}

  .empty-review-icon {{
    margin: 0 auto;
  }}

  .companion-empty-foot {{
    padding: 0 18px 19px;
  }}

  .utility-dock {{
    padding: 18px !important;
    border-radius: 23px !important;
  }}

  .utility-brand {{
    min-width: 100%;
  }}

  .utility-topbar > .form {{
    display: grid !important;
    grid-template-columns: 1fr;
    padding: 7px !important;
  }}
}}

@media (prefers-reduced-motion: reduce) {{
  *,
  *::before,
  *::after {{
    scroll-behavior: auto !important;
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }}
}}

{role_rules}
"""
