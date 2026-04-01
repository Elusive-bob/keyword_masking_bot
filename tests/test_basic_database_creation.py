import tempfile
import unittest
from pathlib import Path

from bot.storage.sqlite_store import SQLiteKeywordStore
from tests._base import LoggedTestCase


class TestBasicDatabaseCreation(LoggedTestCase):
    def test_database_can_be_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "basic_test.db"
            store = SQLiteKeywordStore(str(db_path))
            # Touch the DB through API to ensure schema is usable.
            store.ensure_chat(chat_id=100, default_keywords=["путин"])

            exists = db_path.exists()
            keywords = store.list_keywords(100)
            output = {"db_exists": exists, "keywords": keywords}
            self.set_test_log(
                module_object="bot/storage/sqlite_store.py::SQLiteKeywordStore",
                test_arguments=f"db_path={str(db_path)!r}, chat_id=100, default_keywords=['путин']",
                asserted_output="{'db_exists': True, 'keywords': ['путин']}",
                output=repr(output),
            )

            self.assertTrue(exists)
            self.assertEqual(keywords, ["путин"])


if __name__ == "__main__":
    unittest.main()
