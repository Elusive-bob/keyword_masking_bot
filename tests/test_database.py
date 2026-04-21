import tempfile
import unittest
from pathlib import Path

from bot.config import load_bootstrap_config
from bot.core.censorer import mask_word
from bot.core.service import ModerationService
from bot.storage.sqlite_store import SQLiteKeywordStore
from tests._base import LoggedTestCase


class TestDatabase(LoggedTestCase):
    def test_database_and_keyword_stats_workflow(self) -> None:
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

            # Initialize chat with defaults
            list_result = service.build_listwords_command_result(
                chat_id=chat_id,
                command_text="/listwords",
                chat_name=chat_name,
            )

            # Verify DB structure
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
            self.assertIn("events", tables)
            self.assertEqual(settings_row, (chat_name, cfg.default_mask_char))
            self.assertEqual(keywords_after_init, sorted(cfg.default_keywords))

            # Test basic moderation increments counters
            moderation_result = service.moderate_text(
                chat_id=chat_id,
                text="путин и война",
                chat_name=chat_name,
            )

            # Log the moderation event to increment match_count
            service.log_caught_message(
                chat_id=chat_id,
                user_id=123,
                user_name="Test User",
                original_text="путин и война",
                censored_text="****** и ****",
                triggered_keywords=moderation_result.triggered_keywords,
            )

            # Same keyword can match multiple times in one message.
            repeat_result = service.moderate_text(
                chat_id=chat_id,
                text="путин путин",
                chat_name=chat_name,
            )

            # Log the second moderation event
            service.log_caught_message(
                chat_id=chat_id,
                user_id=123,
                user_name="Test User",
                original_text="путин путин",
                censored_text="****** ******",
                triggered_keywords=repeat_result.triggered_keywords,
            )

            self.assertTrue(moderation_result.matched)
            self.assertIn("путин", moderation_result.triggered_keywords)
            self.assertIn("война", moderation_result.triggered_keywords)
            self.assertTrue(repeat_result.matched)
            self.assertIn("путин", repeat_result.triggered_keywords)

            # Verify stats were incremented
            stats = store.get_keyword_stats(chat_id, limit=10)
            stats_dict = {word: count for word, count in stats}
            self.assertEqual(stats_dict.get("путин"), 3)
            self.assertEqual(stats_dict.get("война"), 1)

            # Test /stats command shows updated counts
            stats_result = service.build_stats_command_result(
                chat_id=chat_id,
                command_text="/stats",
                chat_name=chat_name,
            )
            masked_put = mask_word("путин", cfg.default_mask_char)
            masked_war = mask_word("война", cfg.default_mask_char)
            self.assertIn(masked_put, stats_result)
            self.assertIn(masked_war, stats_result)
            self.assertIn(" - 1", stats_result)

            # Test /addword with new keyword
            add_result = service.build_addword_command_result(
                chat_id=chat_id,
                command_text="/addword test123",
                keyword="test123",
                chat_name=chat_name,
            )

            self.assertIn("Added:", add_result)
            self.assertIn("test123", store.list_keywords(chat_id))

            # Keyword starts with 0 count
            stats = store.get_keyword_stats(chat_id, limit=10)
            stats_dict = {word: count for word, count in stats}
            self.assertEqual(stats_dict.get("test123"), 0)

            # Moderate text with new keyword to increment its counter
            mod_result = service.moderate_text(
                chat_id=chat_id,
                text="test123 here",
                chat_name=chat_name,
            )

            service.log_caught_message(
                chat_id=chat_id,
                user_id=456,
                user_name="Another User",
                original_text="test123 here",
                censored_text="******* here",
                triggered_keywords=mod_result.triggered_keywords,
            )

            self.assertTrue(mod_result.matched)
            self.assertIn("test123", mod_result.triggered_keywords)

            # Verify counter increased
            stats = store.get_keyword_stats(chat_id, limit=10)
            stats_dict = {word: count for word, count in stats}
            self.assertEqual(stats_dict.get("test123"), 1)

            # Test /removeword sets active=false but preserves stats
            remove_result = service.build_removeword_command_result(
                chat_id=chat_id,
                command_text="/removeword test123",
                keyword="test123",
                chat_name=chat_name,
            )

            self.assertTrue(remove_result.startswith("Removed:"))
            self.assertNotIn("test123", store.list_keywords(chat_id))

            # Stats still exist in DB even though inactive
            all_stats = store._connection.execute(
                "SELECT keyword, match_count FROM chat_keywords WHERE chat_id = ? AND keyword = ?",
                (chat_id, "test123"),
            ).fetchone()
            self.assertIsNotNone(all_stats)
            self.assertEqual(all_stats[1], 1)

            # Test /addword reactivates removed keyword without resetting stats
            re_add_result = service.build_addword_command_result(
                chat_id=chat_id,
                command_text="/addword test123",
                keyword="test123",
                chat_name=chat_name,
            )

            self.assertIn("Already exists:", re_add_result)
            self.assertIn("test123", store.list_keywords(chat_id))

            # Stats are preserved
            stats = store.get_keyword_stats(chat_id, limit=10)
            stats_dict = {word: count for word, count in stats}
            self.assertEqual(stats_dict.get("test123"), 1)

            # Test /reset deactivates non-defaults but reactivates defaults
            reset_result = service.build_reset_command_result(
                chat_id=chat_id,
                command_text="/reset",
                chat_name=chat_name,
            )

            self.assertEqual(reset_result, "Settings reset to defaults.")
            self.assertNotIn("test123", store.list_keywords(chat_id))
            self.assertEqual(store.list_keywords(chat_id), sorted(cfg.default_keywords))

            # Default keywords still have their stats (not reset)
            stats = store.get_keyword_stats(chat_id, limit=10)
            stats_dict = {word: count for word, count in stats}
            self.assertEqual(stats_dict.get("путин"), 3)
            self.assertEqual(stats_dict.get("война"), 1)

            # Test mask_char change
            mask_result = service.build_mask_char_command_result(
                chat_id=chat_id,
                command_text="/mask_char #",
                new_mask_char="#",
                chat_name=chat_name,
            )

            self.assertEqual(mask_result, "Mask char updated to: #")

            output = {
                "db_exists": db_path.exists(),
                "tables": sorted(tables),
                "settings_row": settings_row,
                "default_keywords_count": len(keywords_after_init),
                "first_moderation_matched": moderation_result.matched,
                "stats_after_moderation": {"путин": 3, "война": 1},
                "stats_after_re_add": {"test123": 1},
                "stats_after_reset": {"путин": 3, "война": 1},
                "keywords_after_reset": store.list_keywords(chat_id) == sorted(cfg.default_keywords),
                "mask_after_change": store.get_mask_char(chat_id),
            }
            self.set_test_log(
                module_object="bot/storage/sqlite_store.py + bot/core/service.py",
                test_arguments=(
                    f"chat_id={chat_id}, chat_name={chat_name!r}, "
                    "commands with stats: /listwords,/addword,/removeword,/reset,/mask_char,/stats, "
                    "moderation_events=4"
                ),
                asserted_output=(
                    "DB with soft deletes, stats persistence on remove/reset, "
                    "counter increments on moderation, /stats shows top 10 keywords"
                ),
                output=repr(output),
            )


if __name__ == "__main__":
    unittest.main()
