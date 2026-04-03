import tempfile
import unittest
from pathlib import Path

from bot.core.service import ModerationService
from bot.storage.sqlite_store import SQLiteKeywordStore
from tests._base import LoggedTestCase


class TestBasicChatSettings(LoggedTestCase):
    def test_chat_specific_mask_char_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "settings_test.db"
            store = SQLiteKeywordStore(
                str(db_path),
                default_mask_char="#",
                default_keywords=["путин"],
            )
            service = ModerationService(store=store)

            initial = service.moderate_text(
                chat_id=7,
                text="Путин здесь",
                chat_name="Group A",
            )
            invalid_result = service.build_mask_char_command_result(
                chat_id=7,
                command_text="/mask_char **",
                new_mask_char="**",
                chat_name="Group A",
            )
            changed_result = service.build_mask_char_command_result(
                chat_id=7,
                command_text="/mask_char *",
                new_mask_char="*",
                chat_name="Group A",
            )
            changed = service.moderate_text(
                chat_id=7,
                text="Путин здесь",
                chat_name="Group A",
            )
            store.ensure_chat(chat_id=7, chat_name="Group A")
            store.add_keyword(chat_id=7, keyword="тест")
            reset_result = service.build_reset_command_result(
                chat_id=7,
                command_text="/reset",
                chat_name="Group A",
            )
            reset = service.moderate_text(
                chat_id=7,
                text="Путин здесь",
                chat_name="Group A",
            )
            store.ensure_chat(chat_id=7, chat_name="Group A")
            keywords_after_reset = store.list_keywords(chat_id=7)
            stored_settings = store._connection.execute(
                "SELECT chat_name, mask_char FROM chat_settings WHERE chat_id = ?",
                (7,),
            ).fetchone()

            output = {
                "initial": initial.censored_text,
                "invalid": invalid_result,
                "changed_result": changed_result,
                "changed": changed.censored_text,
                "reset_result": reset_result,
                "reset": reset.censored_text,
                "keywords_after_reset": keywords_after_reset,
                "stored_settings": stored_settings,
            }
            self.set_test_log(
                module_object="bot/core/service.py::ModerationService",
                test_arguments=(
                    f"db_path={str(db_path)!r}, chat_id=7, default_keywords=['путин'], "
                    "default_mask_char='#', mask_char updates then reset"
                ),
                asserted_output=(
                    "{'initial': 'П#т#н здесь', 'invalid': 'Usage: /mask_char <1 symbol>', "
                    "'changed_result': 'Mask char updated to: *', 'changed': 'П*т*н здесь', "
                    "'reset_result': 'Settings reset to defaults.', 'reset': 'П#т#н здесь', "
                    "'keywords_after_reset': ['путин'], 'stored_settings': ('Group A', '#')}"
                ),
                output=repr(output),
            )

            self.assertEqual(initial.censored_text, "П#т#н здесь")
            self.assertEqual(invalid_result, "Usage: /mask_char <1 symbol>")
            self.assertEqual(changed_result, "Mask char updated to: *")
            self.assertEqual(changed.censored_text, "П*т*н здесь")
            self.assertEqual(reset_result, "Settings reset to defaults.")
            self.assertEqual(reset.censored_text, "П#т#н здесь")
            self.assertEqual(keywords_after_reset, ["путин"])
            self.assertEqual(stored_settings, ("Group A", "#"))


if __name__ == "__main__":
    unittest.main()