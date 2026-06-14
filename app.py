"""Scam Court AI — Premium Gradio courtroom interface with Shield Mode.

Run locally:
    python app.py

Deploy to Hugging Face Spaces:
    Push this repo; Spaces will run app.py automatically.
"""

from __future__ import annotations

import dataclasses
import html
import pathlib
import random
import re
import urllib.parse

import gradio as gr

from courtroom import get_backend, get_vision_backend
from courtroom.config import get_vision_model_id
from courtroom.engine import CourtroomEngine
from courtroom.zero_gpu import (
    SPACES_IMPORT_SUCCEEDED,
    ZERO_GPU_DECORATOR_ACTIVE,
    ZERO_GPU_RUNTIME_ACTIVE,
    gpu_function,
)

# ---------------------------------------------------------------------------
# Internationalization + theme state
# ---------------------------------------------------------------------------
_current_lang: str = "en"
_current_theme: str = "dark"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Header
        "app_subtitle": "3-Second Scam Shield + AI Courtroom Explanation for the people you protect.",
        # Tabs
        "tab_shield": "Shield",
        "tab_court": "Court",
        "tab_call": "Suspicious Call",
        "tab_companion": "Companion Preview",
        # Shield
        "shield_subtitle": "For suspicious messages or call summaries. Get a 3-second safety verdict.",
        "section_submit_evidence": "Paste a suspicious message",
        "input_placeholder": "WhatsApp, SMS, email, or screenshot text…",
        "upload_screenshot": "Or upload a screenshot",
        "upload_hint": "PNG, JPG, JPEG · WhatsApp, SMS, email, marketplace, or fake invoice screenshot",
        "btn_analyze": "Analyze",
        "btn_analyze_court": "Bring to Court",
        "btn_random_example": "Random Example",
        "btn_clear": "Clear",
        "quick_examples": "Quick Load",
        # Shield output
        "shield_empty": "Paste a message and tap <strong>Analyze</strong> to see your Shield verdict.",
        "shield_score_label": "Risk score",
        "shield_script_label": "What to tell a trusted contact",
        "shield_court_hint": "Switch to the <strong>Court</strong> tab for a full explanation of why this message is risky.",
        # Court
        "court_subtitle": "Full AI courtroom explanation. See Detective, Prosecutor, Defender, Judge, and Clerk.",
        "court_input_label": "Submit Evidence",
        "court_members": "Court Members",
        "export_json": "Report JSON",
        "export_accordion": "Export Report JSON",
        # Role titles/subtitles (render-time)
        "role_detective": "Detective",
        "role_prosecutor": "Prosecutor",
        "role_defender": "Defender",
        "role_judge": "Judge",
        "role_clerk": "Clerk",
        "role_subtitle_detective": "Sharp, observant, factual",
        "role_subtitle_prosecutor": "Persuasive, dramatic, logical",
        "role_subtitle_defender": "Skeptical, fair, cautious",
        "role_subtitle_judge": "Authoritative, measured, decisive",
        "role_subtitle_clerk": "Helpful, calm, actionable",
        "role_title_detective": "Detective Evidence Board",
        "role_title_prosecutor": "Prosecutor Argument",
        "role_title_defender": "Defender Argument",
        "role_title_judge": "Judge Verdict",
        "role_title_clerk": "Safety Clerk",
        "role_waiting": "Waiting for evidence…",
        "role_no_red_flags": "<p><em>No red flags detected.</em></p>",
        "role_safe_reply": "Safe Reply",
        "role_next_steps": "Next Steps",
        # Gauge
        "gauge_risk_score": "RISK SCORE",
        "gauge_waiting": "WAITING",
        "gauge_waiting_rationale": "Submit evidence to begin the trial.",
        # Call
        "call_subtitle": "For active phone calls. Check what is happening right now.",
        "call_title": "Quick phone-call check",
        "call_hint": "Check every box that applies to the call you or a loved one is on.",
        "call_money": "They are asking for money, gift cards, or crypto",
        "call_code": "They are asking for a code, password, or PIN",
        "call_family": "They claim to be family using a new number",
        "call_urgency": "They create urgency, fear, or a deadline",
        "call_secrecy": "They ask you to keep the call secret",
        "btn_check_call": "Check the Call",
        "btn_reset": "Reset",
        "call_warning_signs": "Warning signs",
        "call_quick_score": "Quick risk score",
        # Call trusted scripts
        "call_script_code": "I am on a call where someone is asking for my password or a code. I hung up. Can you help me change my account passwords just in case?",
        "call_script_family_money": "Someone is pretending to be family and asking for money on the phone. I hung up. Can you help me reach [name] on the number we already have?",
        "call_script_money": "I just hung up on a call asking me to send money or buy gift cards. Please remind me not to send anything until I verify through an official channel.",
        "call_script_family": "Someone called claiming to be family from a new number. I hung up. Can you help me reach them on the number we already know?",
        "call_script_high": "I just hung up on a suspicious phone call. The person was pressuring me. Can you sit with me while I report it?",
        "call_script_medium": "I received a suspicious call and I am not sure it is real. I told them I would call back. Can you help me verify the number?",
        "call_script_low": "I received a phone call that seemed okay, but I wanted to be cautious. No action needed right now.",
        "call_action_hangup": "Hang up now and verify independently using a trusted number.",
        # Companion
        "companion_subtitle": "Simulation of future WhatsApp/SMS/Marketplace integration.",
        "companion_title": "Paste a message to preview",
        "companion_btn_analyze": "Analyze Selected Message",
        "companion_whatsapp": "WhatsApp preview",
        "companion_sms": "SMS preview",
        "companion_marketplace": "Marketplace preview",
        "companion_whatsapp_tab": "WhatsApp",
        "companion_sms_tab": "SMS",
        "companion_marketplace_tab": "Marketplace",
        "companion_empty_whatsapp": "Analyze a message first to preview the WhatsApp companion card.",
        "companion_empty_sms": "Analyze a message first to preview the SMS companion card.",
        "companion_empty_marketplace": "Analyze a message first to preview the Marketplace companion card.",
        "companion_unknown_sender": "Unknown sender",
        "companion_buyer_message": "Buyer message",
        "companion_safe_reply": "Your safe reply",
        "companion_recommended_response": "Recommended response",
        "companion_now": "Now",
        "companion_draft": "Draft",
        "companion_platform": "Platform: Marketplace",
        "companion_action_label": "Action:",
        "companion_switch_court": "Switch to the <strong>Court</strong> tab for the full explanation (score: {score})",
        "companion_disclaimer": "Prototype simulation — not a real extension",
        "companion_empty_desc": "This panel previews how Scam Court AI would appear inside {platform}.",
        # Vision
        "vision_title": "Vision Witness",
        "vision_status_inactive": "Inactive — paste text for analysis",
        "vision_status_loaded": "Loaded — vision backend ready",
        "vision_status_analyzed": "Analyzed",
        "vision_status_failed": "Failed — verify independently",
        "vision_status_not_available": "Not Available — install transformers + torch",
        "vision_type_label": "Type:",
        "vision_extracted_label": "Extracted text:",
        "vision_clues_label": "Visual clues:",
        "vision_error_label": "Error:",
        "vision_no_analysis": "<p>Screenshot received. Vision analysis is not active yet. Paste the message text for full analysis.</p>",
        "vision_confidence": "Confidence",
        "vision_privacy": "Model: {model} · Screenshot processed only for this session.",
        # Examples
        "ex_family": "Family Impersonation",
        "ex_bank": "Fake Bank Alert",
        "ex_otp": "OTP / Code Theft",
        "ex_marketplace": "Marketplace Deposit Scam",
        "ex_invoice": "Fake Invoice",
        # Controls
        "lang_label": "Language",
        "theme_label": "Theme",
        "theme_dark": "Dark",
        "theme_light": "Light",
        # Footer
        "footer_tagline": "Scam Court AI · Hugging Face Build Small Hackathon · CPU-first · Model-ready",
        "backend_text": "Text",
        "backend_vision": "Vision",
        "backend_model": "Model",
        "backend_cache": "Cache",
    },
    "es": {
        # Header
        "app_subtitle": "Escudo Anti-Estafa de 3 Segundos + Explicación de la Corte de IA para quienes proteges.",
        # Tabs
        "tab_shield": "Escudo",
        "tab_court": "Corte",
        "tab_call": "Llamada Sospechosa",
        "tab_companion": "Vista Previa del Companion",
        # Shield
        "shield_subtitle": "Para mensajes sospechosos o resúmenes de llamadas. Obtén un veredicto de seguridad en 3 segundos.",
        "section_submit_evidence": "Pega un mensaje sospechoso",
        "input_placeholder": "Texto de WhatsApp, SMS, correo o captura de pantalla…",
        "upload_screenshot": "O sube una captura de pantalla",
        "upload_hint": "PNG, JPG, JPEG · captura de WhatsApp, SMS, correo, marketplace o factura falsa",
        "btn_analyze": "Analizar",
        "btn_analyze_court": "Llevar a la Corte",
        "btn_random_example": "Ejemplo Aleatorio",
        "btn_clear": "Borrar",
        "quick_examples": "Carga Rápida",
        # Shield output
        "shield_empty": "Pega un mensaje y toca <strong>Analizar</strong> para ver tu veredicto del Escudo.",
        "shield_score_label": "Puntuación de riesgo",
        "shield_script_label": "Qué decirle a un contacto de confianza",
        "shield_court_hint": "Cambia a la pestaña <strong>Corte</strong> para una explicación completa de por qué este mensaje es riesgoso.",
        # Court
        "court_subtitle": "Explicación completa de la corte de IA. Ve a Detective, Fiscal, Defensor, Juez y Secretario.",
        "court_input_label": "Enviar evidencia",
        "court_members": "Miembros de la Corte",
        "export_json": "JSON del Informe",
        "export_accordion": "Exportar JSON del Informe",
        # Role titles/subtitles
        "role_detective": "Detective",
        "role_prosecutor": "Fiscal",
        "role_defender": "Defensor",
        "role_judge": "Juez",
        "role_clerk": "Secretario",
        "role_subtitle_detective": "Agudo, observador, factual",
        "role_subtitle_prosecutor": "Persuasivo, dramático, lógico",
        "role_subtitle_defender": "Escéptico, justo, cauteloso",
        "role_subtitle_judge": "Autoritario, mesurado, decisivo",
        "role_subtitle_clerk": "Servicial, calmado, accionable",
        "role_title_detective": "Tablero de Evidencia del Detective",
        "role_title_prosecutor": "Argumento del Fiscal",
        "role_title_defender": "Argumento del Defensor",
        "role_title_judge": "Veredicto del Juez",
        "role_title_clerk": "Secretario de Seguridad",
        "role_waiting": "Esperando evidencia…",
        "role_no_red_flags": "<p><em>No se detectaron señales de alerta.</em></p>",
        "role_safe_reply": "Respuesta Segura",
        "role_next_steps": "Próximos Pasos",
        # Gauge
        "gauge_risk_score": "PUNTUACIÓN DE RIESGO",
        "gauge_waiting": "ESPERANDO",
        "gauge_waiting_rationale": "Envía evidencia para comenzar el juicio.",
        # Call
        "call_subtitle": "Para llamadas telefónicas activas. Comprueba qué está pasando ahora mismo.",
        "call_title": "Revisión rápida de llamada",
        "call_hint": "Marca cada casilla que aplique a la llamada en la que tú o un ser querido están.",
        "call_money": "Pidieron dinero, tarjetas de regalo o cripto",
        "call_code": "Pidieron un código, contraseña o PIN",
        "call_family": "Dicen ser familia usando un nuevo número",
        "call_urgency": "Generan urgencia, miedo o una fecha límite",
        "call_secrecy": "Te piden que mantengas la llamada en secreto",
        "btn_check_call": "Revisar Llamada",
        "btn_reset": "Restablecer",
        "call_warning_signs": "Señales de alerta",
        "call_quick_score": "Puntuación rápida de riesgo",
        # Call trusted scripts
        "call_script_code": "Estoy en una llamada donde alguien me pide mi contraseña o un código. Colgué. ¿Puedes ayudarme a cambiar las contraseñas de mis cuentas por si acaso?",
        "call_script_family_money": "Alguien se hace pasar por un familiar y me pide dinero por teléfono. Colgué. ¿Puedes ayudarme a contactar a [nombre] en el número que ya tenemos?",
        "call_script_money": "Acabo de colgar una llamada donde me pedían enviar dinero o comprar tarjetas de regalo. Por favor recuérdame no enviar nada hasta verificar por un canal oficial.",
        "call_script_family": "Alguien llamó diciendo ser un familiar desde un nuevo número. Colgué. ¿Puedes ayudarme a contactarlos en el número que ya conocemos?",
        "call_script_high": "Acabo de colgar una llamada sospechosa. La persona me presionaba. ¿Puedes acompañarme mientras la reporto?",
        "call_script_medium": "Recibí una llamada sospechosa y no estoy seguro de que sea real. Les dije que devolvería la llamada. ¿Puedes ayudarme a verificar el número?",
        "call_script_low": "Recibí una llamada telefónica que parecía estar bien, pero quise ser cauteloso. No se necesita acción por ahora.",
        "call_action_hangup": "Cuelga ahora y verifica de forma independiente usando un número de confianza.",
        # Companion
        "companion_subtitle": "Simulación de la futura integración con WhatsApp/SMS/Marketplace.",
        "companion_title": "Pega un mensaje para previsualizar",
        "companion_btn_analyze": "Analizar Mensaje Seleccionado",
        "companion_whatsapp": "Vista previa de WhatsApp",
        "companion_sms": "Vista previa de SMS",
        "companion_marketplace": "Vista previa de Marketplace",
        "companion_whatsapp_tab": "WhatsApp",
        "companion_sms_tab": "SMS",
        "companion_marketplace_tab": "Marketplace",
        "companion_empty_whatsapp": "Analiza un mensaje primero para previsualizar la tarjeta companion de WhatsApp.",
        "companion_empty_sms": "Analiza un mensaje primero para previsualizar la tarjeta companion de SMS.",
        "companion_empty_marketplace": "Analiza un mensaje primero para previsualizar la tarjeta companion de Marketplace.",
        "companion_unknown_sender": "Remitente desconocido",
        "companion_buyer_message": "Mensaje del comprador",
        "companion_safe_reply": "Tu respuesta segura",
        "companion_recommended_response": "Respuesta recomendada",
        "companion_now": "Ahora",
        "companion_draft": "Borrador",
        "companion_platform": "Plataforma: Marketplace",
        "companion_action_label": "Acción:",
        "companion_switch_court": "Cambia a la pestaña <strong>Corte</strong> para la explicación completa (puntuación: {score})",
        "companion_disclaimer": "Simulación de prototipo — no es una extensión real",
        "companion_empty_desc": "Este panel muestra cómo aparecería Scam Court AI dentro de {platform}.",
        # Vision
        "vision_title": "Testigo Visual",
        "vision_status_inactive": "Inactivo — pega texto para analizar",
        "vision_status_loaded": "Cargado — backend de visión listo",
        "vision_status_analyzed": "Analizado",
        "vision_status_failed": "Falló — verifica de forma independiente",
        "vision_status_not_available": "No Disponible — instala transformers + torch",
        "vision_type_label": "Tipo:",
        "vision_extracted_label": "Texto extraído:",
        "vision_clues_label": "Pistas visuales:",
        "vision_error_label": "Error:",
        "vision_no_analysis": "<p>Captura de pantalla recibida. El análisis de visión aún no está activo. Pega el texto del mensaje para un análisis completo.</p>",
        "vision_confidence": "Confianza",
        "vision_privacy": "Modelo: {model} · La captura se procesa solo para esta sesión.",
        # Examples
        "ex_family": "Suplantación de Familiar",
        "ex_bank": "Alerta Bancaria Falsa",
        "ex_otp": "Robo de OTP / Código",
        "ex_marketplace": "Estafa de Depósito en Marketplace",
        "ex_invoice": "Factura Falsa",
        # Controls
        "lang_label": "Idioma",
        "theme_label": "Tema",
        "theme_dark": "Oscuro",
        "theme_light": "Claro",
        # Footer
        "footer_tagline": "Scam Court AI · Hugging Face Build Small Hackathon · CPU-first · Model-ready",
        "backend_text": "Texto",
        "backend_vision": "Visión",
        "backend_model": "Modelo",
        "backend_cache": "Caché",
    },
}


