import unittest

from bot.core.validator import validate_mask_char, validate_word
from tests._base import LoggedTestCase


class TestValidation(LoggedTestCase):
    def test_validate_mask_char(self) -> None:
        values = {
            "#": True,
            "●": True,
            "1": True,
            " ": False,
            "": False,
            "ab": False,
            "**": False,
        }
        result = {key: validate_mask_char(key) for key in values}

        self.set_test_log(
            module_object="bot/core/validator.py::validate_mask_char",
            test_arguments=f"values={list(values)!r}",
            asserted_output=repr(values),
            output=repr(result),
        )

        self.assertEqual(result, values)

    def test_validate_word(self) -> None:
        values = {
            "путин": True,
            "word1": True,
            "123": True,
            "": False,
            "two words": False,
            "word!": False,
            "with-dash": False,
        }
        result = {key: validate_word(key) for key in values}

        self.set_test_log(
            module_object="bot/core/validator.py::validate_word",
            test_arguments=f"values={list(values)!r}",
            asserted_output=repr(values),
            output=repr(result),
        )

        self.assertEqual(result, values)


if __name__ == "__main__":
    unittest.main()
