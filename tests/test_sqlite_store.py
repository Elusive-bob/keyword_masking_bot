import tempfile
import unittest
from pathlib import Path

from bot.storage.sqlite_store import SQLiteKeywordStore


class TestSQLiteKeywordStore(unittest.TestCase):
    def test_ensure_chat_and_keyword_crud(self) -> None:
        self._log_details = (
            "targets bot/storage/sqlite_store.py::SQLiteKeywordStore with db='test.db', "
            "chat_id=1, default_keywords=['Путин','наркотик',''], add='Амфетамин', remove='Амфетамин'"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            store = SQLiteKeywordStore(str(db_path))

            store.ensure_chat(1, ["Путин", "наркотик", ""]) 
            self.assertEqual(store.list_keywords(1), ["наркотик", "путин"])

            self.assertFalse(store.add_keyword(1, "   "))
            self.assertTrue(store.add_keyword(1, "Амфетамин"))
            self.assertFalse(store.add_keyword(1, "амфетамин"))

            self.assertEqual(store.list_keywords(1), ["амфетамин", "наркотик", "путин"])

            self.assertTrue(store.remove_keyword(1, "Амфетамин"))
            self.assertFalse(store.remove_keyword(1, "Амфетамин"))
            self.assertEqual(store.list_keywords(1), ["наркотик", "путин"])

    def test_ensure_chat_is_idempotent(self) -> None:
        self._log_details = (
            "targets bot/storage/sqlite_store.py::SQLiteKeywordStore.ensure_chat with "
            "chat_id=10, first defaults=['путин'], second defaults=['другое']; expects first seed only"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            store = SQLiteKeywordStore(str(db_path))

            store.ensure_chat(10, ["путин"])
            store.ensure_chat(10, ["другое"])

            self.assertEqual(store.list_keywords(10), ["путин"])


if __name__ == "__main__":
    unittest.main()
