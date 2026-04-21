import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
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
        """Apply /addword semantics and return user-facing result text."""

        keyword = keyword.strip().lower()
        if not validate_word(keyword):
            return "Usage: /addword <слово>. No special characters or spaces allowed."

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        masked_keyword = mask_word(keyword, mask_char=self._store.get_mask_char(chat_id))
        added = self._store.add_keyword(chat_id, keyword)
        result_text = f"Added: {masked_keyword}" if added else f"Already exists: {masked_keyword}"
        return result_text

    def build_removeword_command_result(
        self,
        chat_id: int,
        command_text: str,
        keyword: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Apply /removeword semantics and return user-facing result text."""

        keyword = keyword.strip().lower()
        if not validate_word(keyword):
            return "Usage: /removeword <слово>. No special characters or spaces allowed."

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        masked_keyword = mask_word(keyword, mask_char=self._store.get_mask_char(chat_id))
        removed = self._store.remove_keyword(chat_id, keyword)
        result_text = f"Removed: {masked_keyword}" if removed else f"Not found: {masked_keyword}"
        return result_text

    def build_listwords_command_result(
        self,
        chat_id: int,
        command_text: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Build /listwords reply text with configured keywords."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        keywords = self._store.list_keywords(chat_id)
        if not keywords:
            return "Keyword list is empty."

        mask_char = self._store.get_mask_char(chat_id)
        body = "\n".join(f"- {mask_word(word, mask_char=mask_char)}" for word in keywords)
        result_text = f"Configured keywords:\n{body}"
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
            return "Usage: /mask_char <1 symbol>"

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        self._store.update_mask_char(chat_id, normalized)
        result_text = f"Mask char updated to: {normalized}"
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
        return "Settings reset to defaults."

    def build_stats_command_result(
        self,
        chat_id: int,
        command_text: str,
        chat_name: Optional[str] = None,
    ) -> str:
        """Return top 10 keywords and top authors by moderation count for a chat."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        keyword_stats = self._store.get_keyword_stats(chat_id, limit=10)
        author_stats = self._store.get_author_stats(chat_id, limit=10)
        if not keyword_stats and not author_stats:
            return "No statistics yet."

        mask_char = self._store.get_mask_char(chat_id)
        result_parts = []
        if keyword_stats:
            keywords_body = "\n".join(f"{mask_word(word, mask_char=mask_char)} - {count}" for word, count in keyword_stats)
            result_parts.append(f"Top moderated keywords:\n{keywords_body}")
        if author_stats:
            authors_body = "\n".join(f"{author} - {count}" for author, count in author_stats)
            result_parts.append(f"\nTop moderated authors:\n{authors_body}")
        result_text = "\n".join(result_parts)
        return result_text

    def log_caught_message(
        self,
        chat_id: int,
        user_id: int,
        user_name: str,
        original_text: str,
        censored_text: str,
        triggered_keywords: list[str],
    ) -> None:
        """Log a moderation event to database and file in JSON format."""

        # Build match_events to increment counters: count each keyword by occurrences
        match_events: list[str] = []
        for keyword in triggered_keywords:
            count = len(build_keyword_pattern(keyword).findall(original_text))
            if count > 0:
                match_events.extend([keyword] * count)

        # Increment match counts for triggered keywords
        if match_events:
            self._store.increment_keyword_match_count(chat_id, match_events)

        # Log event to database and JSON log
        self._log_event(
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            event_type="moderation",
            original_message=original_text,
            bot_response=censored_text,
        )

    def log_command(
        self,
        chat_id: int,
        user_id: int,
        user_name: str,
        original_text: str,
        bot_response: str,
    ) -> None:
        """Log a command event to database and file in JSON format."""

        self._log_event(
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            event_type="command",
            original_message=original_text,
            bot_response=bot_response,
        )

    def _log_event(
        self,
        chat_id: int,
        user_id: int,
        user_name: str,
        event_type: str,
        original_message: str,
        bot_response: str,
    ) -> None:
        """Internal helper to log events with consistent JSON format."""

        event_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "user_name": user_name,
            "event_type": event_type,
            "original_message": original_message,
            "bot_response": bot_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._store.insert_event(
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            event_type=event_type,
            original_message=original_message,
            bot_response=bot_response,
        )
        logger.info("event=%s", json.dumps(event_data, ensure_ascii=False))

    def moderate_text(self, chat_id: int, text: str, chat_name: Optional[str] = None) -> ModerationResult:
        """Check text for triggers and return moderation output. Event logging happens separately."""

        self._store.ensure_chat(chat_id=chat_id, chat_name=chat_name)
        mask_char = self._store.get_mask_char(chat_id)
        keywords = self._store.list_keywords(chat_id)
        triggered = find_triggered_keywords(text=text, keywords=keywords)
        if not triggered:
            return ModerationResult(matched=False, censored_text=text, triggered_keywords=[])

        censored = censor_text(text, triggered, mask_char=mask_char)
        return ModerationResult(
            matched=True,
            censored_text=censored,
            triggered_keywords=triggered,
        )