def _t(key: str) -> str:
    return TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"]).get(key, key)


def set_lang(lang: str) -> str:
    global _current_lang
    _current_lang = lang if lang in TRANSLATIONS else "en"
    return _current_lang


def set_theme(theme: str) -> str:
    global _current_theme
    _current_theme = theme if theme in ("dark", "light") else "dark"
    return _current_theme


# ---------------------------------------------------------------------------
# Load local SVG assets
# ---------------------------------------------------------------------------
_ASSET_DIR = pathlib.Path(__file__).parent / "assets"


def _load_svg(name: str) -> str:
    return (_ASSET_DIR / f"{name}.svg").read_text(encoding="utf-8")


ROLE_SVGS = {
    "detective": _load_svg("detective"),
    "prosecutor": _load_svg("prosecutor"),
    "defender": _load_svg("defender"),
    "judge": _load_svg("judge"),
    "clerk": _load_svg("clerk"),
}

ROLE_SUBTITLE_KEYS = {
    "detective": "role_subtitle_detective",
    "prosecutor": "role_subtitle_prosecutor",
    "defender": "role_subtitle_defender",
    "judge": "role_subtitle_judge",
    "clerk": "role_subtitle_clerk",
}


# ---------------------------------------------------------------------------
# Dynamic CSS — role button backgrounds + subtitles
# ---------------------------------------------------------------------------
def _build_role_css(svgs: dict[str, str], subtitles: dict[str, str]) -> str:
    bg_rules = []
    for role, svg in svgs.items():
        uri = f"url('data:image/svg+xml;charset=utf-8,{urllib.parse.quote(svg)}')"
        bg_rules.append(
            f".role-btn-{role} {{ background-image: {uri} !important; "
            f"background-repeat: no-repeat !important; "
            f"background-position: center 16px !important; "
            f"background-size: 40px 40px !important; }}"
        )
    sub_rules = []
    for role, sub in subtitles.items():
        sub_rules.append(
            f".role-btn-{role}::after {{ content: '{sub}'; display: block; "
            f"font-family: 'Inter', sans-serif; font-size: 0.58rem; "
            f"color: var(--text-tertiary); text-transform: uppercase; "
            f"letter-spacing: 1px; margin-top: 4px; font-weight: 600; }}"
        )
    return "\n".join(bg_rules + sub_rules)


# ---------------------------------------------------------------------------
# Custom CSS — premium dark courtroom aesthetic + accessible Shield Mode
# ---------------------------------------------------------------------------
def _build_css(role_subtitles: dict[str, str]) -> str:
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
  --bg: #0a0c12;
  --bg-elevated: rgba(255,255,255,0.03);
  --border: rgba(255,255,255,0.07);
  --text-primary: #f0f0f0;
  --text-secondary: rgba(240,240,240,0.55);
  --text-tertiary: rgba(240,240,240,0.32);
  --accent: #4ecdc4;
  --accent-dim: rgba(78,205,196,0.12);
  --accent-glow: rgba(78,205,196,0.18);
  --stop: #e85d5d;
  --stop-bg: rgba(232,93,93,0.08);
  --stop-glow: rgba(232,93,93,0.18);
  --verify: #f0a040;
  --verify-bg: rgba(240,160,64,0.08);
  --verify-glow: rgba(240,160,64,0.18);
  --safe: #4cd97b;
  --safe-bg: rgba(76,217,123,0.08);
  --safe-glow: rgba(76,217,123,0.18);
}}

