import tempfile
import unittest
from pathlib import Path

from bot.core.service import ModerationService
from bot.storage.sqlite_store import SQLiteKeywordStore


class TestModerationService(unittest.TestCase):
    def test_moderate_text_and_keyword_management(self) -> None:
        self._log_details = (
            "targets bot/core/service.py::ModerationService with "
            "store=SQLiteKeywordStore(test.db), default_keywords=['путин'], mask_char='●', "
            "chat_id=1, added keyword='наркотик', text='Путина и наркотиком'"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            store = SQLiteKeywordStore(str(db_path))
            service = ModerationService(store=store, default_keywords=["путин"], mask_char="●")

            # Default keywords are seeded on first chat access.
            self.assertEqual(service.list_keywords(1), ["путин"])
            self.assertTrue(service.add_keyword(1, "наркотик"))
            self.assertFalse(service.add_keyword(1, "наркотик"))

            result = service.moderate_text(1, "Путина и наркотиком")
            self.assertTrue(result.matched)
            self.assertEqual(result.triggered_keywords, {"путин", "наркотик"})
            self.assertNotEqual(result.censored_text, "Путина и наркотиком")
            self.assertIn("●", result.censored_text)

            self.assertTrue(service.remove_keyword(1, "наркотик"))
            self.assertFalse(service.remove_keyword(1, "наркотик"))


if __name__ == "__main__":
    unittest.main()
