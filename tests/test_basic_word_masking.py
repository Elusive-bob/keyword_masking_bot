import unittest

from bot.core.censorer import mask_word
from tests._base import LoggedTestCase


class TestBasicWordMasking(LoggedTestCase):
    def test_masking_examples(self) -> None:
        samples = [
            "я",             # len=1  -> unchanged
            "дом",           # len=3  -> keep 1+1
            "тест",          # len=4  -> keep 1+1 (boundary)
            "путин",         # len=5  -> keep 2+2
            "машина",        # len=6  -> keep 2+2 (boundary)
            "наркотик",      # len=8  -> keep 3+3
            "амфетамин",     # len=9  -> keep 3+3
            "метамфетамин",  # len=12 -> keep 3+3
        ]
        result = {word: mask_word(word) for word in samples}

        self.set_test_log(
            module_object="bot/core/censorer.py::mask_word",
            test_arguments=f"samples={samples!r}",
            asserted_output=(
                "{'я': 'я', 'дом': 'д●м', 'тест': 'т●●т', 'путин': 'пу●ин', "
                "'машина': 'ма●●на', 'наркотик': 'нар●●тик', 'амфетамин': 'амф●●●мин', "
                "'метамфетамин': 'мет●●●●●●мин'}"
            ),
            output=repr(result),
        )

        self.assertEqual(result["я"], "я")
        self.assertEqual(result["дом"], "д●м")
        self.assertEqual(result["тест"], "т●●т")
        self.assertEqual(result["путин"], "пу●ин")
        self.assertEqual(result["машина"], "ма●●на")
        self.assertEqual(result["наркотик"], "нар●●тик")
        self.assertEqual(result["амфетамин"], "амф●●●мин")
        self.assertEqual(result["метамфетамин"], "мет●●●●●●мин")


if __name__ == "__main__":
    unittest.main()
