import sqlite3
from typing import Iterable, Optional


class SQLiteKeywordStore:
    """SQLite-backed persistence for per-chat keyword configuration."""

    def __init__(
        self,
        db_path: str,
        default_mask_char: str,
        default_keywords: Iterable[str],
    ) -> None:
        """Open database connection and ensure schema exists."""

        self._default_mask_char = default_mask_char
        self._default_keywords = list(default_keywords)
        self._connection = sqlite3.connect(db_path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        """Create required tables if they do not already exist."""

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                chat_name TEXT NOT NULL,
                mask_char TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_keywords (
                chat_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                match_count INTEGER NOT NULL DEFAULT 0,
                active BOOLEAN NOT NULL DEFAULT 1,
                PRIMARY KEY (chat_id, keyword),
                FOREIGN KEY (chat_id) REFERENCES chat_settings(chat_id) ON DELETE CASCADE
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                original_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_settings(chat_id) ON DELETE CASCADE
            )
            """
        )
        self._connection.commit()

    def _insert_default_keywords(self, chat_id: int) -> None:
        """Insert default keywords for one chat with active=1."""

        for keyword in self._default_keywords:
            self._connection.execute(
                "INSERT OR IGNORE INTO chat_keywords(chat_id, keyword, match_count, active) VALUES(?, ?, 0, 1)",
                (chat_id, keyword),
            )

    def ensure_chat(
        self,
        chat_id: int,
        chat_name: Optional[str] = None,
    ) -> None:
        """Make sure chat exists in DB or initialize chat settings and optional default keywords once."""

        chat_name = chat_name or ""
        row = self._connection.execute(
            "SELECT chat_name FROM chat_settings WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        if row:
            if chat_name and row[0] != chat_name:
                self._connection.execute(
                    "UPDATE chat_settings SET chat_name = ? WHERE chat_id = ?",
                    (chat_name, chat_id),
                )
                self._connection.commit()
            return

        self._connection.execute(
            "INSERT INTO chat_settings(chat_id, chat_name, mask_char) VALUES(?, ?, ?)",
            (chat_id, chat_name, self._default_mask_char),
        )
        self._insert_default_keywords(chat_id)
        self._connection.commit()

    def list_keywords(self, chat_id: int) -> list[str]:
        """Return sorted active keywords for a chat."""

        rows = self._connection.execute(
            "SELECT keyword FROM chat_keywords WHERE chat_id = ? AND active = 1 ORDER BY keyword",
            (chat_id,),
        ).fetchall()
        return [row[0] for row in rows]

    def get_mask_char(self, chat_id: int) -> str:
        """Return the configured mask char for a chat."""

        row = self._connection.execute(
            "SELECT mask_char FROM chat_settings WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        if row is None:
            return self._default_mask_char
        return str(row[0])

    def update_mask_char(self, chat_id: int, mask_char: str) -> None:
        """Persist a new mask char for a chat."""

        self._connection.execute(
            "UPDATE chat_settings SET mask_char = ? WHERE chat_id = ?",
            (mask_char, chat_id),
        )
        self._connection.commit()

    def reset_chat(
        self,
        chat_id: int
    ) -> None:
        """Reset one chat: mask char to default and deactivate non-default keywords."""

        self._connection.execute(
            "UPDATE chat_settings SET mask_char = ? WHERE chat_id = ?",
            (self._default_mask_char, chat_id),
        )
        # Deactivate all non-default keywords while preserving their match counts.
        if self._default_keywords:
            placeholders = ",".join("?" * len(self._default_keywords))
            self._connection.execute(
                f"UPDATE chat_keywords SET active = 0 WHERE chat_id = ? AND keyword NOT IN ({placeholders})",
                (chat_id, *self._default_keywords),
            )

            # Reactivate default keywords in case they were previously removed.
            self._connection.execute(
                f"UPDATE chat_keywords SET active = 1 WHERE chat_id = ? AND keyword IN ({placeholders})",
                (chat_id, *self._default_keywords),
            )
        else:
            # If there are no defaults configured, deactivate all chat keywords.
            self._connection.execute(
                "UPDATE chat_keywords SET active = 0 WHERE chat_id = ?",
                (chat_id,),
            )
        self._connection.commit()

    def add_keyword(self, chat_id: int, keyword: str) -> bool:
        """Insert new keyword or reactivate removed one. Return True if newly inserted."""

        # Try insert first
        cursor = self._connection.execute(
            "INSERT OR IGNORE INTO chat_keywords(chat_id, keyword, match_count, active) VALUES(?, ?, 0, 1)",
            (chat_id, keyword),
        )
        newly_added = cursor.rowcount > 0
        if not newly_added:
            # Already exists; if inactive, reactivate it
            self._connection.execute(
                "UPDATE chat_keywords SET active = 1 WHERE chat_id = ? AND keyword = ?",
                (chat_id, keyword),
            )
        self._connection.commit()
        return newly_added

    def remove_keyword(self, chat_id: int, keyword: str) -> bool:
        """Deactivate a keyword; return True when status changed. Stats persist."""

        cursor = self._connection.execute(
            "UPDATE chat_keywords SET active = 0 WHERE chat_id = ? AND keyword = ? AND active = 1",
            (chat_id, keyword),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def increment_keyword_match_count(self, chat_id: int, keywords: Iterable[str]) -> None:
        """Increment match counter for matched keywords in a chat."""

        for keyword in keywords:
            self._connection.execute(
                "UPDATE chat_keywords SET match_count = match_count + 1 WHERE chat_id = ? AND keyword = ?",
                (chat_id, keyword),
            )
        self._connection.commit()

    def get_keyword_stats(self, chat_id: int, limit: int = 10) -> list[tuple[str, int]]:
        """Return top keywords by match count for a chat, sorted descending."""

        rows = self._connection.execute(
            "SELECT keyword, match_count FROM chat_keywords WHERE chat_id = ? ORDER BY match_count DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
        return rows

    def insert_event(
        self,
        chat_id: int,
        user_id: int,
        user_name: str,
        event_type: str,
        original_message: str,
        bot_response: str,
    ) -> None:
        """Insert an event record into the events table."""

        self._connection.execute(
            """
            INSERT INTO events (chat_id, user_id, user_name, event_type, original_message, bot_response)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chat_id, user_id, user_name, event_type, original_message, bot_response),
        )
        self._connection.commit()

    def get_author_stats(self, chat_id: int, limit: int = 10) -> list[tuple[str, int]]:
        """Return top authors by moderation count (grouped by user_id with latest user_name), sorted descending."""

        rows = self._connection.execute(
            """
            WITH latest_names AS (
                SELECT user_id, user_name, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id DESC) as rn
                FROM events
                WHERE chat_id = ? AND event_type = 'moderation'
            )
            SELECT latest_names.user_name, COUNT(e.id) as count
            FROM events e
            JOIN latest_names ON e.user_id = latest_names.user_id AND latest_names.rn = 1
            WHERE e.chat_id = ? AND e.event_type = 'moderation'
            GROUP BY e.user_id
            ORDER BY count DESC
            LIMIT ?
            """,
            (chat_id, chat_id, limit),
        ).fetchall()
        return rows
