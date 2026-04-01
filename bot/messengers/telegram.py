import logging
from typing import Optional

from telegram import Message, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.core.service import ModerationService


logger = logging.getLogger(__name__)


def create_telegram_application(token: str, service: ModerationService) -> Application:
    """Build and configure Telegram application with command and moderation handlers."""

    app = Application.builder().token(token).build()
    app.bot_data["service"] = service

    app.add_handler(CommandHandler("addword", add_word_command))
    app.add_handler(CommandHandler("removeword", remove_word_command))
    app.add_handler(CommandHandler("listwords", list_words_command))
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, moderate_message)
    )
    return app


def _service(context: ContextTypes.DEFAULT_TYPE) -> ModerationService:
    """Read moderation service from app-scoped bot_data."""

    return context.application.bot_data["service"]


def _is_group_message(update: Update) -> bool:
    """Return True when the update comes from group or supergroup chat."""

    chat = update.effective_chat
    return chat is not None and chat.type in {"group", "supergroup"}


def _author_name(message: Message) -> str:
    """Build a display name for the original message author."""

    user = message.from_user
    if user is None:
        return "Unknown"
    return user.full_name or user.username or str(user.id)


def _reply_to_id(message: Message) -> Optional[int]:
    """Return message id of replied-to message when present."""

    if message.reply_to_message is None:
        return None
    return message.reply_to_message.message_id


def _command_text_args(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Normalize command arguments into one lowercase string."""

    args = context.args or []
    return " ".join(args).strip().lower()


def _build_prefixed_text(author: str, text: str, limit: int) -> str:
    """Prefix text with author and truncate to Telegram length limits."""

    combined = f"{author}: {text}"
    if len(combined) <= limit:
        return combined
    if limit <= 3:
        return combined[:limit]
    return f"{combined[: limit - 3]}..."


async def add_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addword by deleting command message and updating chat keywords."""

    message = update.effective_message
    if not _is_group_message(update) or update.effective_chat is None or message is None:
        return

    chat_id = update.effective_chat.id
    author = _author_name(message)
    command_text = message.text or "/addword"
    keyword = _command_text_args(context)
    await message.delete()
    result_text = _service(context).build_addword_command_result(
        chat_id=chat_id,
        author=author,
        command_text=command_text,
        keyword=keyword,
    )
    await context.bot.send_message(chat_id, result_text)


async def remove_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /removeword by deleting command message and updating chat keywords."""

    message = update.effective_message
    if not _is_group_message(update) or update.effective_chat is None or message is None:
        return

    chat_id = update.effective_chat.id
    author = _author_name(message)
    command_text = message.text or "/removeword"
    keyword = _command_text_args(context)
    await message.delete()
    result_text = _service(context).build_removeword_command_result(
        chat_id=chat_id,
        author=author,
        command_text=command_text,
        keyword=keyword,
    )
    await context.bot.send_message(chat_id, result_text)


async def list_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /listwords by posting masked keyword list for the chat."""

    message = update.effective_message
    if not _is_group_message(update) or update.effective_chat is None or message is None:
        return

    chat_id = update.effective_chat.id
    author = _author_name(message)
    command_text = message.text or "/listwords"
    await message.delete()
    reply_text = _service(context).build_listwords_command_result(
        chat_id=chat_id,
        author=author,
        command_text=command_text,
    )
    await context.bot.send_message(chat_id, reply_text)


async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Moderate text/caption messages by reposting censored content then deleting source."""

    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return

    # Ignore bots to avoid feedback loops.
    if message.from_user is not None and message.from_user.is_bot:
        return

    text_or_caption = message.text or message.caption
    if not text_or_caption:
        return

    result = _service(context).moderate_text(chat_id=chat.id, text=text_or_caption)
    if not result.matched:
        return

    author = _author_name(message)
    reply_to_message_id = _reply_to_id(message)
    caught_text = _build_prefixed_text(author, text_or_caption, limit=120)

    try:
        if message.text is not None:
            reply_text = _build_prefixed_text(author, result.censored_text, limit=4096)
            await context.bot.send_message(
                chat_id=chat.id,
                text=reply_text,
                reply_to_message_id=reply_to_message_id,
            )
        else:
            reply_text = _build_prefixed_text(author, result.censored_text, limit=1024)
            await context.bot.copy_message(
                chat_id=chat.id,
                from_chat_id=chat.id,
                message_id=message.message_id,
                caption=reply_text,
                reply_to_message_id=reply_to_message_id,
            )
        _service(context).log_caught_message(
            chat_id=chat.id,
            author=author,
            caught_text=caught_text,
            corrected_text=_build_prefixed_text(author, result.censored_text, limit=120),
        )
    except Exception as exc:
        logger.exception(
            "error reposting moderated message: chat_id=%s message_id=%s error=%s",
            chat.id,
            message.message_id,
            exc,
        )
        return

    try:
        await message.delete()
    except Exception as exc:
        logger.exception(
            "error deleting original message: chat_id=%s message_id=%s error=%s",
            chat.id,
            message.message_id,
            exc,
        )
