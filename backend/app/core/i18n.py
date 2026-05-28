"""Simple i18n for Jinja2 templates — Chinese ↔ English."""

import json
import os
from functools import lru_cache
from pathlib import Path

_TRANSLATIONS_DIR = Path(__file__).resolve().parent.parent / "translations"

# Supported languages
LANGUAGES: dict[str, str] = {
    "zh": "中文",
    "en": "English",
}

DEFAULT_LANG = "en"


@lru_cache(maxsize=2)
def _load_translations(lang: str) -> dict[str, str]:
    """Load translations for *lang* from its JSON file (cached)."""
    path = _TRANSLATIONS_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_translator(lang: str):
    """Return a ``_(text) -> str`` callable for the given language.

    The key is the Chinese source text.  If no translation is found the
    key itself is returned, so templates always render something readable.
    """
    translations = _load_translations(lang)

    def _(text: str) -> str:
        return translations.get(text, text)

    # Expose the language code for templates
    _.lang = lang if lang in LANGUAGES else DEFAULT_LANG  # type: ignore[attr-defined]
    return _


def detect_lang(accept_language: str = "", cookie_lang: str = "") -> str:
    """Pick the best language.

    Priority:  cookie > DEFAULT_LANG (accept-language is ignored
    so first-time visitors always see Chinese — switch via the UI).
    """
    if cookie_lang in LANGUAGES:
        return cookie_lang
    return DEFAULT_LANG
