"""UI helpers for Scam Court AI."""

from .i18n import DEFAULT_LANG, TRANSLATIONS, normalize_lang, t, theme_choices
from .styles import PAGE_JS, build_css

__all__ = [
    "DEFAULT_LANG",
    "PAGE_JS",
    "TRANSLATIONS",
    "build_css",
    "normalize_lang",
    "t",
    "theme_choices",
]
