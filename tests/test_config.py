import unittest

from bot.config import load_bootstrap_config
from tests._base import LoggedTestCase


class TestConfig(LoggedTestCase):
    def test_config_has_required_non_empty_fields(self) -> None:
        cfg = load_bootstrap_config("config.json")

        checks = {
            "token": bool(cfg.token),
            "default_mask_char": bool(cfg.default_mask_char),
            "default_keywords": bool(cfg.default_keywords),
            "db_path": bool(cfg.db_path),
        }
        output = {
            "token": cfg.token,
            "default_mask_char": cfg.default_mask_char,
            "default_keywords_count": len(cfg.default_keywords),
            "db_path": cfg.db_path,
            "checks": checks,
        }

        self.set_test_log(
            module_object="bot/config.py::load_bootstrap_config",
            test_arguments="path='config.json'",
            asserted_output="All required fields are present and non-empty",
            output=repr(output),
        )

        self.assertTrue(all(checks.values()))


if __name__ == "__main__":
    unittest.main()
