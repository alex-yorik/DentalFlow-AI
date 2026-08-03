import logging

from telegram import Bot

from src.config.loader import AppConfig
from src.leads.models import Lead

logger = logging.getLogger(__name__)


async def notify_staff_followup_complete(config: AppConfig, lead: Lead, bot: Bot) -> None:
    """Notify staff that follow-up task completed."""
    staff_chat_id = config.client.business.staff_chat_id
    if not staff_chat_id:
        return

    message = f"Follow-up completed for lead {lead.id} (chat {lead.channel_user_id})"

    try:
        await bot.send_message(chat_id=staff_chat_id, text=message)
        logger.info("Follow-up completion notification sent for lead %s", lead.id)
    except Exception as e:
        logger.error("Failed to notify staff about followup completion: %s", e)


async def notify_staff(config: AppConfig, lead: Lead, bot: Bot) -> None:
    staff_chat_id = config.client.business.staff_chat_id
    if not staff_chat_id:
        logger.info("No staff_chat_id configured — skipping notification")
        return

    message = (
        f"New Lead: {lead.name or 'Unknown'}\n"
        f"Phone: {lead.phone or 'Unknown'}\n"
        f"Service: {lead.service_interest or 'Unknown'}\n"
        f"Urgency: {lead.urgency or 'Normal'}\n"
        f"Summary: {lead.conversation_summary[:200] if lead.conversation_summary else 'N/A'}"
    )

    try:
        await bot.send_message(chat_id=staff_chat_id, text=message)
        logger.info("Staff notification sent for lead %s (chat %s)", lead.id, lead.channel_user_id)
    except Exception as e:
        logger.error("Failed to send staff notification: %s", e)