body {{
  font-family: 'Inter', sans-serif;
  background:
    radial-gradient(ellipse 80% 60% at 50% -10%, rgba(78,205,196,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 90%, rgba(78,205,196,0.03) 0%, transparent 50%),
    linear-gradient(180deg, #0c0e14 0%, #0a0c12 50%, #080a10 100%) !important;
  color: var(--text-primary) !important;
  min-height: 100vh;
}}

.gradio-container {{
  background: transparent !important;
  max-width: 1200px !important;
  padding: 0 1.5rem !important;
}}

/* Hero */
#court-header {{
  text-align: center;
  padding: 3.5rem 1rem 2.5rem;
  margin-bottom: 0.5rem;
}}
#court-header h1 {{
  font-family: 'Playfair Display', serif;
  font-size: 3rem;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.5px;
  font-weight: 700;
}}
#court-header p {{
  color: var(--text-secondary);
  font-size: 1.05rem;
  margin-top: 0.6rem;
  font-weight: 400;
  letter-spacing: 0.2px;
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.5;
}}

/* Tabs */
.mode-tabs > .tab-nav {{
  border-bottom: 1px solid var(--border) !important;
  margin-bottom: 2rem !important;
}}
.mode-tabs .tab-nav button {{
  background: transparent !important;
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  letter-spacing: 0.3px !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  padding: 0.9rem 1.4rem !important;
  font-size: 0.9rem !important;
  transition: all 0.2s ease !important;
}}
.mode-tabs .tab-nav button.selected {{
  color: var(--text-primary) !important;
  border-bottom-color: var(--accent) !important;
  font-weight: 600 !important;
}}
.mode-tabs .tab-nav button:hover:not(.selected) {{
  color: var(--text-primary) !important;
}}

/* Panels */
.input-panel {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.6rem;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}}
.input-panel:hover {{
  border-color: rgba(255,255,255,0.1);
}}

/* Section labels */
.section-label {{
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
  font-size: 0.8rem;
  margin-bottom: 0.8rem;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  font-weight: 600;
}}

/* Forms */
textarea, input {{
  background: rgba(255,255,255,0.03) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  font-size: 0.95rem !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}}
textarea:focus, input:focus {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-dim) !important;
}}
textarea::placeholder {{
  color: var(--text-tertiary) !important;
}}

/* Buttons */
button.primary {{
  background: var(--accent) !important;
  color: #0c0e14 !important;
  font-weight: 600 !important;
  border: none !important;
  border-radius: 12px !important;
  letter-spacing: 0.2px !important;
  transition: all 0.2s ease !important;
  padding: 0.6rem 1.2rem !important;
}}
button.primary:hover {{
  filter: brightness(1.15) !important;
  transform: translateY(-1px) !important;
}}
button.secondary {{
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}}
button.secondary:hover {{
  background: rgba(255,255,255,0.08) !important;
  color: var(--text-primary) !important;
  border-color: rgba(255,255,255,0.12) !important;
}}

.example-btn {{
  background: rgba(255,255,255,0.03) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  font-size: 0.78rem !important;
  font-weight: 500 !important;
  padding: 0.4rem 0.7rem !important;
}}
.example-btn:hover {{
  background: rgba(255,255,255,0.07) !important;
  color: var(--text-primary) !important;
  border-color: rgba(255,255,255,0.1) !important;
}}

/* Shield verdict card */
.shield-card {{
  border-radius: 22px;
  padding: 2.5rem 2rem;
  text-align: center;
  margin-bottom: 1.5rem;
  border: 1px solid;
  position: relative;
  overflow: hidden;
}}
.shield-card::before {{
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at center, var(--glow-color, transparent) 0%, transparent 70%);
  opacity: 0.4;
  pointer-events: none;
}}
.shield-card.stop {{
  --glow-color: var(--stop-glow);
  background: var(--stop-bg);
  border-color: rgba(232,93,93,0.22);
  color: var(--text-primary);
  box-shadow: 0 0 40px var(--stop-glow), 0 4px 20px rgba(0,0,0,0.3);
}}
.shield-card.verify {{
  --glow-color: var(--verify-glow);
  background: var(--verify-bg);
  border-color: rgba(240,160,64,0.22);
  color: var(--text-primary);
  box-shadow: 0 0 40px var(--verify-glow), 0 4px 20px rgba(0,0,0,0.3);
}}
.shield-card.safe {{
  --glow-color: var(--safe-glow);
  background: var(--safe-bg);
  border-color: rgba(76,217,123,0.22);
  color: var(--text-primary);
  box-shadow: 0 0 40px var(--safe-glow), 0 4px 20px rgba(0,0,0,0.3);
}}
.shield-icon {{
  font-size: 2.8rem;
  margin-bottom: 0.8rem;
  line-height: 1;
}}
.shield-verdict {{
  font-family: 'Inter', sans-serif;
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 0.4rem;
}}
.shield-score {{
  display: inline-block;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
  background: rgba(0,0,0,0.2);
  margin-bottom: 1.2rem;
}}
.shield-action {{
  font-size: 1.15rem;
  font-weight: 500;
  line-height: 1.6;
  max-width: 640px;
  margin: 0 auto 1.5rem;
  color: var(--text-secondary);
}}
.shield-script {{
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.2rem 1.4rem;
  text-align: left;
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 640px;
  margin: 0 auto;
  color: var(--text-primary);
}}
.shield-script-label {{
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-tertiary);
  margin-bottom: 0.5rem;
  font-weight: 600;
}}
.shield-court-hint {{
  margin-top: 1.2rem;
  font-size: 0.9rem;
  color: var(--text-tertiary);
}}
.shield-empty {{
  text-align: center;
  padding: 4rem 1rem;
  color: var(--text-tertiary);
  font-size: 1rem;
  font-weight: 400;
}}

/* Gauge */
.gauge-container {{
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 1rem 1.5rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 20px;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}}
.gauge-container::before {{
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
  opacity: 0.5;
  pointer-events: none;
}}
.gauge-verdict {{
  font-family: 'Playfair Display', serif;
  font-size: 1.05rem;
  color: var(--text-primary);
  margin-top: 0.8rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 600;
}}
.gauge-rationale {{
  font-size: 0.85rem;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 0.4rem;
  max-width: 85%;
  line-height: 1.6;
}}

/* Role selector */
.role-selector {{
  display: flex;
  gap: 0.6rem;
  margin: 1.5rem 0 0.5rem;
}}
.role-btn {{
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: flex-end !important;
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  padding: 72px 0.4rem 0.9rem !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  cursor: pointer !important;
  min-height: 124px !important;
  line-height: 1.2 !important;
  position: relative !important;
}}
.role-btn::before {{
  content: '';
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}}
.role-btn:hover::before {{
  opacity: 1;
}}
.role-btn:hover {{
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.18) !important;
  transform: translateY(-3px) !important;
  box-shadow: 0 12px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(78,205,196,0.1) !important;
}}
.role-btn:active {{
  background: rgba(78,205,196,0.1) !important;
  border-color: var(--accent) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(78,205,196,0.15) !important;
}}

/* Active indicator */
.active-indicator {{
  display: flex;
  gap: 0.4rem;
  margin-bottom: 1rem;
}}
.active-bar {{
  flex: 1;
  height: 2px;
  border-radius: 1px;
  background: transparent;
  transition: background 0.3s ease;
}}
.active-bar.on {{
  background: var(--accent);
}}

/* Role panel */
.role-panel {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2rem;
  min-height: 280px;
  position: relative;
  overflow: hidden;
}}
.role-panel::before {{
  content: '';
  position: absolute;
  top: -30%;
  right: -20%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
  opacity: 0.3;
  pointer-events: none;
}}
.role-header {{
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.4rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}}
.role-avatar svg {{
  width: 48px;
  height: 48px;
}}
.role-title {{
  font-family: 'Playfair Display', serif;
  font-size: 1.25rem;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
  font-weight: 600;
}}
.role-subtitle {{
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin: 0.25rem 0 0;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-weight: 600;
}}
.role-body {{
  color: var(--text-secondary);
  line-height: 1.75;
  font-size: 0.95rem;
}}
.role-body ul, .role-body ol {{
  padding-left: 1.3rem;
  margin: 1rem 0;
}}
.role-body li {{
  margin-bottom: 0.6rem;
}}
.role-body strong {{
  color: var(--text-primary);
  font-weight: 600;
}}
.role-body em {{
  color: var(--text-tertiary);
  font-style: italic;
}}

/* Call checklist */
.call-check {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.4rem;
}}
.call-check label {{
  font-size: 0.95rem !important;
  color: var(--text-secondary) !important;
  font-weight: 400 !important;
}}
.call-check .wrap {{
  padding: 0.8rem 0.7rem !important;
  border-radius: 12px !important;
  transition: all 0.2s ease !important;
  border: 1px solid transparent !important;
  margin-bottom: 0.3rem !important;
}}
.call-check .wrap:hover {{
  background: rgba(255,255,255,0.03) !important;
}}
.call-check .wrap:has(input:checked) {{
  background: var(--accent-dim) !important;
  border-color: var(--accent) !important;
}}
.call-check .wrap:has(input:checked) label {{
  color: var(--text-primary) !important;
  font-weight: 500 !important;
}}
.call-check input[type="checkbox"] {{
  width: 20px !important;
  height: 20px !important;
  accent-color: var(--accent) !important;
}}

