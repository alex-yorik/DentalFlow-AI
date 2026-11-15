import logging
from datetime import UTC, datetime, timedelta

from src.leads.models import Lead, LeadState
from src.leads.repository import create_lead, get_lead_by_chat_id, update_lead

logger = logging.getLogger(__name__)

STALE_LEAD_DAYS = 7


def is_stale(lead: Lead, *, days: int = STALE_LEAD_DAYS) -> bool:
    return datetime.now(UTC) - lead.updated_at > timedelta(days=days)


async def reset_stale_lead(lead: Lead, *, source: str, channel_type: str) -> Lead:
    """Close a stale lead and start a fresh one for the same chat."""
    if lead.state == LeadState.BLOCKED or not is_stale(lead):
        return lead

    logger.info(
        "Resetting stale lead %s (chat %s, last update %s)",
        lead.id, lead.channel_user_id, lead.updated_at.isoformat(),
    )
    lead.state = LeadState.CLOSED
    await update_lead(lead)
    return await create_lead(lead.channel_user_id, source=source, channel_type=channel_type)


async def resolve_lead(
    chat_id: int,
    *,
    source: str,
    channel_type: str,
    blocked_reply: str,
) -> tuple[Lead | None, str | None]:
    """Lookup or create a lead for a chat.

    Returns (lead, blocked_msg): if the chat is blocked returns (None, blocked_msg);
    otherwise (lead, None) where lead is either the found lead (CLOSED leads are
    reset and recreated) or a freshly created one.
    """
    lead = await get_lead_by_chat_id(chat_id)
    if lead and lead.state == LeadState.BLOCKED:
        return None, blocked_reply
    if lead and lead.state == LeadState.CLOSED:
        lead = None
    if lead is None:
        lead = await create_lead(chat_id, source=source, channel_type=channel_type)
    return lead, None
