import contextlib
import logging
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import cast

from telegram import Update
from telegram.ext import ContextTypes

from src.channels.base import IncomingMessage
from src.config.loader import AppConfig
from src.core.lead_lookup import resolve_lead
from src.core.message_processor import process_message, sanitize_input
from src.leads.models import Lead, LeadState
from src.leads.repository import get_lead_by_chat_id
from src.llm.client import LLMClient
from src.storage import database

logger = logging.getLogger(__name__)

_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60.0


class TelegramOutgoingAdapter:
    def __init__(self, update: Update) -> None:
        message = update.message
        assert message is not None
        self._message = message

    async def send_message(self, channel_user_id: str, text: str) -> None:
        await self._message.reply_text(text)


_rate_limit: dict[int, deque] = defaultdict(deque)


def _check_rate_limit(chat_id: int) -> bool:
    now = time.monotonic()
    had_history = chat_id in _rate_limit
    timestamps = _rate_limit[chat_id]
    while timestamps and timestamps[0] < now - _RATE_LIMIT_WINDOW:
        timestamps.popleft()
    if had_history and not timestamps:
        del _rate_limit[chat_id]
    if len(timestamps) >= _RATE_LIMIT_MAX:
        return False
    timestamps.append(now)
    return True


_RATE_LIMIT_REPLY = "Please slow down. You are sending messages too quickly."


def _extract_text_after_start(text: str | None) -> str | None:
    if not text:
        return None
    first_line, sep, rest = text.lstrip().partition("\n")
    if not first_line.startswith("/start"):
        return None
    parts = first_line.split(" ", 1)
    trailing = parts[1] + (sep + rest if sep else "") if len(parts) > 1 else rest
    trailing = trailing.strip()
    return trailing or None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    text = config.client.business.messages.get("welcome", "Hello!")
    message = update.message
    if message is None:
        return
    await message.reply_text(text)

    trailing = _extract_text_after_start(message.text)
    if trailing is not None:
        await handle_message(update, context, text=trailing)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str | None = None,
) -> None:
    config: AppConfig = context.bot_data["config"]
    llm_client: LLMClient = context.bot_data["llm_client"]
    message = update.message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    chat_id = chat.id

    try:
        user_text = sanitize_input(text if text is not None else message.text)
        if user_text is None:
            await message.reply_text(
                config.client.business.messages.get("error_generic", "")
            )
            return

        if not _check_rate_limit(chat_id):
            logger.warning("Rate limit hit for chat %s", chat_id)
            await message.reply_text(_RATE_LIMIT_REPLY)
            return

        lead = await get_lead_by_chat_id(chat_id)

        if lead and lead.state == LeadState.FOLLOWUP_PENDING:
            followup_engine = context.bot_data.get("followup_engine")
            if followup_engine:
                await followup_engine.cancel_followup(lead.id)
            now = datetime.now(UTC)
            conn = await database.get_connection()
            await conn.execute(
                "UPDATE leads SET followup_task_id = NULL, updated_at = ? WHERE id = ?",
                (now.isoformat(), lead.id),
            )
            await conn.commit()
            await conn.close()

        lead, blocked_reply = await resolve_lead(
            chat_id,
            source="telegram",
            channel_type="telegram",
            blocked_reply=config.client.business.messages.get("error_unsafe", ""),
        )
        if blocked_reply:
            await message.reply_text(blocked_reply)
            return

        lead = cast(Lead, lead)

        msg = IncomingMessage(channel_user_id=str(chat_id), text=user_text)
        outgoing = TelegramOutgoingAdapter(update)
        followup_engine = context.bot_data.get("followup_engine")

        await process_message(
            msg=msg,
            outgoing=outgoing,
            lead=lead,
            config=config,
            llm_client=llm_client,
            followup_engine=followup_engine,
            bot_for_notifications=context.bot,
        )
    except Exception as e:
        logger.error("Unhandled error in handle_message for chat %s: %s", chat_id, e, exc_info=True)
        with contextlib.suppress(Exception):
            await message.reply_text(
                config.client.business.messages.get("error_generic", "")
            )
