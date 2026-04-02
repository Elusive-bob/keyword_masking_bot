import unittest

from bot.core.censorer import mask_word
from tests._base import LoggedTestCase


class TestBasicWordMasking(LoggedTestCase):
    def test_masking_examples(self) -> None:
        samples = [
            "я",             # len=1  -> unchanged
            "дом",           # len=3  -> д●м
            "тест",          # len=4  -> т●ст
            "путин",         # len=5  -> п●т●н
            "машина",        # len=6  -> м●ш●на
            "наркотик",      # len=8  -> н●р●о●ик
            "амфетамин",     # len=9  -> а●ф●т●м●н
            "метамфетамин",  # len=12 -> м●т●м●е●а●ин
        ]
        result = {word: mask_word(word) for word in samples}

        self.set_test_log(
            module_object="bot/core/censorer.py::mask_word",
            test_arguments=f"samples={samples!r}",
            asserted_output=(
                "{'я': 'я', 'дом': 'д●м', 'тест': 'т●ст', 'путин': 'п●т●н', "
                "'машина': 'м●ш●на', 'наркотик': 'н●р●о●ик', 'амфетамин': 'а●ф●т●м●н', "
                "'метамфетамин': 'м●т●м●е●а●ин'}"
            ),
            output=repr(result),
        )

        self.assertEqual(result["я"], "я")
        self.assertEqual(result["дом"], "д●м")
        self.assertEqual(result["тест"], "т●ст")
        self.assertEqual(result["путин"], "п●т●н")
        self.assertEqual(result["машина"], "м●ш●на")
        self.assertEqual(result["наркотик"], "н●р●о●ик")
        self.assertEqual(result["амфетамин"], "а●ф●т●м●н")
        self.assertEqual(result["метамфетамин"], "м●т●м●е●а●ин")


if __name__ == "__main__":
    unittest.main()
