import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bot.messengers import telegram


class TestTelegramHelpers(unittest.TestCase):
    def test_is_group_message(self) -> None:
        self._log_details = (
            "targets bot/messengers/telegram.py::_is_group_message with chat.type in "
            "['group','supergroup','private']"
        )
        self.assertTrue(telegram._is_group_message(SimpleNamespace(effective_chat=SimpleNamespace(type="group"))))
        self.assertTrue(telegram._is_group_message(SimpleNamespace(effective_chat=SimpleNamespace(type="supergroup"))))
        self.assertFalse(telegram._is_group_message(SimpleNamespace(effective_chat=SimpleNamespace(type="private"))))

    def test_build_prefixed_text_truncates(self) -> None:
        self._log_details = (
            "targets bot/messengers/telegram.py::_build_prefixed_text with "
            "author='author', text='abcdef', limit=10; expects 'author:...'"
        )
        value = telegram._build_prefixed_text("author", "abcdef", limit=10)
        self.assertEqual(value, "author:...")

    def test_command_text_args(self) -> None:
        self._log_details = (
            "targets bot/messengers/telegram.py::_command_text_args with args=['  ПуТин','!!!  ']; "
            "expects 'путин !!!'"
        )
        context = SimpleNamespace(args=["  ПуТин", "!!!  "])
        self.assertEqual(telegram._command_text_args(context), "путин !!!")


class TestTelegramAdapterAsync(unittest.IsolatedAsyncioTestCase):
    async def test_moderate_message_text_success_flow(self) -> None:
        self._log_details = (
            "targets bot/messengers/telegram.py::moderate_message with text='путин', "
            "reply_to_message_id=42, matched=True, censored_text='п***н'; expects send_message + delete"
        )
        service = Mock()
        service.moderate_text.return_value = SimpleNamespace(matched=True, censored_text="п***н", triggered_keywords={"путин"})

        bot = SimpleNamespace(send_message=AsyncMock(), copy_message=AsyncMock())
        message = SimpleNamespace(
            text="путин",
            caption=None,
            from_user=SimpleNamespace(is_bot=False, full_name="User", username=None, id=1),
            reply_to_message=SimpleNamespace(message_id=42),
            message_id=100,
            delete=AsyncMock(),
        )
        update = SimpleNamespace(effective_message=message, effective_chat=SimpleNamespace(id=7, type="group"))
        context = SimpleNamespace(bot=bot, application=SimpleNamespace(bot_data={"service": service}))

        await telegram.moderate_message(update, context)

        bot.send_message.assert_awaited_once()
        message.delete.assert_awaited_once()

    async def test_moderate_message_media_uses_copy(self) -> None:
        self._log_details = (
            "targets bot/messengers/telegram.py::moderate_message with caption='путин', "
            "message_id=100, matched=True, censored_text='п***н'; expects copy_message + delete"
        )
        service = Mock()
        service.moderate_text.return_value = SimpleNamespace(matched=True, censored_text="п***н", triggered_keywords={"путин"})

        bot = SimpleNamespace(send_message=AsyncMock(), copy_message=AsyncMock())
        message = SimpleNamespace(
            text=None,
            caption="путин",
            from_user=SimpleNamespace(is_bot=False, full_name="User", username=None, id=1),
            reply_to_message=None,
            message_id=100,
            delete=AsyncMock(),
        )
        update = SimpleNamespace(effective_message=message, effective_chat=SimpleNamespace(id=7, type="group"))
        context = SimpleNamespace(bot=bot, application=SimpleNamespace(bot_data={"service": service}))

        await telegram.moderate_message(update, context)

        bot.copy_message.assert_awaited_once()
        message.delete.assert_awaited_once()


class TestCreateApplication(unittest.TestCase):
    def test_create_telegram_application_wires_service(self) -> None:
        self._log_details = (
            "targets bot/messengers/telegram.py::create_telegram_application with "
            "token='token' and mocked Application.builder(); expects handlers registration and bot_data['service']"
        )
        fake_builder = Mock()
        fake_app = Mock()
        fake_builder.token.return_value = fake_builder
        fake_builder.build.return_value = fake_app
        fake_app.bot_data = {}

        with patch("bot.messengers.telegram.Application.builder", return_value=fake_builder):
            app = telegram.create_telegram_application("token", Mock())

        self.assertIs(app, fake_app)
        self.assertIn("service", fake_app.bot_data)


if __name__ == "__main__":
    unittest.main()
