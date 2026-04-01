import logging
import os
from bot.config import load_bootstrap_config
from bot.core.service import ModerationService
from bot.messengers.telegram import create_telegram_application
from bot.storage.sqlite_store import SQLiteKeywordStore


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize dependencies from config and run Telegram polling loop."""

    config_path = os.getenv("CENSOR_CONFIG_PATH", "config.json")
    cfg = load_bootstrap_config(config_path)

    store = SQLiteKeywordStore(cfg.db_path)
    service = ModerationService(
        store=store,
        default_keywords=cfg.default_keywords,
        mask_char=cfg.mask_char,
    )

    app = create_telegram_application(token=cfg.token, service=service)

    logger.info("Bot started. Monitoring group chats for configured keywords.")
    app.run_polling()


if __name__ == "__main__":
    main()
