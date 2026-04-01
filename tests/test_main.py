import unittest
from unittest.mock import Mock, patch

import main


class TestMain(unittest.TestCase):
    @patch("main.create_telegram_application")
    @patch("main.ModerationService")
    @patch("main.SQLiteKeywordStore")
    @patch("main.load_bootstrap_config")
    def test_main_wires_dependencies(
        self,
        mock_load_config: Mock,
        mock_store_cls: Mock,
        mock_service_cls: Mock,
        mock_create_app: Mock,
    ) -> None:
        self._log_details = (
            "targets main.py::main with config token='test-token', db_path='test.db', "
            "default_keywords=['путин'], mask_char='●'; expects SQLiteKeywordStore, "
            "ModerationService, and create_telegram_application wiring"
        )
        cfg = Mock(token="test-token", db_path="test.db", default_keywords=["путин"], mask_char="●")
        mock_load_config.return_value = cfg

        fake_store = Mock()
        fake_service = Mock()
        fake_app = Mock()
        mock_store_cls.return_value = fake_store
        mock_service_cls.return_value = fake_service
        mock_create_app.return_value = fake_app

        main.main()

        mock_load_config.assert_called_once()
        mock_store_cls.assert_called_once_with("test.db")
        mock_service_cls.assert_called_once_with(store=fake_store, default_keywords=["путин"], mask_char="●")
        mock_create_app.assert_called_once_with(token="test-token", service=fake_service)
        fake_app.run_polling.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
