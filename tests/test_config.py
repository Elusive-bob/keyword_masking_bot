import json
import tempfile
import unittest
from pathlib import Path

from bot.config import load_bootstrap_config


class TestConfig(unittest.TestCase):
    def test_load_bootstrap_config_normalizes_keywords(self) -> None:
        self._log_details = (
            "targets bot/config.py::load_bootstrap_config with "
            "config token=' test-token ', db_path=' custom.db ', mask_char='●', "
            "keywords=[' Путин ','путин','',3,'Наркотик']"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "token": " test-token ",
                        "keywords": [" Путин ", "путин", "", 3, "Наркотик"],
                        "db_path": " custom.db ",
                        "mask_char": "●",
                    }
                ),
                encoding="utf-8",
            )

            cfg = load_bootstrap_config(str(path))

            self.assertEqual(cfg.token, "test-token")
            self.assertEqual(cfg.db_path, "custom.db")
            self.assertEqual(cfg.mask_char, "●")
            self.assertEqual(cfg.default_keywords, ["путин", "наркотик"])

    def test_load_bootstrap_config_uses_default_db_path(self) -> None:
        self._log_details = (
            "targets bot/config.py::load_bootstrap_config with "
            "config token='abc', keywords=[] and omitted db_path/mask_char defaults"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "config.json"
            path.write_text(json.dumps({"token": "abc", "keywords": []}), encoding="utf-8")

            cfg = load_bootstrap_config(str(path))

            self.assertEqual(cfg.db_path, "bot.db")
            self.assertEqual(cfg.mask_char, "●")

    def test_load_bootstrap_config_requires_token(self) -> None:
        self._log_details = (
            "targets bot/config.py::load_bootstrap_config with config missing token; "
            "expects ValueError"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "config.json"
            path.write_text(json.dumps({"keywords": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_bootstrap_config(str(path))


if __name__ == "__main__":
    unittest.main()
