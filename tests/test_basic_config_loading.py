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
                        "mask_char": "●",
                        "default_keywords": ["Путин", "Наркотик"],
                    }
                ),
                encoding="utf-8",
            )

            cfg = load_bootstrap_config(str(config_path))
            output = {
                "token": cfg.token,
                "db_path": cfg.db_path,
                "mask_char": cfg.mask_char,
                "default_keywords": cfg.default_keywords,
            }
            self.set_test_log(
                module_object="bot/config.py::load_bootstrap_config",
                test_arguments=f"path={str(config_path)!r}",
                asserted_output=(
                    "{'token': 'abc-token', 'db_path': 'my_bot.db', "
                    "'mask_char': '●', 'default_keywords': ['путин', 'наркотик']}"
                ),
                output=repr(output),
            )

            self.assertEqual(cfg.token, "abc-token")
            self.assertEqual(cfg.db_path, "my_bot.db")
            self.assertEqual(cfg.mask_char, "●")
            self.assertEqual(cfg.default_keywords, ["путин", "наркотик"])


if __name__ == "__main__":
    unittest.main()