/* Companion */
.companion-phone {{
  max-width: 360px;
  margin: 0 auto;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: #0a0a0a;
  overflow: hidden;
}}
.companion-header {{
  background: rgba(255,255,255,0.04);
  padding: 0.6rem 0.9rem;
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border-bottom: 1px solid var(--border);
}}
.companion-body {{
  padding: 0.8rem;
  min-height: 120px;
}}
.companion-bubble-in {{
  background: rgba(255,255,255,0.06);
  color: var(--text-primary);
  border-radius: 14px 14px 14px 4px;
  padding: 0.6rem 0.85rem;
  margin-bottom: 0.5rem;
  font-size: 0.88rem;
  line-height: 1.45;
}}
.companion-bubble-out {{
  background: rgba(78,205,196,0.15);
  color: var(--text-primary);
  border-radius: 14px 14px 4px 14px;
  padding: 0.6rem 0.85rem;
  margin-bottom: 0.5rem;
  font-size: 0.88rem;
  line-height: 1.45;
  margin-left: auto;
}}
.companion-sms {{
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 0.75rem;
  font-size: 0.88rem;
  line-height: 1.45;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}}
.companion-sms-label {{
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 600;
}}
.companion-meta {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
}}
.companion-shield {{
  display: inline-block;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-top: 0.5rem;
}}
.companion-shield.stop {{
  background: var(--stop-bg);
  color: var(--stop);
  border: 1px solid rgba(232,93,93,0.2);
}}
.companion-shield.verify {{
  background: var(--verify-bg);
  color: var(--verify);
  border: 1px solid rgba(240,160,64,0.2);
}}
.companion-shield.safe {{
  background: var(--safe-bg);
  color: var(--safe);
  border: 1px solid rgba(76,217,123,0.2);
}}
.companion-empty {{
  text-align: center;
  padding: 1.2rem 1rem;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}}
.companion-action {{
  margin-top: 0.6rem;
  font-size: 0.82rem;
  color: var(--text-secondary);
}}
.companion-court-hint {{
  margin-top: 0.3rem;
  font-size: 0.78rem;
  color: var(--text-tertiary);
}}
.companion-disclaimer {{
  font-size: 0.65rem;
  color: var(--text-tertiary);
  margin-top: 0.5rem;
  text-align: center;
  letter-spacing: 0.3px;
}}

/* Vision */
.vision-card {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.4rem;
  margin-top: 1.2rem;
  position: relative;
  overflow: hidden;
}}
.vision-card::before {{
  content: '';
  position: absolute;
  top: -50%;
  left: -20%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
  opacity: 0.25;
  pointer-events: none;
}}
.vision-header {{
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary);
  margin-bottom: 0.8rem;
}}
.vision-status {{
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}}
.vision-status.inactive {{
  background: rgba(150,150,150,0.12);
  color: var(--text-tertiary);
  border: 1px solid rgba(150,150,150,0.15);
}}
.vision-status.loaded {{
  background: rgba(78,205,196,0.1);
  color: var(--accent);
  border: 1px solid rgba(78,205,196,0.2);
}}
.vision-status.analyzed {{
  background: var(--safe-bg);
  color: var(--safe);
  border: 1px solid rgba(76,217,123,0.2);
}}
.vision-status.failed {{
  background: var(--stop-bg);
  color: var(--stop);
  border: 1px solid rgba(232,93,93,0.2);
}}
.vision-status.not_available {{
  background: var(--verify-bg);
  color: var(--verify);
  border: 1px solid rgba(240,160,64,0.2);
}}
.vision-body {{
  font-size: 0.92rem;
  color: var(--text-secondary);
  line-height: 1.65;
}}
.vision-body p {{
  margin: 0.4rem 0;
}}
.vision-body strong {{
  color: var(--text-primary);
  font-weight: 600;
}}
.vision-privacy {{
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin-top: 0.8rem;
  padding-top: 0.8rem;
  border-top: 1px solid var(--border);
}}

/* Backend status */
.backend-status {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 500;
  letter-spacing: 0.3px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}}
.backend-status:hover {{
  background: rgba(255,255,255,0.07);
  border-color: rgba(255,255,255,0.12);
}}
.backend-status .dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--safe);
  box-shadow: 0 0 6px var(--safe);
}}
.backend-status .dot.off {{
  background: var(--verify);
  box-shadow: 0 0 6px var(--verify);
}}

/* Utility bar / footer dock */
.utility-bar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.9rem 1.4rem;
  margin-top: 3rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: 18px;
  position: relative;
  overflow: hidden;
}}
.utility-bar::before {{
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0.3;
}}
.utility-section {{
  display: flex;
  align-items: center;
  gap: 0.6rem;
}}
.utility-section-label {{
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  font-weight: 700;
  color: var(--text-tertiary);
  margin-right: 0.3rem;
}}
.utility-brand {{
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.3px;
  font-family: 'Playfair Display', serif;
}}
.utility-meta {{
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}}
.utility-controls {{
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}
.utility-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.72rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}}
.utility-pill:hover {{
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.12);
}}
.utility-pill select {{
  background: transparent;
  border: none;
  color: inherit;
  font-size: inherit;
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  appearance: none;
  padding-right: 0.4rem;
}}

/* Accordion */
.gr-accordion {{
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
}}

footer {{ display: none !important; }}

/* -------------------- Light mode -------------------- */
body.light {{
  --bg: #f5f5f0;
  --bg-elevated: #ffffff;
  --border: rgba(0,0,0,0.06);
  --text-primary: #1a1a1a;
  --text-secondary: rgba(0,0,0,0.55);
  --text-tertiary: rgba(0,0,0,0.35);
  --accent: #2a9d8f;
  --accent-dim: rgba(42,157,143,0.08);
  --stop: #c0392b;
  --stop-bg: rgba(192,57,43,0.06);
  --verify: #d68910;
  --verify-bg: rgba(214,137,16,0.06);
  --safe: #27ae60;
  --safe-bg: rgba(39,174,96,0.06);
}}
body.light {{
  background: var(--bg) !important;
  color: var(--text-primary) !important;
}}
body.light .gradio-container {{
  background: transparent !important;
}}
body.light .companion-phone {{
  background: #fff !important;
}}
body.light .companion-bubble-in {{
  background: #f2f2f2 !important;
  color: #1a1a1a !important;
}}
body.light .companion-bubble-out {{
  background: #d1f0ea !important;
  color: #154a3f !important;
}}
body.light textarea::placeholder {{
  color: var(--text-tertiary) !important;
}}
body.light button.secondary {{
  background: rgba(0,0,0,0.03) !important;
  color: var(--text-secondary) !important;
  border-color: var(--border) !important;
}}
body.light button.secondary:hover {{
  background: rgba(0,0,0,0.06) !important;
  color: var(--text-primary) !important;
}}
body.light .example-btn {{
  background: rgba(0,0,0,0.02) !important;
  color: var(--text-secondary) !important;
  border-color: var(--border) !important;
}}
body.light .example-btn:hover {{
  background: rgba(0,0,0,0.05) !important;
  color: var(--text-primary) !important;
}}
body.light .call-check .wrap:hover {{
  background: rgba(0,0,0,0.02) !important;
}}
body.light .role-btn:hover {{
  box-shadow: 0 8px 24px rgba(0,0,0,0.1) !important;
}}

/* -------------------- Responsive -------------------- */
@media (max-width: 1200px) {{
  .gradio-container {{ max-width: 1100px !important; padding: 0 1rem !important; }}
}}

@media (max-width: 899px) {{
  #court-header {{ padding: 2.5rem 1rem 1.5rem !important; }}
  #court-header h1 {{ font-size: 2.2rem !important; }}
  .role-selector {{
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    gap: 0.5rem !important;
    padding-bottom: 0.4rem !important;
  }}
  .role-btn {{
    flex: 0 0 auto !important;
    min-width: 88px !important;
    min-height: 102px !important;
    padding: 56px 0.4rem 0.6rem !important;
    background-size: 34px 34px !important;
    background-position: center 10px !important;
  }}
  .role-btn::after {{ font-size: 0.55rem !important; letter-spacing: 0.6px !important; }}
  .input-panel {{ padding: 1.2rem !important; }}
  .utility-bar {{ flex-direction: column !important; align-items: flex-start !important; gap: 0.8rem !important; }}
}}

@media (max-width: 639px) {{
  .gradio-container {{ padding: 0 0.8rem !important; }}
  #court-header {{ padding: 2rem 0.8rem 1.2rem !important; }}
  #court-header h1 {{ font-size: 1.8rem !important; }}
  .mode-tabs .tab-nav button {{ padding: 0.7rem 0.9rem !important; font-size: 0.8rem !important; }}
  .input-panel {{ border-radius: 14px !important; }}
  .shield-verdict {{ font-size: 1.8rem !important; }}
  .shield-action {{ font-size: 1rem !important; }}
  .companion-phone {{ border-radius: 16px !important; }}
  .top-controls {{
    flex-direction: column !important;
    gap: 0.5rem !important;
    align-items: stretch !important;
  }}
  .utility-bar {{ padding: 0.8rem 1rem !important; border-radius: 12px !important; }}
}}

