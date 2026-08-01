import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from src.config.loader import AppConfig
from src.llm.client import LLMClient
from src.leads.models import Lead, LeadState
from src.leads.repository import create_lead, get_lead_by_chat_id
from src.core.message_processor import process_message, sanitize_input
from src.channels.base import IncomingMessage, OutgoingAdapter
from src.followup import FollowUpEngine
from src.storage import database
from src.integrations.crm import get_provider  # re-export for test patches

logger = logging.getLogger(__name__)

_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60.0


class TelegramOutgoingAdapter:
    def __init__(self, update: Update) -> None:
        self._update = update

    async def send_message(self, channel_user_id: str, text: str) -> None:
        await self._update.message.reply_text(text)


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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    text = config.client.business.messages.get("welcome", "Hello!")
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    llm_client: LLMClient = context.bot_data["llm_client"]
    chat_id = update.effective_chat.id

    try:
        user_text = sanitize_input(update.message.text)
        if user_text is None:
            await update.message.reply_text(
                config.client.business.messages.get("error_generic", "")
            )
            return

        if not _check_rate_limit(chat_id):
            logger.warning("Rate limit hit for chat %s", chat_id)
            await update.message.reply_text(_RATE_LIMIT_REPLY)
            return

        lead = await get_lead_by_chat_id(chat_id)

        if lead and lead.state == LeadState.BLOCKED:
            await update.message.reply_text(
                config.client.business.messages.get("error_unsafe", "")
            )
            return

        if lead and lead.state == LeadState.FOLLOWUP_PENDING:
            followup_engine = context.bot_data.get("followup_engine")
            if followup_engine:
                await followup_engine.cancel_followup(lead.id)
            now = datetime.now(timezone.utc)
            conn = await database.get_connection()
            await conn.execute(
                "UPDATE leads SET followup_task_id = NULL, updated_at = ? WHERE id = ?",
                (now.isoformat(), lead.id),
            )
            await conn.commit()
            await conn.close()
            lead = await get_lead_by_chat_id(chat_id)

        if lead and lead.state == LeadState.CLOSED:
            lead = None

        if lead is None:
            lead = await create_lead(chat_id)

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
        try:
            await update.message.reply_text(
                config.client.business.messages.get("error_generic", "")
            )
        except Exception:
            pass