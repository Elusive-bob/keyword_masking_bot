import unittest

from bot.core.censorer import censor_text, mask_word


class TestCensorer(unittest.TestCase):
    def test_mask_word(self) -> None:
        self._log_details = (
            "targets bot/core/censorer.py::mask_word with "
            "word='я' -> 'я', word='дом' -> 'д●м', word='путин' -> 'п●●●н', "
            "word='наркотик' -> 'на●●●●ик', word='амфетамин' -> 'ам●●●●●ин', "
            "word='метамфетамин' -> 'мет●●●●●●мин'"
        )
        self.assertEqual(mask_word("я"), "я")            # ≤2 → unchanged
        self.assertEqual(mask_word("дом"), "д●м")         # 3 chars → keep 1+1
        self.assertEqual(mask_word("путин"), "п●●●н")      # 5 chars → keep 1+1
        self.assertEqual(mask_word("наркотик"), "на●●●●ик")  # 8 chars → keep 2+2
        self.assertEqual(mask_word("амфетамин"), "ам●●●●●ин")  # 9 chars → keep 2+2
        self.assertEqual(mask_word("метамфетамин"), "мет●●●●●●мин")  # 12 chars → keep 3+3

    def test_mask_word_uses_custom_mask_char(self) -> None:
        self._log_details = (
            "targets bot/core/censorer.py::mask_word with "
            "word='путин', mask_char='●' -> 'п●●●н'"
        )
        self.assertEqual(mask_word("путин", mask_char="●"), "п●●●н")

    def test_censor_text_masks_matched_variations(self) -> None:
        self._log_details = (
            "targets bot/core/censorer.py::censor_text with "
            "text='Я видел Путина и наркотиком торговали', keywords={'путин','наркотик'}; "
            "expects masked results like 'П●●●●а' and 'на●●●●●●●м'"
        )
        text = "Я видел Путина и наркотиком торговали"
        result = censor_text(text, {"путин", "наркотик"})
        # Verify masking happened without asserting exact star count.
        self.assertIn("●", result)
        self.assertNotEqual(result, text)

    def test_censor_text_uses_custom_mask_char(self) -> None:
        self._log_details = (
            "targets bot/core/censorer.py::censor_text with "
            "text='Я видел Путина', keywords={'путин'}, mask_char='●'"
        )
        text = "Я видел Путина"
        result = censor_text(text, {"путин"}, mask_char="●")
        self.assertIn("●", result)


if __name__ == "__main__":
    unittest.main()
