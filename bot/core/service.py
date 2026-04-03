import logging
from dataclasses import dataclass
from typing import Optional

from bot.core.censorer import censor_text, mask_word
from bot.core.matcher import build_keyword_pattern, find_triggered_keywords
from bot.core.validator import validate_mask_char, validate_word
from bot.storage.sqlite_store import SQLiteKeywordStore


logger = logging.getLogger("bot.service")


@dataclass
class ModerationResult:
    """Result of checking a single text payload against chat keywords."""

    matched: bool
    censored_text: str
    triggered_keywords: list[str]


class ModerationService:
    """Chat-scoped moderation operations backed by keyword storage."""

    def __init__(
        self,
        store: SQLiteKeywordStore,
    ) -> None:
        """Initialize service with storage."""

        self._store = store

    def build_addword_command_result(
        self,
        chat_id: int,
        command_text: str,
        keyword: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Apply /addword semantics, return user-facing result text, and log it."""

        keyword = keyword.strip().lower()
        if not validate_word(keyword):
            logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, "Usage: /addword <слово>. No special characters or spaces.")
            return "Usage: /addword <слово>. No special characters or spaces allowed."

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        masked_keyword = mask_word(keyword, mask_char=self._store.get_mask_char(chat_id))
        added = self._store.add_keyword(chat_id, keyword)
        result_text = f"Added: {masked_keyword}" if added else f"Already exists: {masked_keyword}"
        logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, result_text)
        return result_text

    def build_removeword_command_result(
        self,
        chat_id: int,
        command_text: str,
        keyword: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Apply /removeword semantics, return user-facing result text, and log it."""

        keyword = keyword.strip().lower()
        if not validate_word(keyword):
            logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, "Usage: /removeword <слово>. No special characters or spaces.")
            return "Usage: /removeword <слово>. No special characters or spaces allowed."

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        masked_keyword = mask_word(keyword, mask_char=self._store.get_mask_char(chat_id))
        removed = self._store.remove_keyword(chat_id, keyword)
        result_text = f"Removed: {masked_keyword}" if removed else f"Not found: {masked_keyword}"
        logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, result_text)
        return result_text

    def build_listwords_command_result(
        self,
        chat_id: int,
        command_text: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Build /listwords reply text and log a single command result line."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        keywords = self._store.list_keywords(chat_id)
        if not keywords:
            logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, "Keyword list is empty.")
            return "Keyword list is empty."

        mask_char = self._store.get_mask_char(chat_id)
        body = "\n".join(f"- {mask_word(word, mask_char=mask_char)}" for word in keywords)
        result_text = f"Configured keywords:\n{body}"
        logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, result_text)
        return result_text

    def build_mask_char_command_result(
        self,
        chat_id: int,
        command_text: str,
        new_mask_char: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Validate and persist a new mask char for one chat."""

        normalized = new_mask_char.strip()
        if not validate_mask_char(normalized):
            logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, "Usage: /mask_char <1 symbol>")
            return "Usage: /mask_char <1 symbol>"

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        self._store.update_mask_char(chat_id, normalized)
        result_text = f"Mask char updated to: {normalized}"
        logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, result_text)
        return result_text

    def build_reset_command_result(
        self,
        chat_id: int,
        command_text: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Reset one chat back to default keywords and default mask char."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        self._store.reset_chat(chat_id=chat_id)
        logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, "Settings reset to defaults.")
        return "Settings reset to defaults."

    def build_stats_command_result(
        self,
        chat_id: int,
        command_text: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Return top 10 moderated keywords for a chat with their match counts."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        stats = self._store.get_keyword_stats(chat_id, limit=10)
        if not stats:
            logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, "No statistics yet.")
            return "No statistics yet."

        mask_char = self._store.get_mask_char(chat_id)
        body = "\n".join(f"{mask_word(word, mask_char=mask_char)} - {count}" for word, count in stats)
        result_text = f"Top moderated keywords:\n{body}"
        logger.info("chat_id=%s cmd=%r res=%r", chat_id, command_text, result_text)
        return result_text

    def log_caught_message(self, chat_id: int, caught_text: str, corrected_text: str) -> None:
        """Log a single moderation event line for a caught and corrected message."""

        logger.info(
            "chat_id=%s msg=%r res=%r",
            chat_id,
            caught_text,
            corrected_text,
        )

    def moderate_text(self, chat_id: int, text: str, chat_name: Optional[str] = None) -> ModerationResult:
        """Check text for triggers, increment counters, and return moderation output."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        mask_char = self._store.get_mask_char(chat_id)
        keywords = self._store.list_keywords(chat_id)
        triggered = find_triggered_keywords(text=text, keywords=keywords)
        if not triggered:
            return ModerationResult(matched=False, censored_text=text, triggered_keywords=[])

        match_events: list[str] = []
        for keyword in triggered:
            count = len(build_keyword_pattern(keyword).findall(text))
            if count > 0:
                match_events.extend([keyword] * count)
        self._store.increment_keyword_match_count(chat_id, match_events)
        censored = censor_text(text, triggered, mask_char=mask_char)
        return ModerationResult(
            matched=True,
            censored_text=censored,
            triggered_keywords=triggered,
        )
