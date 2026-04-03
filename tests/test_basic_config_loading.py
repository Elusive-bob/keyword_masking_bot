import json
import tempfile
import unittest
from pathlib import Path

from bot.config import load_bootstrap_config
from tests._base import LoggedTestCase


class TestBasicConfigLoading(LoggedTestCase):
    def test_config_loading_with_expected_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "token": "abc-token",
                        "db_path": "my_bot.db",
                        "default_mask_char": "●",
                        "default_keywords": ["Путин", "Наркотик"],
                    }
                ),
                encoding="utf-8",
            )

            cfg = load_bootstrap_config(str(config_path))
            output = {
                "token": cfg.token,
                "db_path": cfg.db_path,
                "default_mask_char": cfg.default_mask_char,
                "default_keywords": cfg.default_keywords,
            }
            self.set_test_log(
                module_object="bot/config.py::load_bootstrap_config",
                test_arguments=f"path={str(config_path)!r}",
                asserted_output=(
                    "{'token': 'abc-token', 'db_path': 'my_bot.db', "
                    "'default_mask_char': '●', 'default_keywords': ['путин', 'наркотик']}"
                ),
                output=repr(output),
            )

            self.assertEqual(cfg.token, "abc-token")
            self.assertEqual(cfg.db_path, "my_bot.db")
            self.assertEqual(cfg.default_mask_char, "●")
            self.assertEqual(cfg.default_keywords, ["путин", "наркотик"])

    def test_config_rejects_multi_symbol_mask_char(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "token": "abc-token",
                        "db_path": "my_bot.db",
                        "default_mask_char": "**",
                        "default_keywords": ["Путин"],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "default_mask_char"):
                load_bootstrap_config(str(config_path))

    def test_config_rejects_missing_db_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "token": "abc-token",
                        "default_mask_char": "#",
                        "default_keywords": ["Путин"],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "db_path"):
                load_bootstrap_config(str(config_path))

    def test_config_rejects_empty_default_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "token": "abc-token",
                        "db_path": "my_bot.db",
                        "default_mask_char": "#",
                        "default_keywords": ["   ", ""],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "default_keywords"):
                load_bootstrap_config(str(config_path))


if __name__ == "__main__":
    unittest.main()
