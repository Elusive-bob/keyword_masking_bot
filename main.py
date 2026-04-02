import asyncio
import logging
import os
import sys
from bot.config import load_bootstrap_config
from bot.core.service import ModerationService
from bot.messengers.telegram import create_telegram_application
from bot.storage.sqlite_store import SQLiteKeywordStore


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
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

    # Python 3.14 no longer creates an implicit main-thread event loop.
    # PTB's run_polling() still expects one to exist.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    app.run_polling()


if __name__ == "__main__":
    main()
