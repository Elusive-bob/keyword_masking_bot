import sqlite3
from typing import Iterable


class SQLiteKeywordStore:
    """SQLite-backed persistence for per-chat keyword configuration."""

    def __init__(self, db_path: str) -> None:
        """Open database connection and ensure schema exists."""

        self._connection = sqlite3.connect(db_path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        """Create required tables if they do not already exist."""

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                initialized INTEGER NOT NULL DEFAULT 1
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

    def ensure_chat(self, chat_id: int, default_keywords: Iterable[str]) -> None:
        """Initialize chat settings and optional default keywords once."""

        row = self._connection.execute(
            "SELECT 1 FROM chat_settings WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        if row:
            return

        self._connection.execute(
            "INSERT INTO chat_settings(chat_id, initialized) VALUES(?, 1)",
            (chat_id,),
        )
        for keyword in default_keywords:
            normalized = keyword.strip().lower()
            if normalized:
                self._connection.execute(
                    "INSERT OR IGNORE INTO chat_keywords(chat_id, keyword) VALUES(?, ?)",
                    (chat_id, normalized),
                )
        self._connection.commit()

    def list_keywords(self, chat_id: int) -> list[str]:
        """Return sorted keywords for a chat."""

        rows = self._connection.execute(
            "SELECT keyword FROM chat_keywords WHERE chat_id = ? ORDER BY keyword",
            (chat_id,),
        ).fetchall()
        return [row[0] for row in rows]

    def add_keyword(self, chat_id: int, keyword: str) -> bool:
        """Insert a normalized keyword; return True when newly added."""

        normalized = keyword.strip().lower()
        if not normalized:
            return False

        cursor = self._connection.execute(
            "INSERT OR IGNORE INTO chat_keywords(chat_id, keyword) VALUES(?, ?)",
            (chat_id, normalized),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def remove_keyword(self, chat_id: int, keyword: str) -> bool:
        """Delete a normalized keyword; return True when removed."""

        normalized = keyword.strip().lower()
        if not normalized:
            return False

        cursor = self._connection.execute(
            "DELETE FROM chat_keywords WHERE chat_id = ? AND keyword = ?",
            (chat_id, normalized),
        )
        self._connection.commit()
        return cursor.rowcount > 0
