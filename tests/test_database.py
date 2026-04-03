import tempfile
import unittest
from pathlib import Path

from bot.config import load_bootstrap_config
from bot.core.censorer import mask_word
from bot.core.service import ModerationService
from bot.storage.sqlite_store import SQLiteKeywordStore
from tests._base import LoggedTestCase


class TestDatabase(LoggedTestCase):
    def test_database_and_commands_workflow(self) -> None:
        cfg = load_bootstrap_config("config.json")

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test_bot.db"
            store = SQLiteKeywordStore(
                db_path=str(db_path),
                default_mask_char=cfg.default_mask_char,
                default_keywords=cfg.default_keywords,
            )
            service = ModerationService(store=store)

            chat_id = 101
            chat_name = "Fake Chat"

            list_result = service.build_listwords_command_result(
                chat_id=chat_id,
                command_text="/listwords",
                chat_name=chat_name,
            )

            tables = {
                row[0]
                for row in store._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            settings_row = store._connection.execute(
                "SELECT chat_name, mask_char FROM chat_settings WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
            keywords_after_init = store.list_keywords(chat_id)

            self.assertTrue(db_path.exists())
            self.assertIn("chat_settings", tables)
            self.assertIn("chat_keywords", tables)
            self.assertEqual(settings_row, (chat_name, cfg.default_mask_char))
            self.assertEqual(keywords_after_init, sorted(cfg.default_keywords))

            for word in keywords_after_init:
                self.assertIn(mask_word(word, cfg.default_mask_char), list_result)

            add_word = "test123"
            add_result = service.build_addword_command_result(
                chat_id=chat_id,
                command_text=f"/addword {add_word}",
                keyword=add_word,
                chat_name=chat_name,
            )
            moderated_after_add = service.moderate_text(
                chat_id=chat_id,
                text=f"Message with {add_word}",
                chat_name=chat_name,
            )

            self.assertIn(add_result.split(":", 1)[0], {"Added", "Already exists"})
            self.assertTrue(moderated_after_add.matched)

            remove_result = service.build_removeword_command_result(
                chat_id=chat_id,
                command_text=f"/removeword {add_word}",
                keyword=add_word,
                chat_name=chat_name,
            )
            list_after_remove = service.build_listwords_command_result(
                chat_id=chat_id,
                command_text="/listwords",
                chat_name=chat_name,
            )
            moderated_after_remove = service.moderate_text(
                chat_id=chat_id,
                text=f"Message with {add_word}",
                chat_name=chat_name,
            )

            self.assertTrue(remove_result.startswith("Removed:"))
            self.assertNotIn(mask_word(add_word, cfg.default_mask_char), list_after_remove)
            self.assertFalse(moderated_after_remove.matched)

            mask_result = service.build_mask_char_command_result(
                chat_id=chat_id,
                command_text="/mask_char #",
                new_mask_char="#",
                chat_name=chat_name,
            )
            masked_text = service.moderate_text(
                chat_id=chat_id,
                text="путин здесь",
                chat_name=chat_name,
            )

            self.assertEqual(mask_result, "Mask char updated to: #")
            self.assertTrue(masked_text.matched)
            self.assertIn("#", masked_text.censored_text)

            reset_result = service.build_reset_command_result(
                chat_id=chat_id,
                command_text="/reset",
                chat_name=chat_name,
            )
            keywords_after_reset = store.list_keywords(chat_id)
            mask_after_reset = store.get_mask_char(chat_id)

            self.assertEqual(reset_result, "Settings reset to defaults.")
            self.assertEqual(keywords_after_reset, sorted(cfg.default_keywords))
            self.assertEqual(mask_after_reset, cfg.default_mask_char)

            output = {
                "db_exists": db_path.exists(),
                "tables": sorted(tables),
                "settings_row": settings_row,
                "default_keywords_count": len(keywords_after_init),
                "add_result": add_result,
                "remove_result": remove_result,
                "mask_result": mask_result,
                "reset_result": reset_result,
                "mask_after_reset": mask_after_reset,
            }
            self.set_test_log(
                module_object="bot/storage/sqlite_store.py + bot/core/service.py",
                test_arguments=(
                    f"chat_id={chat_id}, chat_name={chat_name!r}, db_path={str(db_path)!r}, "
                    "commands=/listwords,/addword,/removeword,/mask_char,/reset"
                ),
                asserted_output=(
                    "DB created with chat_settings/chat_keywords and command workflow behaves correctly"
                ),
                output=repr(output),
            )


if __name__ == "__main__":
    unittest.main()
