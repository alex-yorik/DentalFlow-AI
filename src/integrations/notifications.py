import logging

from src.config.loader import AppConfig
from src.leads.models import Lead

logger = logging.getLogger(__name__)


async def notify_staff(config: AppConfig, lead: Lead) -> None:
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

    logger.info(
        "Staff notification for lead %s (chat %s):\n%s",
        lead.id, lead.telegram_chat_id, message,
    )