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
                PRIMARY KEY (chat_id, keyword),
                FOREIGN KEY (chat_id) REFERENCES chat_settings(chat_id) ON DELETE CASCADE
            )
            """
        )
        self._connection.commit()

    def _insert_default_keywords(self, chat_id: int) -> None:
        """Insert keywords for one chat."""

        for keyword in self._default_keywords:
            self._connection.execute(
                "INSERT OR IGNORE INTO chat_keywords(chat_id, keyword) VALUES(?, ?)",
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
        """Return sorted keywords for a chat."""

        rows = self._connection.execute(
            "SELECT keyword FROM chat_keywords WHERE chat_id = ? ORDER BY keyword",
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
        """Reset one chat back to the configured defaults."""

        self._connection.execute(
            "UPDATE chat_settings SET mask_char = ? WHERE chat_id = ?",
            (self._default_mask_char, chat_id),
        )
        self._connection.execute(
            "DELETE FROM chat_keywords WHERE chat_id = ?",
            (chat_id,),
        )
        self._insert_default_keywords(chat_id)
        self._connection.commit()

    def add_keyword(self, chat_id: int, keyword: str) -> bool:
        """Insert a keyword; return True when newly added."""

        cursor = self._connection.execute(
            "INSERT OR IGNORE INTO chat_keywords(chat_id, keyword) VALUES(?, ?)",
            (chat_id, keyword),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def remove_keyword(self, chat_id: int, keyword: str) -> bool:
        """Delete a keyword; return True when removed."""

        cursor = self._connection.execute(
            "DELETE FROM chat_keywords WHERE chat_id = ? AND keyword = ?",
            (chat_id, keyword),
        )
        self._connection.commit()
        return cursor.rowcount > 0