{_build_role_css(ROLE_SVGS, role_subtitles)}
"""




def _role_subtitles_for_theme() -> dict[str, str]:
    return {role: _t(key) for role, key in ROLE_SUBTITLE_KEYS.items()}

# ---------------------------------------------------------------------------
# Backend instance (heuristic by default; smollm3 when SCAM_COURT_BACKEND=smollm3)
# ---------------------------------------------------------------------------
backend = get_backend()

# ---------------------------------------------------------------------------
# Example messages
# ---------------------------------------------------------------------------
EXAMPLES = [
    {
        "label": _t("ex_family"),
        "text": (
            "Hi honey, it's Mom. I got a new phone and lost all my contacts. "
            "Can you send me $500 via Zelle? I'm stuck at the grocery store and my card isn't working. "
            "Please don't tell Dad, it's embarrassing. Send it to this number quickly!"
        ),
    },
    {
        "label": _t("ex_bank"),
        "text": (
            "ALERT: Your Chase account has been suspended due to suspicious login activity. "
            "Verify your identity immediately at http://chase-verify-now.tk/login to avoid permanent closure. "
            "Failure to act within 24 hours will result in loss of all funds."
        ),
    },
    {
        "label": _t("ex_otp"),
        "text": (
            "Hey, this is Mike from IT support. We're doing a security audit and I need you to forward "
            "the 6-digit code I just sent to your phone. It's urgent — the CEO's account is compromised "
            "and we need to lock it down now. Please reply with the code ASAP."
        ),
    },
    {
        "label": _t("ex_marketplace"),
        "text": (
            "Hi! I'm very interested in buying your couch. I can't pick it up in person because I'm a "
            "marine engineer offshore, but I'll send a courier. Please pay a $150 holding deposit via "
            "Cash App so I know you're serious. My assistant will collect it tomorrow."
        ),
    },
    {
        "label": _t("ex_invoice"),
        "text": (
            "Invoice #8921-REM is now 7 days overdue. Total due: $4,250.00. "
            "Please remit payment immediately to avoid late fees and service interruption. "
            "Click here to view and pay your invoice: https://invoice-portal.zip/pay?id=8921"
        ),
    },
]

EXAMPLE_BUTTONS = [[ex["label"], ex["text"]] for ex in EXAMPLES]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _risk_color(score: int) -> str:
    if score >= 80:
        return "#c0392b"
    if score >= 50:
        return "#d35400"
    if score >= 20:
        return "#f39c12"
    return "#27ae60"


def _verdict_label(score: int) -> str:
    if score >= 80:
        return "SCAM"
    if score >= 50:
        return "SUSPICIOUS"
    if score >= 20:
        return "CAUTION"
    return "LIKELY SAFE"


def _render_gauge(score: int, verdict: str, rationale: str) -> str:
    r = 58
    c = 2 * 3.14159 * r
    offset = c * (1 - score / 100)
    color = _risk_color(score)
    return f"""
    <div class="gauge-container">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
        <circle cx="70" cy="70" r="{r}" fill="none" stroke="{color}" stroke-width="6"
          stroke-dasharray="{c:.2f}" stroke-dashoffset="{offset:.2f}"
          stroke-linecap="round" transform="rotate(-90 70 70)"/>
        <text x="70" y="66" text-anchor="middle" fill="var(--text-primary)" font-size="32" font-weight="700"
          font-family="'Inter', sans-serif">{score}</text>
        <text x="70" y="84" text-anchor="middle" fill="var(--text-tertiary)" font-size="8"
          font-family="'Inter', sans-serif" letter-spacing="2">{html.escape(_t("gauge_risk_score"))}</text>
      </svg>
      <div class="gauge-verdict">{html.escape(verdict)}</div>
      <div class="gauge-rationale">{html.escape(rationale)}</div>
    </div>
    """


def _render_indicator(active_role: str | None) -> str:
    roles = ["detective", "prosecutor", "defender", "judge", "clerk"]
    bars = []
    for role in roles:
        cls = "on" if role == active_role else ""
        bars.append(f'<div class="active-bar {cls}"></div>')
    return f'<div class="active-indicator">{ "".join(bars) }</div>'


def _render_role(role: str, report_dict: dict | None) -> str:
    if not report_dict:
        return f'<div class="role-panel"><div class="role-body"><em>{html.escape(_t("role_waiting"))}</em></div></div>'

    titles = {
        "detective": _t("role_title_detective"),
        "prosecutor": _t("role_title_prosecutor"),
        "defender": _t("role_title_defender"),
        "judge": _t("role_title_judge"),
        "clerk": _t("role_title_clerk"),
    }
    subtitles = {
        "detective": _t("role_subtitle_detective"),
        "prosecutor": _t("role_subtitle_prosecutor"),
        "defender": _t("role_subtitle_defender"),
        "judge": _t("role_subtitle_judge"),
        "clerk": _t("role_subtitle_clerk"),
    }

    if role == "detective":
        evidence = report_dict.get("detective_report", {}).get("evidence", [])
        if not evidence:
            content = _t("role_no_red_flags")
        else:
            items = "".join(f"<li>{html.escape(e)}</li>" for e in evidence)
            content = f"<ul>{items}</ul>"
    elif role == "prosecutor":
        text = report_dict.get("prosecutor_argument", "").replace("\n", "<br>")
        content = f"<p>{text}</p>"
    elif role == "defender":
        text = report_dict.get("defender_argument", "").replace("\n", "<br>")
        content = f"<p>{text}</p>"
    elif role == "judge":
        verdict = html.escape(report_dict.get("judge_summary", {}).get("verdict", ""))
        rationale = report_dict.get("judge_summary", {}).get("rationale", "").replace("\n", "<br>")
        content = f"<p><strong>{verdict}</strong></p><p>{rationale}</p>"
    else:  # clerk
        reply = html.escape(report_dict.get("safety_reply", ""))
        steps = report_dict.get("next_steps", [])
        content = f"<p><strong>{_t('role_safe_reply')}</strong></p><p>{reply}</p>"
        if steps:
            items = "".join(f"<li>{html.escape(s)}</li>" for s in steps)
            content += f"<p><strong>{_t('role_next_steps')}</strong></p><ol>{items}</ol>"

    svg = ROLE_SVGS.get(role, "")
    return f"""
    <div class="role-panel">
      <div class="role-header">
        <div class="role-avatar">{svg}</div>
        <div class="role-meta">
          <div class="role-title">{html.escape(titles.get(role, role))}</div>
          <div class="role-subtitle">{html.escape(subtitles.get(role, ""))}</div>
        </div>
      </div>
      <div class="role-body">{content}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Shield Mode renderers
# ---------------------------------------------------------------------------
def _shield_card_class(verdict: str) -> str:
    v = verdict.upper()
    if "STOP" in v:
        return "stop"
    if "VERIFY" in v:
        return "verify"
    return "safe"


def _shield_icon(verdict: str) -> str:
    v = verdict.upper()
    if "STOP" in v:
        return "&#128721;"  # stop sign
    if "VERIFY" in v:
        return "&#9888;"  # warning
    return "&#10003;"  # check


def render_shield(report_dict: dict | None) -> str:
    if not report_dict:
        return f'<div class="shield-empty">{_t("shield_empty")}</div>'
    verdict = report_dict.get("shield_verdict", "VERIFY FIRST")
    action = report_dict.get("immediate_action", "Pause and verify before acting.")
    script = report_dict.get("trusted_contact_script", "")
    score = report_dict.get("risk_score", 0)
    cls = _shield_card_class(verdict)
    icon = _shield_icon(verdict)
    court_hint = ""
    if score >= 35:
        court_hint = f'<div class="shield-court-hint">{_t("shield_court_hint")}</div>'
    return f"""
    <div class="shield-card {cls}">
      <div class="shield-icon">{icon}</div>
      <div class="shield-verdict">{html.escape(verdict, quote=False)}</div>
      <div class="shield-score">{score}/100</div>
      <div class="shield-action">{html.escape(action, quote=False)}</div>
      <div class="shield-script">
        <div class="shield-script-label">{html.escape(_t("shield_script_label"))}</div>
        {html.escape(script, quote=False)}
      </div>
      {court_hint}
    </div>
    """


# ---------------------------------------------------------------------------
# Suspicious Call Quick Check
# ---------------------------------------------------------------------------
def _call_trusted_script(score: int, tags: list[str]) -> str:
    if "asks_code" in tags:
        return _t("call_script_code")
    if "asks_money" in tags and "claims_family_new_number" in tags:
        return _t("call_script_family_money")
    if "asks_money" in tags:
        return _t("call_script_money")
    if "claims_family_new_number" in tags:
        return _t("call_script_family")
    if score >= 70:
        return _t("call_script_high")
    if score >= 35:
        return _t("call_script_medium")
    return _t("call_script_low")


def _clean_visual_risk_clues(raw_clues: list[str], extracted_text: str) -> list[str]:
    """Remove placeholder tokens and derive fallback clues from text."""
    placeholder_tokens = {"list", "of", "visual", "red", "flags", "item", "none", "n/a", "unknown"}
    cleaned: list[str] = []
    for clue in raw_clues:
        clue_lower = clue.lower().strip()
        if clue_lower in placeholder_tokens or len(clue_lower) < 3:
            continue
        cleaned.append(clue.strip())

    # Derive fallback clues from extracted text heuristics
    if extracted_text:
        lowered = extracted_text.lower()
        fallback_map = {
            "suspicious link detected": bool(re.search(r"https?://", lowered)),
            "package delivery action request": any(k in lowered for k in ("fedex", "dhl", "usps", "ups", "package", "parcel", "delivery")),
            "money or payment request": any(k in lowered for k in ("payment", "pay", "wire", "gift card", "crypto", "zelle", "venmo")),
            "credential or code request": any(k in lowered for k in ("otp", "code", "password", "pin", "verify your identity")),
            "urgency or deadline": any(k in lowered for k in ("urgent", "immediately", "24 hours", "deadline", "act now")),
            "bank or government impersonation": any(k in lowered for k in ("bank", "irs", "social security", "government", "stimulus")),
            "marketplace off-platform payment": any(k in lowered for k in ("holding deposit", "security deposit", "off platform", "outside the app")),
        }
        for label, triggered in fallback_map.items():
            if triggered and label not in [c.lower() for c in cleaned]:
                cleaned.append(label)

    return cleaned


