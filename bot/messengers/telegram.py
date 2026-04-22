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
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("mask_char", set_mask_char_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, moderate_message)
    )
    return app


def _group_command_context(update: Update) -> Optional[tuple[Message, int, Optional[str]]]:
    """Return group command data when the update can be handled."""

    message = update.effective_message
    chat = update.effective_chat
    if chat is None or message is None or chat.type not in {"group", "supergroup"}:
        return None
    return message, chat.id, _chat_name(update)


def _author_name(message: Message) -> str:
    """Build a display name for the original message author."""

    user = message.from_user
    if user is None:
        return "Unknown"
    return user.full_name or user.username or str(user.id)


def _chat_name(update: Update) -> Optional[str]:
    """Build a readable name for the current chat when one is available."""

    chat = update.effective_chat
    if chat is None:
        return None
    return chat.title or chat.full_name or chat.username


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

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/addword"
    service: ModerationService = context.application.bot_data["service"]
    keyword = " ".join(context.args or []).strip().lower()
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    result_text = service.build_addword_command_result(
        chat_id=chat_id,
        command_text=command_text,
        keyword=keyword,
        chat_name=chat_name,
    )
    await context.bot.send_message(chat_id, result_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=result_text,
    )


async def remove_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /removeword by deleting command message and updating chat keywords."""

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/removeword"
    service: ModerationService = context.application.bot_data["service"]
    keyword = " ".join(context.args or []).strip().lower()
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    result_text = service.build_removeword_command_result(
        chat_id=chat_id,
        command_text=command_text,
        keyword=keyword,
        chat_name=chat_name,
    )
    await context.bot.send_message(chat_id, result_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=result_text,
    )


async def list_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /listwords by posting masked keyword list for the chat."""

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/listwords"
    service: ModerationService = context.application.bot_data["service"]
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    reply_text = service.build_listwords_command_result(
        chat_id=chat_id,
        command_text=command_text,
        chat_name=chat_name,
    )
    await context.bot.send_message(chat_id, reply_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=reply_text,
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats by posting top moderated keywords for the chat."""

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/stats"
    service: ModerationService = context.application.bot_data["service"]
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    reply_text = service.build_stats_command_result(
        chat_id=chat_id,
        command_text=command_text,
        chat_name=chat_name,
    )
    await context.bot.send_message(chat_id, reply_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=reply_text,
    )


async def set_mask_char_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mask_char by validating and saving one per-chat mask char."""

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/mask_char"
    service: ModerationService = context.application.bot_data["service"]
    new_mask_char = " ".join(context.args or []).strip()
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    result_text = service.build_mask_char_command_result(
        chat_id=chat_id,
        command_text=command_text,
        new_mask_char=new_mask_char,
        chat_name=chat_name,
    )
    await context.bot.send_message(chat_id, result_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=result_text,
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset by restoring chat settings from config defaults."""

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/reset"
    service: ModerationService = context.application.bot_data["service"]
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    result_text = service.build_reset_command_result(
        chat_id=chat_id,
        command_text=command_text,
        chat_name=chat_name,
    )
    await context.bot.send_message(chat_id, result_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=result_text,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help by posting the list of available commands."""

    command_context = _group_command_context(update)
    if command_context is None:
        return

    message, chat_id, chat_name = command_context
    command_text = message.text or "/help"
    service: ModerationService = context.application.bot_data["service"]
    user_id = message.from_user.id if message.from_user else 0
    user_name = _author_name(message)
    await message.delete()
    result_text = service.build_help_command_result()
    await context.bot.send_message(chat_id, result_text)
    service.log_command(
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        original_text=command_text,
        bot_response=result_text,
    )


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

    service: ModerationService = context.application.bot_data["service"]
    result = service.moderate_text(
        chat_id=chat.id,
        text=text_or_caption,
        chat_name=_chat_name(update),
    )
    if not result.matched:
        return

    author = _author_name(message)
    user_id = message.from_user.id if message.from_user else 0
    reply_to_message_id = (
        message.reply_to_message.message_id if message.reply_to_message is not None else None
    )

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
        service.log_caught_message(
            chat_id=chat.id,
            user_id=user_id,
            user_name=author,
            original_text=text_or_caption,
            censored_text=_build_prefixed_text(author, result.censored_text, limit=120),
            triggered_keywords=result.triggered_keywords,
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
