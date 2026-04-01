from dataclasses import dataclass

from bot.core.censorer import censor_text, mask_word
from bot.core.matcher import find_triggered_keywords
from bot.storage.sqlite_store import SQLiteKeywordStore


@dataclass
class ModerationResult:
    """Result of checking a single text payload against chat keywords."""

    matched: bool
    censored_text: str
    triggered_keywords: set[str]


class ModerationService:
    """Chat-scoped moderation operations backed by keyword storage."""

    def __init__(self, store: SQLiteKeywordStore, default_keywords: list[str], mask_char: str = "●") -> None:
        """Initialize service with storage, default keywords, and mask symbol."""

        self._store = store
        self._default_keywords = [item.strip().lower() for item in default_keywords if item.strip()]
        self._mask_char = mask_char

    def ensure_chat(self, chat_id: int) -> None:
        """Ensure a chat has initialized keyword settings in storage."""

        self._store.ensure_chat(chat_id=chat_id, default_keywords=self._default_keywords)

    def list_keywords(self, chat_id: int) -> list[str]:
        """Return current keyword list for a chat."""

        self.ensure_chat(chat_id)
        return self._store.list_keywords(chat_id)

    def add_keyword(self, chat_id: int, keyword: str) -> bool:
        """Add a keyword to chat settings; returns True when inserted."""

        self.ensure_chat(chat_id)
        return self._store.add_keyword(chat_id, keyword)

    def remove_keyword(self, chat_id: int, keyword: str) -> bool:
        """Remove a keyword from chat settings; returns True when removed."""

        self.ensure_chat(chat_id)
        return self._store.remove_keyword(chat_id, keyword)

    def mask_word(self, word: str) -> str:
        """Mask a word using the service mask character policy."""

        return mask_word(word, mask_char=self._mask_char)

    def moderate_text(self, chat_id: int, text: str) -> ModerationResult:
        """Check text for triggers and return moderation output."""

        self.ensure_chat(chat_id)
        keywords = self._store.list_keywords(chat_id)
        triggered = find_triggered_keywords(text=text, keywords=keywords)
        if not triggered:
            return ModerationResult(matched=False, censored_text=text, triggered_keywords=set())

        return ModerationResult(
            matched=True,
            censored_text=censor_text(text, triggered, mask_char=self._mask_char),
            triggered_keywords=triggered,
        )
