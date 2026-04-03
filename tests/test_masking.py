import unittest

from bot.core.censorer import mask_word
from tests._base import LoggedTestCase


class TestMasking(LoggedTestCase):
    def test_mask_word_examples(self) -> None:
        words = [
            "я",
            "дом",
            "тест",
            "путин",
            "машина",
            "наркотик",
            "амфетамин",
            "метамфетамин",
        ]
        expected = {
            "я": "я",
            "дом": "д●м",
            "тест": "т●ст",
            "путин": "п●т●н",
            "машина": "м●ш●на",
            "наркотик": "н●р●о●ик",
            "амфетамин": "а●ф●т●м●н",
            "метамфетамин": "м●т●м●е●а●ин",
        }
        actual = {word: mask_word(word, mask_char="●") for word in words}

        self.set_test_log(
            module_object="bot/core/censorer.py::mask_word",
            test_arguments=f"words={words!r}, mask_char='●'",
            asserted_output=repr(expected),
            output=repr(actual),
        )

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
