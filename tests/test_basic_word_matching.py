import unittest

from bot.core.matcher import find_triggered_keywords
from tests._base import LoggedTestCase


class TestBasicWordMatching(LoggedTestCase):
    def test_word_matching_in_message(self) -> None:
        keywords = ["путин", "наркотик", "амфетамин", "дом"]
        phrases = [
            "В чате обсуждали Путина и новости дня",
            "Полиция сообщила о наркотиком торговле в районе",
            "Сегодня нашли амфетамин в лаборатории",
            "Дом стоит на углу улицы",
            "Нейтральная фраза без триггеров",
        ]
        results = {phrase: find_triggered_keywords(phrase, keywords) for phrase in phrases}

        self.set_test_log(
            module_object="bot/core/matcher.py::find_triggered_keywords",
            test_arguments=f"phrases={phrases!r}, keywords={keywords!r}",
            asserted_output=(
                "{phrase1:{'путин'}, phrase2:{'наркотик'}, phrase3:{'амфетамин'}, "
                "phrase4:{'дом'}, phrase5:set()}"
            ),
            output=repr(results),
        )

        self.assertEqual(results[phrases[0]], {"путин"})
        self.assertEqual(results[phrases[1]], {"наркотик"})
        self.assertEqual(results[phrases[2]], {"амфетамин"})
        self.assertEqual(results[phrases[3]], {"дом"})
        self.assertEqual(results[phrases[4]], set())


if __name__ == "__main__":
    unittest.main()
