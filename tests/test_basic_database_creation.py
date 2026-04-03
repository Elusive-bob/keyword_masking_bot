import tempfile
import unittest
from pathlib import Path

from bot.storage.sqlite_store import SQLiteKeywordStore
from tests._base import LoggedTestCase


class TestBasicDatabaseCreation(LoggedTestCase):
    def test_database_can_be_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "basic_test.db"
            store = SQLiteKeywordStore(
                str(db_path),
                default_mask_char="#",
                default_keywords=["путин"],
            )
            # Touch the DB through API to ensure schema is usable.
            store.ensure_chat(chat_id=100, chat_name="Test Chat")

            exists = db_path.exists()
            keywords = store.list_keywords(100)
            settings_row = store._connection.execute(
                "SELECT chat_name, mask_char FROM chat_settings WHERE chat_id = ?",
                (100,),
            ).fetchone()
            columns = [
                row[1]
                for row in store._connection.execute("PRAGMA table_info(chat_settings)").fetchall()
            ]
            output = {
                "db_exists": exists,
                "keywords": keywords,
                "settings": settings_row,
                "columns": columns,
            }
            self.set_test_log(
                module_object="bot/storage/sqlite_store.py::SQLiteKeywordStore",
                test_arguments=(
                    f"db_path={str(db_path)!r}, chat_id=100, default_keywords=['путин'], "
                    "chat_name='Test Chat', default_mask_char='#'"
                ),
                asserted_output=(
                    "{'db_exists': True, 'keywords': ['путин'], "
                    "'settings': ('Test Chat', '#'), "
                    "'columns': ['chat_id', 'chat_name', 'mask_char']}"
                ),
                output=repr(output),
            )

            self.assertTrue(exists)
            self.assertEqual(keywords, ["путин"])
            self.assertEqual(settings_row, ("Test Chat", "#"))
            self.assertEqual(columns, ["chat_id", "chat_name", "mask_char"])


if __name__ == "__main__":
    unittest.main()