def analyze_call_checklist(
    asks_money: bool,
    asks_code: bool,
    claims_family_new_number: bool,
    urgency: bool,
    secrecy: bool,
) -> str:
    result = CourtroomEngine.evaluate_call_checklist(
        asks_money=asks_money,
        asks_code=asks_code,
        claims_family_new_number=claims_family_new_number,
        creates_urgency_or_fear=urgency,
        asks_secrecy=secrecy,
    )
    score = result["score"]
    verdict = result["verdict"]
    action = result["action"]
    tags = result["tags"]

    # Override high-risk action with stronger wording
    if score >= 70:
        action = _t("call_action_hangup")

    cls = _shield_card_class(verdict)
    icon = _shield_icon(verdict)
    script = _call_trusted_script(score, tags)

    tags_html = ""
    if tags:
        tags_html = (
            "<div style='margin-top:0.8rem;font-size:0.85rem;opacity:0.8;'>"
            f"{html.escape(_t('call_warning_signs'), quote=False)}: " + ", ".join(html.escape(t.replace("_", " "), quote=False) for t in tags)
            + "</div>"
        )
    return f"""
    <div class="shield-card {cls}">
      <div class="shield-icon">{icon}</div>
      <div class="shield-verdict">{html.escape(verdict, quote=False)}</div>
      <div class="shield-score">{score}/100</div>
      <div class="shield-action">{html.escape(action, quote=False)}</div>
      <div class="shield-script">
        <div class="shield-script-label">{html.escape(_t("shield_script_label"))}</div>
        {html.escape(script, quote=False)}
      </div>
      {tags_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Companion Preview renderers
# ---------------------------------------------------------------------------
def _truncate(text: str, length: int = 280) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"


def _companion_badge(report_dict: dict | None) -> str:
    if not report_dict:
        return ""
    verdict = report_dict.get("shield_verdict", "VERIFY FIRST")
    cls = _shield_card_class(verdict)
    return f'<span class="companion-shield {cls}">{html.escape(verdict)}</span>'


def render_companion_whatsapp(report_dict: dict | None) -> str:
    if not report_dict:
        return f'<div class="companion-empty">{html.escape(_t("companion_empty_whatsapp"))}</div>'
    text = report_dict.get("input_text", "")
    script = report_dict.get("trusted_contact_script", "")
    action = report_dict.get("immediate_action", "")
    score = report_dict.get("risk_score", 0)
    badge = _companion_badge(report_dict)
    return f"""
    <div class="companion-phone">
      <div class="companion-header">&#128172; {html.escape(_t("companion_whatsapp"))}</div>
      <div class="companion-body">
        <div class="companion-bubble-in">{html.escape(_truncate(text), quote=False)}</div>
        <div class="companion-bubble-out">{html.escape(_truncate(script), quote=False)}</div>
        {badge}
        <div class="companion-action">
          <strong>{html.escape(_t("companion_action_label"))}</strong> {html.escape(action, quote=False)}
        </div>
        <div class="companion-court-hint">
          {_t("companion_switch_court").format(score=score)}
        </div>
        <div class="companion-disclaimer">{html.escape(_t("companion_disclaimer"))}</div>
      </div>
    </div>
    """


def render_companion_sms(report_dict: dict | None) -> str:
    if not report_dict:
        return f'<div class="companion-empty">{html.escape(_t("companion_empty_sms"))}</div>'
    text = report_dict.get("input_text", "")
    script = report_dict.get("trusted_contact_script", "")
    action = report_dict.get("immediate_action", "")
    score = report_dict.get("risk_score", 0)
    badge = _companion_badge(report_dict)
    return f"""
    <div class="companion-phone">
      <div class="companion-header">&#9993; {html.escape(_t("companion_sms"))}</div>
      <div class="companion-body">
        <div class="companion-sms">
          <div class="companion-sms-label">{html.escape(_t("companion_unknown_sender"))}</div>
          {html.escape(_truncate(text), quote=False)}
          <div class="companion-meta"><span>{html.escape(_t("companion_now"))}</span></div>
        </div>
        <div class="companion-sms">
          <div class="companion-sms-label">{html.escape(_t("companion_safe_reply"))}</div>
          {html.escape(_truncate(script), quote=False)}
          <div class="companion-meta"><span>{html.escape(_t("companion_draft"))}</span></div>
        </div>
        {badge}
        <div class="companion-action">
          <strong>{html.escape(_t("companion_action_label"))}</strong> {html.escape(action, quote=False)}
        </div>
        <div class="companion-court-hint">
          {_t("companion_switch_court").format(score=score)}
        </div>
        <div class="companion-disclaimer">{html.escape(_t("companion_disclaimer"))}</div>
      </div>
    </div>
    """


def render_companion_marketplace(report_dict: dict | None) -> str:
    if not report_dict:
        return f'<div class="companion-empty">{html.escape(_t("companion_empty_marketplace"))}</div>'
    text = report_dict.get("input_text", "")
    script = report_dict.get("trusted_contact_script", "")
    action = report_dict.get("immediate_action", "")
    score = report_dict.get("risk_score", 0)
    badge = _companion_badge(report_dict)
    return f"""
    <div class="companion-phone">
      <div class="companion-header">&#128235; {html.escape(_t("companion_marketplace"))}</div>
      <div class="companion-body">
        <div class="companion-sms">
          <div class="companion-sms-label">{html.escape(_t("companion_buyer_message"))}</div>
          {html.escape(_truncate(text), quote=False)}
          <div class="companion-meta"><span>{html.escape(_t("companion_platform"))}</span></div>
        </div>
        <div class="companion-sms">
          <div class="companion-sms-label">{html.escape(_t("companion_recommended_response"))}</div>
          {html.escape(_truncate(script), quote=False)}
          <div class="companion-meta"><span>{html.escape(_t("companion_draft"))}</span></div>
        </div>
        {badge}
        <div class="companion-action">
          <strong>{html.escape(_t("companion_action_label"))}</strong> {html.escape(action, quote=False)}
        </div>
        <div class="companion-court-hint">
          {_t("companion_switch_court").format(score=score)}
        </div>
        <div class="companion-disclaimer">{html.escape(_t("companion_disclaimer"))}</div>
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Vision Witness renderer
# ---------------------------------------------------------------------------
def render_vision_witness(report_dict: dict | None) -> str:
    if not report_dict:
        return ""
    if not report_dict.get("image_evidence_present"):
        return ""
    status = report_dict.get("vision_status", "inactive")
    backend = report_dict.get("vision_backend", "none")
    model = report_dict.get("vision_model") or backend
    summary = report_dict.get("vision_summary") or ""
    extracted = report_dict.get("extracted_text") or ""
    screenshot_type = report_dict.get("screenshot_type") or ""
    clues = report_dict.get("screenshot_risk_clues", [])
    confidence = report_dict.get("vision_confidence", 0.0)
    error = report_dict.get("vision_error") or ""

    status_label = {
        "inactive": _t("vision_status_inactive"),
        "loaded": _t("vision_status_loaded"),
        "analyzed": _t("vision_status_analyzed"),
        "failed": _t("vision_status_failed"),
        "not_available": _t("vision_status_not_available"),
    }.get(status, status)

    body_parts = []
    if screenshot_type:
        body_parts.append(f'<p><strong>{html.escape(_t("vision_type_label"))}</strong> {html.escape(screenshot_type.capitalize(), quote=False)}</p>')
    if summary:
        body_parts.append(f"<p>{html.escape(summary, quote=False)}</p>")
    if extracted:
        body_parts.append(f'<p><strong>{html.escape(_t("vision_extracted_label"))}</strong> {html.escape(extracted, quote=False)}</p>')
    if clues:
        items = "".join(f"<li>{html.escape(c, quote=False)}</li>" for c in clues)
        body_parts.append(f'<p><strong>{html.escape(_t("vision_clues_label"))}</strong></p><ul>{items}</ul>')
    if error and status in ("failed", "not_available"):
        body_parts.append(f'<p style="opacity:0.7;font-size:0.85rem;"><strong>{html.escape(_t("vision_error_label"))}</strong> {html.escape(error, quote=False)}</p>')

    body_html = "".join(body_parts) if body_parts else _t("vision_no_analysis")

    confidence_badge = ""
    if confidence > 0:
        confidence_badge = f'<span style="margin-left:0.5rem;font-size:0.7rem;opacity:0.7;">{html.escape(_t("vision_confidence"))}: {confidence:.0%}</span>'

    return f"""
    <div class="vision-card">
      <div class="vision-header">&#128248; {html.escape(_t("vision_title"))}</div>
      <span class="vision-status {status}">{html.escape(status_label, quote=False)}</span>{confidence_badge}
      <div class="vision-body">{body_html}</div>
      <div class="vision-privacy">{_t("vision_privacy").format(model=html.escape(model, quote=False))}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Analysis function
# ---------------------------------------------------------------------------
@gpu_function(duration=180)
def analyze_message(message: str, image_path: str | None = None) -> tuple[str, dict, str, str, str, str, str, str]:
    has_image = image_path is not None and image_path != ""
    has_text = message and message.strip()

    if not has_text and not has_image:
        empty_gauge = _render_gauge(0, _t("gauge_waiting"), _t("gauge_waiting_rationale"))
        empty_shield = render_shield(None)
        empty_vision = render_vision_witness(None)
        empty_companion = (
            render_companion_whatsapp(None),
            render_companion_sms(None),
            render_companion_marketplace(None),
        )
        return empty_gauge, {}, "", empty_shield, empty_vision, *empty_companion

    # Vision backend handling
    vision_backend = get_vision_backend()
    vision_result: dict[str, Any] | None = None
    if has_image:
        vision_result = vision_backend.analyze_image(image_path, context_text=message or None)

    # Determine what text to analyze
    text_for_analysis = message or ""
    extracted_text = ""
    input_sources: list[str] = []
    if has_text:
        input_sources.append("pasted_text")
    if vision_result:
        extracted_text = vision_result.get("extracted_text") or ""
        recommended = vision_result.get("recommended_text_for_analysis") or ""
        if recommended:
            extracted_text = recommended
        if extracted_text:
            input_sources.append("vision_extracted_text")

    # Combine user text + extracted text if both present
    if has_text and extracted_text:
        text_for_analysis = f"[User text]: {message.strip()}\n[From screenshot]: {extracted_text}"
    elif extracted_text:
        text_for_analysis = extracted_text

    # Run text analysis on the effective input
    report = backend.analyze(text_for_analysis)

    # Override vision fields and fusion tracking on the report
    if has_image and vision_result:
        v_status = vision_result.get("vision_status", "inactive")
        v_confidence = float(vision_result.get("vision_confidence", 0.0))

        # SAFETY RULE: if vision failed or is inactive, force at least VERIFY FIRST
        if v_status not in ("analyzed", "loaded"):
            if report.risk_score < 35:
                report = dataclasses.replace(
                    report,
                    risk_score=35,
                    risk_level="medium",
                    verdict="VERIFY FIRST",
                    shield_verdict="VERIFY FIRST",
                    immediate_action="Screenshot uploaded but vision analysis is unavailable. Do not act on this message. Verify through a trusted, independent channel.",
                    trusted_contact_script="I received a suspicious screenshot but the vision tool could not read it. I need help verifying this message before I do anything.",
                    recommended_action="verify_independently",
                )

        # Clean visual risk clues: remove placeholder tokens
        raw_clues = vision_result.get("screenshot_risk_clues", [])
        cleaned_clues = _clean_visual_risk_clues(raw_clues, extracted_text)

        report = dataclasses.replace(
            report,
            evidence_source="text_and_screenshot" if has_text else "screenshot",
            image_evidence_present=True,
            vision_backend=vision_backend.backend_name,
            vision_model=vision_result.get("vision_model"),
            vision_status=v_status,
            vision_summary=vision_result.get("vision_summary"),
            extracted_text=vision_result.get("extracted_text"),
            screenshot_type=vision_result.get("screenshot_type"),
            screenshot_risk_clues=cleaned_clues,
            recommended_text_for_analysis=vision_result.get("recommended_text_for_analysis"),
            vision_confidence=v_confidence,
            vision_error=vision_result.get("vision_error"),
            effective_input_text=text_for_analysis,
            input_sources=input_sources,
            analysis_used_vision_text=bool(extracted_text),
        )
    else:
        # Text-only analysis
        report = dataclasses.replace(
            report,
            effective_input_text=text_for_analysis,
            input_sources=input_sources,
            analysis_used_vision_text=False,
        )

    gauge = _render_gauge(report.risk_score, report.judge_verdict, report.judge_rationale)
    report_dict = report.to_dict()
    json_export = report.to_json()
    shield = render_shield(report_dict)
    vision_html = render_vision_witness(report_dict)
    whatsapp = render_companion_whatsapp(report_dict)
    sms = render_companion_sms(report_dict)
    marketplace = render_companion_marketplace(report_dict)
    return gauge, report_dict, json_export, shield, vision_html, whatsapp, sms, marketplace


# ---------------------------------------------------------------------------
# Random example loader
# ---------------------------------------------------------------------------
def load_random_example() -> str:
    return random.choice(EXAMPLES)["text"]


# ---------------------------------------------------------------------------
# Role switching factory
# ---------------------------------------------------------------------------
def _make_switch(role: str):
    def _switch(report: dict | None) -> tuple[str, str]:
        return _render_indicator(role), _render_role(role, report)
    return _switch


def _show_detective(report: dict | None) -> tuple[str, str]:
    return _render_indicator("detective"), _render_role("detective", report)


def _render_backend_status() -> str:
    """Render backend status pills for the utility bar."""
    import os
    import sys
    text_backend = getattr(backend, "model_backend", "heuristic_v1")
    vision = get_vision_backend()
    vision_name = vision.backend_name
    vision_dot = "off" if vision_name == "none" else ""
    hf_home = os.getenv("HF_HOME", "~/.cache/huggingface")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    return (
        f'<span class="backend-status">{_t("backend_text")}: {text_backend}</span>'
        f'<span class="backend-status">{_t("backend_vision")}: {vision_name} <span class="dot {vision_dot}"></span></span>'
        f'<span class="backend-status">{_t("backend_model")}: {get_vision_model_id()}</span>'
        f'<span class="backend-status">{_t("backend_cache")}: {hf_home}</span>'
        f'<span class="backend-status">Py: {py_ver}</span>'
    )


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Scam Court AI",
        css=_build_css(_role_subtitles_for_theme()),
    ) as demo:
        # ── Hero ──
        gr.HTML(
            f"""
            <div id="court-header">
                <h1>Scam Court AI</h1>
                <p>{html.escape(_t("app_subtitle"))}</p>
            </div>
            <script>
            (function() {{
              function applyTheme(t) {{
                document.body.classList.toggle("light", t === "light");
                try {{ localStorage.setItem("scam-court-theme", t); }} catch(e) {{}}
              }}
              function applyLang(l) {{
                try {{ localStorage.setItem("scam-court-lang", l); }} catch(e) {{}}
                if (l !== "{_current_lang}") {{
                  const url = new URL(window.location.href);
                  url.searchParams.set("__lang", l);
                  window.location.replace(url.toString());
                }}
              }}
              var storedTheme = null;
              var storedLang = null;
              try {{
                storedTheme = localStorage.getItem("scam-court-theme");
                storedLang = localStorage.getItem("scam-court-lang");
              }} catch(e) {{}}
              var initialTheme = storedTheme || "{_current_theme}";
              var initialLang = storedLang || "{_current_lang}";
              applyTheme(initialTheme);
              window._scamCourtSetTheme = applyTheme;
              window._scamCourtSetLang = applyLang;
              var selT = document.getElementById("sc-theme");
              var selL = document.getElementById("sc-lang");
              if (selT) selT.value = initialTheme;
              if (selL) selL.value = initialLang;
              if (initialLang !== "{_current_lang}" && !window.location.search.includes("__lang=")) {{
                applyLang(initialLang);
              }}
            }})();
            </script>
            """
        )

        report_state = gr.State(None)
        lang_state = gr.State(_current_lang)
        theme_state = gr.State(_current_theme)

        with gr.Tabs(elem_classes=["mode-tabs"]):
            # ── Shield Mode ──
            with gr.Tab(_t("tab_shield")):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel"]):
                        gr.Markdown(f'<div class="section-label">{html.escape(_t("section_submit_evidence"))}</div>')
                        shield_input = gr.Textbox(
                            label="",
                            placeholder=_t("input_placeholder"),
                            lines=10,
                            max_lines=18,
                            show_label=False,
                        )
                        gr.Markdown(
                            f'<div class="section-label" style="margin-top:1.2rem;">{html.escape(_t("upload_screenshot"))}</div>'
                        )
                        shield_image = gr.Image(
                            label="",
                            type="filepath",
                            sources=["upload"],
                            interactive=True,
                            show_label=False,
                        )
                        gr.Markdown(
                            f'<div style="font-size:0.75rem;color:var(--text-tertiary);margin-top:0.4rem;">{html.escape(_t("upload_hint"))}</div>'
                        )
                        with gr.Row():
                            shield_submit = gr.Button(_t("btn_analyze"), variant="primary")
                            shield_random = gr.Button(_t("btn_random_example"), elem_classes=["secondary"])
                            shield_clear = gr.Button(_t("btn_clear"), elem_classes=["secondary"])
                        gr.Markdown(f'<div class="section-label" style="margin-top:1.5rem;">{html.escape(_t("quick_examples"))}</div>')
                        shield_example_btns = []
                        for label, text in EXAMPLE_BUTTONS:
                            btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                            shield_example_btns.append((btn, text))

                    with gr.Column(scale=2):
                        shield_output = gr.HTML()
                        shield_vision = gr.HTML()

            # ── Court Mode ──
            with gr.Tab(_t("tab_court")):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel"]):
                        gr.Markdown(f'<div class="section-label">{html.escape(_t("court_input_label"))}</div>')
                        court_input = gr.Textbox(
                            label="",
                            placeholder=_t("input_placeholder"),
                            lines=10,
                            max_lines=18,
                            show_label=False,
                        )
                        gr.Markdown(
                            f'<div class="section-label" style="margin-top:1.2rem;">{html.escape(_t("upload_screenshot"))}</div>'
                        )
                        court_image = gr.Image(
                            label="",
                            type="filepath",
                            sources=["upload"],
                            interactive=True,
                            show_label=False,
                        )
                        gr.Markdown(
                            f'<div style="font-size:0.75rem;color:var(--text-tertiary);margin-top:0.4rem;">{html.escape(_t("upload_hint"))}</div>'
                        )
                        with gr.Row():
                            court_submit = gr.Button(_t("btn_analyze_court"), variant="primary")
                            court_random = gr.Button(_t("btn_random_example"), elem_classes=["secondary"])
                            court_clear = gr.Button(_t("btn_clear"), elem_classes=["secondary"])

                        gr.Markdown(f'<div class="section-label" style="margin-top:1.5rem;">{html.escape(_t("quick_examples"))}</div>')
                        court_example_btns = []
                        for label, text in EXAMPLE_BUTTONS:
                            btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                            court_example_btns.append((btn, text))

                    with gr.Column(scale=2):
                        risk_gauge = gr.HTML()
                        court_vision = gr.HTML()

                        gr.Markdown(f'<div class="section-label">{html.escape(_t("court_members"))}</div>')
                        with gr.Row(elem_classes=["role-selector"]):
                            btn_detective = gr.Button(_t("role_detective"), elem_classes=["role-btn", "role-btn-detective"])
                            btn_prosecutor = gr.Button(_t("role_prosecutor"), elem_classes=["role-btn", "role-btn-prosecutor"])
                            btn_defender = gr.Button(_t("role_defender"), elem_classes=["role-btn", "role-btn-defender"])
                            btn_judge = gr.Button(_t("role_judge"), elem_classes=["role-btn", "role-btn-judge"])
                            btn_clerk = gr.Button(_t("role_clerk"), elem_classes=["role-btn", "role-btn-clerk"])

                        active_indicator = gr.HTML(_render_indicator(None))
                        role_display = gr.HTML()

                        with gr.Accordion(_t("export_accordion"), open=False):
                            json_out = gr.Code(language="json", label=_t("export_json"))

            # ── Suspicious Call Quick Check ──
            with gr.Tab(_t("tab_call")):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel", "call-check"]):
                        gr.Markdown(f'<div class="section-label">{html.escape(_t("call_title"))}</div>')
                        gr.Markdown(f'<div style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:1rem;">{html.escape(_t("call_hint"))}</div>')
                        chk_money = gr.Checkbox(label=_t("call_money"), elem_classes=["call-factor"], container=False)
                        chk_code = gr.Checkbox(label=_t("call_code"), elem_classes=["call-factor"], container=False)
                        chk_family = gr.Checkbox(label=_t("call_family"), elem_classes=["call-factor"], container=False)
                        chk_urgency = gr.Checkbox(label=_t("call_urgency"), elem_classes=["call-factor"], container=False)
                        chk_secrecy = gr.Checkbox(label=_t("call_secrecy"), elem_classes=["call-factor"], container=False)
                        with gr.Row():
                            call_submit = gr.Button(_t("btn_check_call"), variant="primary")
                            call_clear = gr.Button(_t("btn_reset"), elem_classes=["secondary"])
                    with gr.Column(scale=2):
                        call_output = gr.HTML()

            # ── Companion Preview ──
            with gr.Tab(_t("tab_companion")):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["input-panel"]):
                        gr.Markdown(f'<div class="section-label">{html.escape(_t("companion_title"))}</div>')
                        companion_input = gr.Textbox(
                            label="",
                            placeholder=_t("input_placeholder"),
                            lines=10,
                            max_lines=18,
                            show_label=False,
                        )
                        with gr.Row():
                            companion_submit = gr.Button(_t("companion_btn_analyze"), variant="primary")
                            companion_random = gr.Button(_t("btn_random_example"), elem_classes=["secondary"])
                            companion_clear = gr.Button(_t("btn_clear"), elem_classes=["secondary"])
                        gr.Markdown(f'<div class="section-label" style="margin-top:1.5rem;">{html.escape(_t("quick_examples"))}</div>')
                        companion_example_btns = []
                        for label, text in EXAMPLE_BUTTONS:
                            btn = gr.Button(label, elem_classes=["example-btn"], size="sm")
                            companion_example_btns.append((btn, text))

                    with gr.Column(scale=2):
                        companion_vision = gr.HTML()
                        with gr.Tabs():
                            with gr.Tab(_t("companion_whatsapp_tab")):
                                companion_whatsapp = gr.HTML()
                            with gr.Tab(_t("companion_sms_tab")):
                                companion_sms = gr.HTML()
                            with gr.Tab(_t("companion_marketplace_tab")):
                                companion_marketplace = gr.HTML()

        # ── Shared events ──
        shield_submit.click(
            fn=analyze_message,
            inputs=[shield_input, shield_image],
            outputs=[risk_gauge, report_state, json_out, shield_output, shield_vision, companion_whatsapp, companion_sms, companion_marketplace],
        ).then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        court_submit.click(
            fn=analyze_message,
            inputs=[court_input, court_image],
            outputs=[risk_gauge, report_state, json_out, shield_output, court_vision, companion_whatsapp, companion_sms, companion_marketplace],
        ).then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        companion_submit.click(
            fn=analyze_message,
            inputs=[companion_input, gr.State(None)],
            outputs=[risk_gauge, report_state, json_out, shield_output, companion_vision, companion_whatsapp, companion_sms, companion_marketplace],
        ).then(
            fn=_show_detective,
            inputs=report_state,
            outputs=[active_indicator, role_display],
        )

        btn_detective.click(fn=_make_switch("detective"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_prosecutor.click(fn=_make_switch("prosecutor"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_defender.click(fn=_make_switch("defender"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_judge.click(fn=_make_switch("judge"), inputs=report_state, outputs=[active_indicator, role_display])
        btn_clerk.click(fn=_make_switch("clerk"), inputs=report_state, outputs=[active_indicator, role_display])

        call_submit.click(
            fn=analyze_call_checklist,
            inputs=[chk_money, chk_code, chk_family, chk_urgency, chk_secrecy],
            outputs=call_output,
        )
        call_clear.click(
            fn=lambda: (False, False, False, False, False, ""),
            outputs=[chk_money, chk_code, chk_family, chk_urgency, chk_secrecy, call_output],
        )

        shield_random.click(fn=load_random_example, outputs=shield_input)
        court_random.click(fn=load_random_example, outputs=court_input)
        companion_random.click(fn=load_random_example, outputs=companion_input)
        for btn, text in shield_example_btns:
            btn.click(fn=lambda t=text: t, outputs=shield_input)
        for btn, text in court_example_btns:
            btn.click(fn=lambda t=text: t, outputs=court_input)
        for btn, text in companion_example_btns:
            btn.click(fn=lambda t=text: t, outputs=companion_input)

        def _clear_all():
            return (
                None, None, None,
                "", "", "",
                _render_gauge(0, _t("gauge_waiting"), _t("gauge_waiting_rationale")),
                None,
                "",
                _render_indicator(None),
                "",
                render_shield(None),
                "", "", "",
                render_companion_whatsapp(None),
                render_companion_sms(None),
                render_companion_marketplace(None),
            )

        shield_clear.click(
            fn=_clear_all,
            outputs=[
                shield_image, court_image, gr.State(None),
                shield_input, court_input, companion_input,
                risk_gauge, report_state, json_out,
                active_indicator, role_display,
                shield_output, shield_vision, court_vision, companion_vision,
                companion_whatsapp, companion_sms, companion_marketplace,
            ],
        )
        court_clear.click(
            fn=_clear_all,
            outputs=[
                shield_image, court_image, gr.State(None),
                shield_input, court_input, companion_input,
                risk_gauge, report_state, json_out,
                active_indicator, role_display,
                shield_output, shield_vision, court_vision, companion_vision,
                companion_whatsapp, companion_sms, companion_marketplace,
            ],
        )
        companion_clear.click(
            fn=_clear_all,
            outputs=[
                shield_image, court_image, gr.State(None),
                shield_input, court_input, companion_input,
                risk_gauge, report_state, json_out,
                active_indicator, role_display,
                shield_output, shield_vision, court_vision, companion_vision,
                companion_whatsapp, companion_sms, companion_marketplace,
            ],
        )

        # ── Premium utility bar ──
        gr.HTML(
            f"""
            <div class="utility-bar">
              <div class="utility-section">
                <div class="utility-brand">Scam Court AI</div>
              </div>
              <div class="utility-section">
                <span class="utility-section-label">System</span>
                <div class="utility-meta">
                  {_render_backend_status()}
                </div>
              </div>
              <div class="utility-section">
                <span class="utility-section-label">Settings</span>
                <div class="utility-controls">
                  <div class="utility-pill">
                    <label for="sc-lang" style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.6px;font-weight:700;margin-right:0.3rem;opacity:0.6;">{html.escape(_t("lang_label"))}</label>
                    <select id="sc-lang" onchange="window._scamCourtSetLang(this.value)">
                      <option value="en" {"selected" if _current_lang == "en" else ""}>English</option>
                      <option value="es" {"selected" if _current_lang == "es" else ""}>Español</option>
                    </select>
                  </div>
                  <div class="utility-pill">
                    <label for="sc-theme" style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.6px;font-weight:700;margin-right:0.3rem;opacity:0.6;">{html.escape(_t("theme_label"))}</label>
                    <select id="sc-theme" onchange="window._scamCourtSetTheme(this.value)">
                      <option value="dark" {"selected" if _current_theme == "dark" else ""}>{html.escape(_t("theme_dark"))}</option>
                      <option value="light" {"selected" if _current_theme == "light" else ""}>{html.escape(_t("theme_light"))}</option>
                    </select>
                  </div>
                </div>
              </div>
              </div>
            </div>
            """
        )

    return demo


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "7860"))
    print(
        "[startup] "
        f"text_backend={getattr(backend, 'model_backend', 'heuristic_v1')} "
        f"vision_backend={get_vision_backend().backend_name} "
        f"vision_model={get_vision_model_id()} "
        f"spaces_import_succeeded={SPACES_IMPORT_SUCCEEDED} "
        f"zero_gpu_decorator_active={ZERO_GPU_DECORATOR_ACTIVE} "
        f"zero_gpu_runtime_active={ZERO_GPU_RUNTIME_ACTIVE} "
        f"port={port}",
        flush=True,
    )
    demo = build_ui()
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
    )
