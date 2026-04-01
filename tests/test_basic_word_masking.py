import unittest

from bot.core.censorer import mask_word
from tests._base import LoggedTestCase


class TestBasicWordMasking(LoggedTestCase):
    def test_masking_examples(self) -> None:
        samples = ["я", "дом", "путин", "наркотик", "амфетамин", "метамфетамин"]
        result = {word: mask_word(word) for word in samples}

        self.set_test_log(
            module_object="bot/core/censorer.py::mask_word",
            test_arguments=f"samples={samples!r}",
            asserted_output=(
                "{'я': 'я', 'дом': 'д●м', 'путин': 'п●●●н', "
                "'наркотик': 'на●●●●ик', 'амфетамин': 'ам●●●●●ин', "
                "'метамфетамин': 'мет●●●●●●мин'}"
            ),
            output=repr(result),
        )

        self.assertEqual(result["я"], "я")
        self.assertEqual(result["дом"], "д●м")
        self.assertEqual(result["путин"], "п●●●н")
        self.assertEqual(result["наркотик"], "на●●●●ик")
        self.assertEqual(result["амфетамин"], "ам●●●●●ин")
        self.assertEqual(result["метамфетамин"], "мет●●●●●●мин")


if __name__ == "__main__":
    unittest.main()
