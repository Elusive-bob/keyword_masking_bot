import unittest

from bot.core.matcher import _build_variants, build_keyword_pattern, find_triggered_keywords


class TestMatcher(unittest.TestCase):
    def test_build_variants_adds_russian_endings_for_long_words(self) -> None:
        self._log_details = (
            "targets bot/core/matcher.py::_build_variants with keyword='путин'; "
            "expects variants including 'путин', 'путина', 'путином'"
        )
        variants = _build_variants("путин")
        self.assertIn("путин", variants)
        self.assertIn("путина", variants)
        self.assertIn("путином", variants)

    def test_build_variants_short_word_exact_only(self) -> None:
        self._log_details = (
            "targets bot/core/matcher.py::_build_variants with keyword='дом'; "
            "expects exact-only variant ['дом']"
        )
        variants = _build_variants("дом")
        self.assertEqual(variants, ["дом"])

    def test_pattern_uses_word_boundaries(self) -> None:
        self._log_details = (
            "targets bot/core/matcher.py::build_keyword_pattern with keyword='путин'; "
            "checks text='Я вижу Путина' matches and text='запутинский' does not"
        )
        pattern = build_keyword_pattern("путин")
        self.assertIsNotNone(pattern.search("Я вижу Путина"))
        self.assertIsNone(pattern.search("запутинский"))

    def test_find_triggered_keywords(self) -> None:
        self._log_details = (
            "targets bot/core/matcher.py::find_triggered_keywords with "
            "text='Это был путином и амфетамин', keywords=['путин','амфетамин','дом']; "
            "expects {'путин','амфетамин'}"
        )
        triggered = find_triggered_keywords("Это был путином и амфетамин", ["путин", "амфетамин", "дом"])
        self.assertEqual(triggered, {"путин", "амфетамин"})


if __name__ == "__main__":
    unittest.main()
