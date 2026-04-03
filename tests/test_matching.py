import unittest

from bot.config import load_bootstrap_config
from bot.core.matcher import find_triggered_keywords
from tests._base import LoggedTestCase


class TestMatching(LoggedTestCase):
    def test_matcher_catches_default_keywords(self) -> None:
        cfg = load_bootstrap_config("config.json")
        phrases = {
            "В чате обсуждали Путина и новости": ["путин"],
            "Трафик идет через VPN сервис": ["vpn"],
            "Упоминали амфетамин в статье": ["амфетамин"],
            "Нейтральная фраза без триггеров": [],
        }

        actual = {
            phrase: find_triggered_keywords(phrase, cfg.default_keywords)
            for phrase in phrases
        }

        self.set_test_log(
            module_object="bot/core/matcher.py::find_triggered_keywords",
            test_arguments=f"phrases={list(phrases)!r}",
            asserted_output=repr(phrases),
            output=repr(actual),
        )

        self.assertEqual(actual, phrases)


if __name__ == "__main__":
    unittest.main()
