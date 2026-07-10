import json
import os
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class I18n:
    """Internationalization service"""

    def __init__(self, locales_path: str = "src/bot/locales"):
        self.locales_path = locales_path
        self.translations: dict[str, dict] = {}
        self.default_language = "en"
        self._load_locales()

    def _load_locales(self) -> None:
        """Load all locale files"""
        try:
            for file in os.listdir(self.locales_path):
                if file.endswith(".json"):
                    lang = file.replace(".json", "")
                    filepath = os.path.join(self.locales_path, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                    logger.info("Locale loaded", language=lang)
        except Exception as e:
            logger.error("Failed to load locales", error=str(e))

    def get_text(self, key: str, language: str = "en") -> str:
        """Get translated text by key"""
        if language not in self.translations:
            language = self.default_language

        text = self.translations.get(language, {}).get(key)
        if text is None:
            text = self.translations.get(self.default_language, {}).get(key, key)
            logger.warning("Translation not found", key=key, language=language)

        return text

    def __call__(self, key: str, language: str = "en") -> str:
        """Allow using i18n as callable"""
        return self.get_text(key, language)


# Global i18n instance
i18n = I18n()
